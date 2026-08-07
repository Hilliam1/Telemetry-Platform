from unittest.mock import Mock, patch

import pytest

from app.alerts.engine import AlertEngine
from app.alerts.repository import AlertRepository
from app.collector_factory import create_collector
from app.correlation.engine import CorrelationEngine
from app.correlation.repository import CorrelationRepository
from app.detection.engine import DetectionEngine
from app.detection.repository import DetectionRepository
from app.intelligence.service import IntelligenceService
from app.risk.engine import RiskEngine
from app.risk.repository import RiskRepository
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
    windows_handler_kwargs = mock_windows_handler.call_args.kwargs
    metrics_handler_kwargs = mock_metrics_handler.call_args.kwargs

    assert collector_kwargs["hostname"] == "HOST-01"
    assert collector_kwargs["settings"] is settings
    assert collector_kwargs["conn"] is conn
    assert collector_kwargs["repository"] is mock_repository.return_value
    assert handlers[SourceKind.WINDOWS_EVENT] is mock_windows_handler.return_value
    assert handlers[SourceKind.HOST_METRICS] is mock_metrics_handler.return_value
    assert isinstance(
        windows_handler_kwargs["detection_engine"],
        DetectionEngine,
    )
    assert isinstance(
        windows_handler_kwargs["detection_repository"],
        DetectionRepository,
    )
    assert isinstance(
        windows_handler_kwargs["intelligence_service"],
        IntelligenceService,
    )
    assert isinstance(
        windows_handler_kwargs[
            "intelligence_service"
        ].correlation_repository,
        CorrelationRepository,
    )
    assert isinstance(
        windows_handler_kwargs[
            "intelligence_service"
        ].correlation_engine,
        CorrelationEngine,
    )
    assert isinstance(
        windows_handler_kwargs[
            "intelligence_service"
        ].risk_repository,
        RiskRepository,
    )
    assert isinstance(
        windows_handler_kwargs[
            "intelligence_service"
        ].risk_engine,
        RiskEngine,
    )
    assert isinstance(
        windows_handler_kwargs[
            "intelligence_service"
        ].alert_repository,
        AlertRepository,
    )
    assert isinstance(
        windows_handler_kwargs[
            "intelligence_service"
        ].alert_engine,
        AlertEngine,
    )
    assert "correlation_engine" not in windows_handler_kwargs
    assert "risk_engine" not in windows_handler_kwargs
    assert "alert_engine" not in windows_handler_kwargs
    assert "detection_engine" not in metrics_handler_kwargs
    assert "detection_repository" not in metrics_handler_kwargs


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
