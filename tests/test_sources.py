import pytest

from app.config import DEFAULT_SOURCES
from app.sources import (
    SOURCE_REGISTRY,
    SourceKind,
    get_source,
    get_sources,
)


def test_system_source_definition():
    source = get_source("windows_system")

    assert source.name == "windows_system"
    assert source.kind is SourceKind.WINDOWS_EVENT
    assert source.channels == ("System",)


def test_powershell_contains_both_channels():
    source = get_source("powershell")

    assert source.channels == (
        "Windows PowerShell",
        "Microsoft-Windows-PowerShell/Operational",
    )


def test_health_metrics_has_no_windows_channels():
    source = get_source("health_metrics")

    assert source.kind is SourceKind.HOST_METRICS
    assert source.channels == ()


def test_get_sources_preserves_requested_order():
    sources = get_sources(
        (
            "sysmon",
            "windows_system",
            "health_metrics",
        )
    )

    assert tuple(source.name for source in sources) == (
        "sysmon",
        "windows_system",
        "health_metrics",
    )


def test_unknown_source_raises_clear_error():
    with pytest.raises(
        ValueError,
        match="Unknown telemetry source",
    ):
        get_source("not_a_real_source")


def test_registry_contains_all_default_sources():
    assert set(SOURCE_REGISTRY) == set(DEFAULT_SOURCES)
