"""Execution strategies for registered telemetry sources."""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any

import pywintypes
from psycopg2.extensions import connection

from app.detection.engine import DetectionEngine
from app.detection.repository import DetectionRepository
from app.health_metrics import HostMetricsCollector
from app.parsers.windows_event_parser import WindowsEventParser
from app.repository import TelemetryRepository
from app.sources import SourceKind, TelemetrySource
from app.state import CollectorState
from app.windows_reader import WindowsEventReader

LOG = logging.getLogger("telemetry_platform.source_handlers")


class SourceHandler(ABC):
    """Base interface implemented by every telemetry source handler."""

    @property
    @abstractmethod
    def kind(self) -> SourceKind:
        """Return the source category handled by this object."""

    @abstractmethod
    def ingest(self, source: TelemetrySource) -> int:
        """Collect and persist data for one telemetry source."""


class WindowsEventSourceHandler(SourceHandler):
    """Collect Windows Event Log channels and persist normalized events."""

    def __init__(
        self,
        *,
        conn: connection,
        repository: TelemetryRepository,
        detection_engine: DetectionEngine,
        detection_repository: DetectionRepository,
        reader: WindowsEventReader,
        parser: WindowsEventParser,
        state: CollectorState,
        hostname: str,
    ) -> None:
        self.conn = conn
        self.repository = repository
        self.detection_engine = detection_engine
        self.detection_repository = detection_repository
        self.reader = reader
        self.parser = parser
        self.state = state
        self.hostname = hostname

    @property
    def kind(self) -> SourceKind:
        return SourceKind.WINDOWS_EVENT

    def ingest(self, source: TelemetrySource) -> int:
        inserted = 0

        for channel in source.channels:
            try:
                inserted += self._ingest_channel(
                    source_type=source.name,
                    channel=channel,
                )
            except pywintypes.error as exc:
                self.conn.rollback()

                if exc.winerror == 5:
                    LOG.warning(
                        "Access denied reading %s. Run elevated, add the collector account "
                        "to Event Log Readers, or remove %s from COLLECTOR_SOURCES.",
                        channel,
                        source.name,
                    )
                    continue

                LOG.exception("Failed to ingest channel %s", channel)
            except Exception:
                self.conn.rollback()
                LOG.exception("Failed to ingest channel %s", channel)

        return inserted

    def _ingest_channel(
        self,
        *,
        source_type: str,
        channel: str,
    ) -> int:
        last_record_id = self.state.get_last_record_id(
            source_type,
            channel,
        )

        event_xml_documents = self.reader.read_channel(
            channel=channel,
            last_record_id=last_record_id,
        )

        parsed_events = [
            self.parser.parse(event_xml) for event_xml in event_xml_documents
        ]

        parsed_events.sort(key=lambda item: item["record_id"])

        inserted = 0
        highest_record_id: int | None = None

        for event in parsed_events:
            event["source_type"] = source_type

            self.repository.insert_log_event(
                source_host=event["computer"] or self.hostname,
                source_type=source_type,
                provider_name=event["provider"],
                event_id=event["event_id"],
                event_record_id=event["record_id"],
                severity=event["severity"],
                time_created=event["time_created"],
                message=event["message"],
                raw_data=json.dumps(
                    event["raw"],
                    sort_keys=True,
                ),
            )

            self.repository.insert_process_event(event)

            findings = self.detection_engine.evaluate(event)
            self.detection_repository.insert_findings(findings)

            inserted += 1
            highest_record_id = event["record_id"]

        self.conn.commit()

        if highest_record_id is not None:
            self.state.update_record_id(
                source_type,
                channel,
                highest_record_id,
            )
            self.state.save()

        return inserted


class HostMetricsSourceHandler(SourceHandler):
    """Collect and persist local host-performance metrics."""

    def __init__(
        self,
        *,
        conn: connection,
        repository: TelemetryRepository,
        metrics_collector: HostMetricsCollector,
    ) -> None:
        self.conn = conn
        self.repository = repository
        self.metrics_collector = metrics_collector

    @property
    def kind(self) -> SourceKind:
        return SourceKind.HOST_METRICS

    def ingest(self, source: TelemetrySource) -> int:
        del source

        metrics: dict[str, Any] = self.metrics_collector.collect()

        if not metrics.get("psutil_available"):
            return 0

        self.repository.insert_host_metrics(metrics)
        self.conn.commit()

        return 1
