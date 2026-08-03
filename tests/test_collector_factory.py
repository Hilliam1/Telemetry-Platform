from unittest.mock import Mock, patch

import pytest

from app.collector_factory import create_collector
from app.sources import SourceKind


@patch("app.collector_factory.Collector")
@patch("app.collector_factory.HostMetricsSourceHandler")
@patch("app.collector_factory.WindowsEventSourceHandler")
@patch("app.collector_factory.TelemetryRepository")
@patch("app.collector_factory.create_connection")
@patch("app.collector_factory.HostMetricsCollector")
@patch("app.collector_factory.WindowsEventParser")
@patch("app.collector_factory.WindowsEventReader")
@patch("app.collector_factory.CollectorState")
@patch("app.collector_factory.load_collector_settings")
@patch("app.collector_factory.socket.gethostname")
def test_factory_constructs_collector(
    mock_hostname,
    mock_settings_loader,
    mock_state,
    mock_reader,
    mock_parser,
    mock_metrics,
    mock_connection,
    mock_repository,
    mock_windows_handler,
    mock_metrics_handler,
    mock_collector,
):
    mock_hostname.return_value = "HOST-01"

    settings = Mock()
    settings.state_file = "collector_state.json"
    settings.batch_size = 100
    mock_settings_loader.return_value = settings

    conn = Mock()
    mock_connection.return_value = conn

    collector_instance = Mock()
    mock_collector.return_value = collector_instance

    result = create_collector()

    assert result is collector_instance

    mock_state.assert_called_once_with("collector_state.json")
    mock_reader.assert_called_once_with(batch_size=100)
    mock_parser.assert_called_once_with(default_computer="HOST-01")
    mock_metrics.assert_called_once_with(hostname="HOST-01")
    mock_repository.assert_called_once_with(conn)

    collector_kwargs = mock_collector.call_args.kwargs
    handlers = collector_kwargs["source_handlers"]

    assert collector_kwargs["hostname"] == "HOST-01"
    assert collector_kwargs["settings"] is settings
    assert collector_kwargs["conn"] is conn
    assert collector_kwargs["repository"] is mock_repository.return_value
    assert handlers[SourceKind.WINDOWS_EVENT] is mock_windows_handler.return_value
    assert handlers[SourceKind.HOST_METRICS] is mock_metrics_handler.return_value


@patch(
    "app.collector_factory.TelemetryRepository",
    side_effect=RuntimeError("construction failed"),
)
@patch("app.collector_factory.create_connection")
@patch("app.collector_factory.HostMetricsCollector")
@patch("app.collector_factory.WindowsEventParser")
@patch("app.collector_factory.WindowsEventReader")
@patch("app.collector_factory.CollectorState")
@patch("app.collector_factory.load_collector_settings")
@patch("app.collector_factory.socket.gethostname")
def test_factory_closes_connection_after_failure(
    mock_hostname,
    mock_settings_loader,
    mock_state,
    mock_reader,
    mock_parser,
    mock_metrics,
    mock_connection,
    mock_repository,
):
    mock_hostname.return_value = "HOST-01"

    settings = Mock()
    settings.state_file = "collector_state.json"
    settings.batch_size = 100
    mock_settings_loader.return_value = settings

    conn = Mock()
    mock_connection.return_value = conn

    with pytest.raises(RuntimeError, match="construction failed"):
        create_collector()

    conn.close.assert_called_once_with()
