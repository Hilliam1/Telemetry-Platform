from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.ingest import Collector
from app.sources import SourceKind, TelemetrySource


def make_collector_without_init():
    collector = Collector.__new__(Collector)
    collector.source_handlers = {
        SourceKind.WINDOWS_EVENT: Mock(),
        SourceKind.HOST_METRICS: Mock(),
    }
    collector.source_handlers[SourceKind.WINDOWS_EVENT].ingest.return_value = 5
    collector.source_handlers[SourceKind.HOST_METRICS].ingest.return_value = 1
    return collector


def test_dispatches_windows_source():
    collector = make_collector_without_init()

    source = TelemetrySource(
        name="sysmon",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Sysmon",),
    )

    result = collector._ingest_source(source)

    assert result == 5
    collector.source_handlers[
        SourceKind.WINDOWS_EVENT
    ].ingest.assert_called_once_with(source)


def test_dispatches_health_metrics_source():
    collector = make_collector_without_init()

    source = TelemetrySource(
        name="health_metrics",
        kind=SourceKind.HOST_METRICS,
    )

    result = collector._ingest_source(source)

    assert result == 1
    collector.source_handlers[
        SourceKind.HOST_METRICS
    ].ingest.assert_called_once_with(source)


def test_rejects_unregistered_handler_kind():
    collector = Collector.__new__(Collector)
    collector.source_handlers = {}

    source = TelemetrySource(
        name="sysmon",
        kind=SourceKind.WINDOWS_EVENT,
    )

    with pytest.raises(
        ValueError,
        match="No handler registered",
    ):
        collector._ingest_source(source)


def test_enabled_sources_resolves_configured_names():
    collector = Collector.__new__(Collector)
    collector.settings = SimpleNamespace(
        enabled_sources=(
            "sysmon",
            "health_metrics",
        )
    )

    sources = collector._enabled_sources()

    assert tuple(source.name for source in sources) == (
        "sysmon",
        "health_metrics",
    )


def test_enabled_sources_rejects_unknown_name():
    collector = Collector.__new__(Collector)
    collector.settings = SimpleNamespace(enabled_sources=("not_a_real_source",))

    with pytest.raises(
        ValueError,
        match="Unknown telemetry source",
    ):
        collector._enabled_sources()
