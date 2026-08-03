"""Telemetry collector orchestration service."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

from psycopg2.extensions import connection

from app.config import DEFAULT_SOURCES, CollectorSettings
from app.repository import TelemetryRepository
from app.source_handlers import SourceHandler
from app.sources import (
    SourceKind,
    TelemetrySource,
    get_sources,
)

LOG = logging.getLogger("telemetry_platform.collector")


class Collector:
    """Coordinate configured telemetry sources and polling runs."""

    def __init__(
        self,
        *,
        hostname: str,
        settings: CollectorSettings,
        conn: connection,
        repository: TelemetryRepository,
        source_handlers: dict[SourceKind, SourceHandler],
    ) -> None:
        self.hostname = hostname
        self.settings = settings
        self.conn = conn
        self.repository = repository
        self.source_handlers = source_handlers

    def _enabled_sources(
        self,
    ) -> tuple[TelemetrySource, ...]:
        source_names = (
            DEFAULT_SOURCES
            if self.settings.enabled_sources is None
            else self.settings.enabled_sources
        )

        return get_sources(source_names)

    def _ingest_source(
        self,
        source: TelemetrySource,
    ) -> int:
        try:
            handler = self.source_handlers[source.kind]
        except KeyError as exc:
            raise ValueError(
                f"No handler registered for source kind {source.kind!r}"
            ) from exc

        return handler.ingest(source)

    def close(self) -> None:
        """Close the shared PostgreSQL connection."""

        self.conn.close()

    def run_forever(self) -> None:
        """Execute polling runs until the process is interrupted."""

        while True:
            total = self.run_once()
            LOG.info(
                "Polling complete. Inserted %s events. Sleeping %s seconds.",
                total,
                self.settings.poll_seconds,
            )
            time.sleep(self.settings.poll_seconds)

    def run_once(self) -> int:
        """Execute one complete polling cycle."""

        started_at = datetime.now(timezone.utc)
        total = 0
        status = "success"
        error_message = None

        try:
            for source in self._enabled_sources():
                total += self._ingest_source(source)

        except Exception as exc:
            self.conn.rollback()
            status = "failed"
            error_message = str(exc)
            LOG.exception("Collector run failed.")

        self.repository.insert_collector_run(
            source_host=self.hostname,
            status=status,
            events_inserted=total,
            started_at=started_at,
            error_message=error_message,
        )

        self.conn.commit()
        return total
