"""PostgreSQL persistence operations for telemetry data."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from psycopg2.extensions import connection


class TelemetryRepository:
    """Persist normalized telemetry using an existing transaction."""

    def __init__(self, conn: connection) -> None:
        self.conn = conn

    def insert_log_event(
        self,
        *,
        source_host: str,
        source_type: str,
        provider_name: str,
        event_id: int,
        event_record_id: int,
        severity: str,
        time_created: datetime,
        message: str,
        raw_data: str,
    ) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO log_events (
                    source_host,
                    source_type,
                    provider_name,
                    event_id,
                    event_record_id,
                    severity,
                    time_created,
                    message,
                    raw_data
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    source_host,
                    source_type,
                    provider_name,
                    event_id,
                    event_record_id,
                    severity,
                    time_created,
                    message,
                    raw_data,
                ),
            )

    def insert_process_event(
        self,
        event: dict[str, Any],
    ) -> bool:
        if event.get("source_type") != "sysmon":
            return False

        if event.get("event_id") != 1:
            return False

        raw = event.get("raw", {})
        data = raw.get("event_data", {})

        sha256 = self._extract_sha256(
            data.get("Hashes", "")
        )

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO process_events (
                    source_host,
                    process_guid,
                    process_id,
                    image,
                    command_line,
                    parent_image,
                    parent_command_line,
                    user_name,
                    sha256,
                    created_at
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    event.get("computer", ""),
                    data.get("ProcessGuid", ""),
                    int(data.get("ProcessId", 0) or 0),
                    data.get("Image", ""),
                    data.get("CommandLine", ""),
                    data.get("ParentImage", ""),
                    data.get("ParentCommandLine", ""),
                    data.get("User", ""),
                    sha256,
                    event["time_created"],
                ),
            )

        return True

    def insert_host_metrics(
        self,
        metrics: dict[str, Any],
    ) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO host_metrics (
                    host_name,
                    cpu_percent,
                    memory_percent,
                    disk_percent,
                    boot_time
                )
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    metrics["host"],
                    metrics["cpu_percent"],
                    metrics["memory_percent"],
                    metrics["disk_percent"],
                    metrics["boot_time"],
                ),
            )

    def insert_collector_run(
        self,
        *,
        source_host: str,
        status: str,
        events_inserted: int,
        started_at: datetime,
        error_message: str | None = None,
    ) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO collector_runs (
                    source_host,
                    status,
                    events_inserted,
                    started_at,
                    error_message
                )
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    source_host,
                    status,
                    events_inserted,
                    started_at,
                    error_message,
                ),
            )

    @staticmethod
    def _extract_sha256(hashes: str) -> str:
        for item in hashes.split(","):
            key, separator, value = item.strip().partition("=")

            if separator and key.upper() == "SHA256":
                return value

        return ""