"""Construct the telemetry collector and its dependencies."""

from __future__ import annotations

import socket

from app.alerts.engine import AlertEngine
from app.alerts.policy import AlertPolicy
from app.alerts.repository import AlertRepository
from app.collector import Collector
from app.config import load_collector_settings
from app.correlation.engine import CorrelationEngine
from app.correlation.repository import CorrelationRepository
from app.correlation.rules import BUILTIN_CORRELATION_RULES
from app.database import create_connection
from app.detection.engine import DetectionEngine
from app.detection.repository import DetectionRepository
from app.detection.rules import BUILTIN_RULES
from app.health_metrics import HostMetricsCollector
from app.intelligence.service import IntelligenceService
from app.parsers.windows_event_parser import WindowsEventParser
from app.repository import TelemetryRepository
from app.risk.engine import RiskEngine
from app.risk.policy import RiskPolicy
from app.risk.providers import RepeatedActivityRiskProvider
from app.risk.repository import RiskRepository
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
        correlation_repository = CorrelationRepository(conn)
        correlation_engine = CorrelationEngine(
            BUILTIN_CORRELATION_RULES
        )
        risk_repository = RiskRepository(conn)
        risk_engine = RiskEngine(
            policy=RiskPolicy(),
            providers=(
                RepeatedActivityRiskProvider(),
            ),
        )
        alert_repository = AlertRepository(conn)
        alert_engine = AlertEngine(
            policy=AlertPolicy(),
        )
        intelligence_service = IntelligenceService(
            detection_repository=detection_repository,
            correlation_engine=correlation_engine,
            correlation_repository=correlation_repository,
            risk_engine=risk_engine,
            risk_repository=risk_repository,
            alert_engine=alert_engine,
            alert_repository=alert_repository,
        )
        source_handlers: dict[SourceKind, SourceHandler] = {
            SourceKind.WINDOWS_EVENT: WindowsEventSourceHandler(
                conn=conn,
                repository=repository,
                detection_engine=detection_engine,
                detection_repository=detection_repository,
                intelligence_service=intelligence_service,
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
