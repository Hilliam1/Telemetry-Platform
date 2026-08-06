"""PostgreSQL persistence for deterministic detection findings."""

from __future__ import annotations

import json
from collections.abc import Iterable

from psycopg2.extensions import connection

from app.detection.models import DetectionFinding


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