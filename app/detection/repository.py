"""PostgreSQL persistence for deterministic detection findings."""

from __future__ import annotations

import json
from collections.abc import Iterable
from datetime import datetime
from types import MappingProxyType
from typing import Any

from psycopg2.extensions import connection

from app.detection.models import (
    DetectionFinding,
    DetectionSeverity,
)


class DetectionRepository:
    """Persist detection findings using an existing transaction."""

    def __init__(self, conn: connection) -> None:
        self.conn = conn

    def insert_finding(
        self,
        finding: DetectionFinding,
    ) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO detection_findings (
                    finding_uuid,
                    rule_id,
                    rule_version,
                    title,
                    severity,
                    source_host,
                    source_type,
                    event_id,
                    event_record_id,
                    event_time,
                    evaluated_at,
                    explanation,
                    investigation_steps,
                    evidence,
                    tags
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s::jsonb, %s::jsonb, %s
                )
                """,
                (
                    finding.finding_id,
                    finding.rule_id,
                    finding.rule_version,
                    finding.title,
                    finding.severity.value,
                    finding.source_host,
                    finding.source_type,
                    finding.event_id,
                    finding.event_record_id,
                    finding.event_time,
                    finding.evaluated_at,
                    finding.explanation,
                    json.dumps(
                        list(finding.investigation_steps)
                    ),
                    json.dumps(
                        dict(finding.evidence),
                        sort_keys=True,
                        default=str,
                    ),
                    list(finding.tags),
                ),
            )

    def insert_findings(
        self,
        findings: Iterable[DetectionFinding],
    ) -> int:
        inserted = 0

        for finding in findings:
            self.insert_finding(finding)
            inserted += 1

        return inserted

    def find_recent_findings(
        self,
        *,
        source_host: str,
        rule_ids: tuple[str, ...],
        start_time: datetime,
        end_time: datetime,
    ) -> tuple[DetectionFinding, ...]:
        if not rule_ids:
            return ()

        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    finding_uuid,
                    rule_id,
                    rule_version,
                    title,
                    severity,
                    source_host,
                    source_type,
                    event_id,
                    event_record_id,
                    event_time,
                    evaluated_at,
                    explanation,
                    investigation_steps,
                    evidence,
                    tags
                FROM detection_findings
                WHERE source_host = %s
                  AND rule_id = ANY(%s)
                  AND event_time >= %s
                  AND event_time <= %s
                ORDER BY event_time, finding_uuid
                """,
                (
                    source_host,
                    list(rule_ids),
                    start_time,
                    end_time,
                ),
            )

            rows = cur.fetchall()

        return tuple(
            self._finding_from_row(row)
            for row in rows
        )

    @staticmethod
    def _finding_from_row(
        row: tuple[Any, ...],
    ) -> DetectionFinding:
        (
            finding_uuid,
            rule_id,
            rule_version,
            title,
            severity,
            source_host,
            source_type,
            event_id,
            event_record_id,
            event_time,
            evaluated_at,
            explanation,
            investigation_steps,
            evidence,
            tags,
        ) = row

        if isinstance(investigation_steps, str):
            investigation_steps = json.loads(
                investigation_steps
            )

        if isinstance(evidence, str):
            evidence = json.loads(evidence)

        return DetectionFinding(
            finding_id=str(finding_uuid),
            rule_id=rule_id,
            rule_version=rule_version,
            title=title,
            severity=DetectionSeverity(severity),
            source_host=source_host,
            source_type=source_type,
            event_id=event_id,
            event_record_id=event_record_id,
            event_time=event_time,
            evaluated_at=evaluated_at,
            explanation=explanation,
            investigation_steps=tuple(
                investigation_steps or ()
            ),
            evidence=MappingProxyType(
                dict(evidence or {})
            ),
            tags=tuple(tags or ()),
        )
