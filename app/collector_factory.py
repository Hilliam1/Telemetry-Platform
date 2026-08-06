"""Construct the telemetry collector and its dependencies."""

from __future__ import annotations

import socket

from app.collector import Collector
from app.config import load_collector_settings
from app.database import create_connection
from app.detection.engine import DetectionEngine
from app.detection.repository import DetectionRepository
from app.detection.rules import BUILTIN_RULES
from app.health_metrics import HostMetricsCollector
from app.parsers.windows_event_parser import WindowsEventParser
from app.repository import TelemetryRepository
from app.source_handlers import (
    HostMetricsSourceHandler,
    SourceHandler,
    WindowsEventSourceHandler,
)
from app.sources import SourceKind
from app.state import CollectorState
from app.windows_reader import WindowsEventReader


def create_collector() -> Collector:
    """Build a fully configured telemetry collector."""

    hostname = socket.gethostname()
    settings = load_collector_settings()

    state = CollectorState(settings.state_file)
    reader = WindowsEventReader(batch_size=settings.batch_size)
    parser = WindowsEventParser(default_computer=hostname)
    metrics_collector = HostMetricsCollector(hostname=hostname)

    conn = create_connection()

    try:
        repository = TelemetryRepository(conn)
        detection_repository = DetectionRepository(conn)
        detection_engine = DetectionEngine(BUILTIN_RULES)
        source_handlers: dict[SourceKind, SourceHandler] = {
            SourceKind.WINDOWS_EVENT: WindowsEventSourceHandler(
                conn=conn,
                repository=repository,
                detection_engine=detection_engine,
                detection_repository=detection_repository,
                reader=reader,
                parser=parser,
                state=state,
                hostname=hostname,
            ),
            SourceKind.HOST_METRICS: HostMetricsSourceHandler(
                conn=conn,
                repository=repository,
                metrics_collector=metrics_collector,
            ),
        }

        return Collector(
            hostname=hostname,
            settings=settings,
            conn=conn,
            repository=repository,
            source_handlers=source_handlers,
        )
    except Exception:
        conn.close()
        raise
