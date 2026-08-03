"""Telemetry source definitions and registry."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class SourceKind(str, Enum):
    """Supported telemetry source categories."""

    WINDOWS_EVENT = "windows_event"
    HOST_METRICS = "host_metrics"


@dataclass(frozen=True)
class TelemetrySource:
    """Describe one configured telemetry source."""

    name: str
    kind: SourceKind
    channels: tuple[str, ...] = ()


SOURCE_REGISTRY: dict[str, TelemetrySource] = {
    "windows_system": TelemetrySource(
        name="windows_system",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("System",),
    ),
    "windows_application": TelemetrySource(
        name="windows_application",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Application",),
    ),
    "windows_security": TelemetrySource(
        name="windows_security",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Security",),
    ),
    "sysmon": TelemetrySource(
        name="sysmon",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Microsoft-Windows-Sysmon/Operational",),
    ),
    "powershell": TelemetrySource(
        name="powershell",
        kind=SourceKind.WINDOWS_EVENT,
        channels=(
            "Windows PowerShell",
            "Microsoft-Windows-PowerShell/Operational",
        ),
    ),
    "defender": TelemetrySource(
        name="defender",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Microsoft-Windows-Windows Defender/Operational",),
    ),
    "task_scheduler": TelemetrySource(
        name="task_scheduler",
        kind=SourceKind.WINDOWS_EVENT,
        channels=("Microsoft-Windows-TaskScheduler/Operational",),
    ),
    "health_metrics": TelemetrySource(
        name="health_metrics",
        kind=SourceKind.HOST_METRICS,
    ),
}


def get_source(name: str) -> TelemetrySource:
    """Return a source definition or raise a clear configuration error."""

    try:
        return SOURCE_REGISTRY[name]
    except KeyError as exc:
        supported = ", ".join(sorted(SOURCE_REGISTRY))

        raise ValueError(
            f"Unknown telemetry source {name!r}. Supported sources: {supported}"
        ) from exc


def get_sources(names: tuple[str, ...]) -> tuple[TelemetrySource, ...]:
    """Resolve multiple configured source names."""

    return tuple(get_source(name) for name in names)
