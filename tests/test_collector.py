from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.collector import Collector
from app.sources import (
    SourceKind,
    TelemetrySource,
)


def make_collector(
    *,
    enabled_sources=None,
):
    conn = Mock()
    repository = Mock()
    settings = SimpleNamespace(
        enabled_sources=enabled_sources,
        poll_seconds=5,
    )
    handler = Mock()
    handler.ingest.return_value = 3

    collector = Collector(
        hostname="HOST-01",
        settings=settings,
        conn=conn,
        repository=repository,
        source_handlers={
            SourceKind.WINDOWS_EVENT: handler,
        },
    )

    return collector, conn, repository, handler


def test_dispatches_source_to_registered_handler():
    collector, _, _, handler = make_collector()

    source = TelemetrySource(
        name="sysmon",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Sysmon",),
    )

    result = collector._ingest_source(source)

    assert result == 3
    handler.ingest.assert_called_once_with(source)


def test_missing_handler_raises_clear_error():
    collector, _, _, _ = make_collector()
    collector.source_handlers = {}

    source = TelemetrySource(
        name="health_metrics",
        kind=SourceKind.HOST_METRICS,
    )

    with pytest.raises(
        ValueError,
        match="No handler registered",
    ):
        collector._ingest_source(source)


def test_run_once_records_successful_run():
    collector, conn, repository, handler = make_collector(
        enabled_sources=("windows_system",)
    )

    handler.ingest.return_value = 4

    result = collector.run_once()

    assert result == 4

    repository.insert_collector_run.assert_called_once()
    call = repository.insert_collector_run.call_args.kwargs

    assert call["source_host"] == "HOST-01"
    assert call["status"] == "success"
    assert call["events_inserted"] == 4
    assert call["error_message"] is None
    conn.rollback.assert_not_called()
    conn.commit.assert_called_once_with()


def test_run_once_records_failed_run():
    collector, conn, repository, handler = make_collector(
        enabled_sources=("windows_system",)
    )

    handler.ingest.side_effect = RuntimeError("source failed")

    result = collector.run_once()

    assert result == 0
    conn.rollback.assert_called_once_with()

    call = repository.insert_collector_run.call_args.kwargs

    assert call["status"] == "failed"
    assert call["events_inserted"] == 0
    assert call["error_message"] == "source failed"
    conn.commit.assert_called_once_with()


def test_close_closes_connection():
    collector, conn, _, _ = make_collector()

    collector.close()

    conn.close.assert_called_once_with()
