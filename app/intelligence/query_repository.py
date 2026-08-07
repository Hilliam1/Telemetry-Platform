"""Read-only PostgreSQL queries for intelligence data."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from psycopg2.extensions import connection


class IntelligenceQueryRepository:
    """Query persisted intelligence without modifying state."""

    def __init__(
        self,
        conn: connection,
    ) -> None:
        self.conn = conn

    def list_detections(
        self,
        *,
        source_host: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        parameters: list[object] = []

        if source_host is not None:
            conditions.append("source_host = %s")
            parameters.append(source_host)

        if severity is not None:
            conditions.append("severity = %s")
            parameters.append(severity)

        where_clause = self._where_clause(conditions)
        parameters.append(limit)

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
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
                {where_clause}
                ORDER BY evaluated_at DESC
                LIMIT %s
                """,
                tuple(parameters),
            )
            rows = cur.fetchall()

        return [
            {
                "finding_uuid": row[0],
                "rule_id": row[1],
                "rule_version": row[2],
                "title": row[3],
                "severity": row[4],
                "source_host": row[5],
                "source_type": row[6],
                "event_id": row[7],
                "event_record_id": row[8],
                "event_time": row[9],
                "evaluated_at": row[10],
                "explanation": row[11],
                "investigation_steps": row[12],
                "evidence": row[13],
                "tags": row[14],
            }
            for row in rows
        ]

    def list_correlations(
        self,
        *,
        source_host: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        parameters: list[object] = []

        if source_host is not None:
            conditions.append("source_host = %s")
            parameters.append(source_host)

        if severity is not None:
            conditions.append("severity = %s")
            parameters.append(severity)

        where_clause = self._where_clause(conditions)
        parameters.append(limit)

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    correlation_uuid,
                    rule_id,
                    rule_version,
                    title,
                    severity,
                    source_host,
                    first_event_time,
                    last_event_time,
                    matched_finding_ids::text[],
                    matched_detection_rule_ids,
                    explanation,
                    investigation_steps,
                    evidence,
                    tags
                FROM correlation_matches
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                tuple(parameters),
            )
            rows = cur.fetchall()

        return [
            {
                "correlation_uuid": row[0],
                "rule_id": row[1],
                "rule_version": row[2],
                "title": row[3],
                "severity": row[4],
                "source_host": row[5],
                "first_event_time": row[6],
                "last_event_time": row[7],
                "matched_finding_ids": row[8],
                "matched_detection_rule_ids": row[9],
                "explanation": row[10],
                "investigation_steps": row[11],
                "evidence": row[12],
                "tags": row[13],
            }
            for row in rows
        ]

    def list_risk_assessments(
        self,
        *,
        source_host: str | None = None,
        level: str | None = None,
        minimum_score: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        parameters: list[object] = []

        if source_host is not None:
            conditions.append("source_host = %s")
            parameters.append(source_host)

        if level is not None:
            conditions.append("level = %s")
            parameters.append(level)

        if minimum_score is not None:
            conditions.append("score >= %s")
            parameters.append(minimum_score)

        where_clause = self._where_clause(conditions)
        parameters.append(limit)

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    assessment_uuid,
                    correlation_uuid,
                    correlation_rule_id,
                    score,
                    level,
                    base_score,
                    contributions,
                    source_host,
                    first_event_time,
                    last_event_time,
                    assessed_at,
                    explanation,
                    evidence
                FROM risk_assessments
                {where_clause}
                ORDER BY assessed_at DESC
                LIMIT %s
                """,
                tuple(parameters),
            )
            rows = cur.fetchall()

        return [
            {
                "assessment_uuid": row[0],
                "correlation_uuid": row[1],
                "correlation_rule_id": row[2],
                "score": row[3],
                "level": row[4],
                "base_score": row[5],
                "contributions": row[6],
                "source_host": row[7],
                "first_event_time": row[8],
                "last_event_time": row[9],
                "assessed_at": row[10],
                "explanation": row[11],
                "evidence": row[12],
            }
            for row in rows
        ]

    def list_alerts(
        self,
        *,
        source_host: str | None = None,
        status: str | None = None,
        risk_level: str | None = None,
        minimum_score: int | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        conditions: list[str] = []
        parameters: list[object] = []

        if source_host is not None:
            conditions.append("source_host = %s")
            parameters.append(source_host)

        if status is not None:
            conditions.append("status = %s")
            parameters.append(status)

        if risk_level is not None:
            conditions.append("risk_level = %s")
            parameters.append(risk_level)

        if minimum_score is not None:
            conditions.append("risk_score >= %s")
            parameters.append(minimum_score)

        where_clause = self._where_clause(conditions)
        parameters.append(limit)

        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                SELECT
                    alert_uuid,
                    assessment_uuid,
                    correlation_uuid,
                    correlation_rule_id,
                    title,
                    risk_score,
                    risk_level,
                    status,
                    source_host,
                    first_event_time,
                    last_event_time,
                    created_at,
                    summary,
                    evidence
                FROM alerts
                {where_clause}
                ORDER BY created_at DESC
                LIMIT %s
                """,
                tuple(parameters),
            )
            rows = cur.fetchall()

        return [self._alert_from_row(row) for row in rows]

    def get_alert(
        self,
        alert_uuid: UUID,
    ) -> dict[str, Any] | None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    alert_uuid,
                    assessment_uuid,
                    correlation_uuid,
                    correlation_rule_id,
                    title,
                    risk_score,
                    risk_level,
                    status,
                    source_host,
                    first_event_time,
                    last_event_time,
                    created_at,
                    summary,
                    evidence
                FROM alerts
                WHERE alert_uuid = %s
                LIMIT 1
                """,
                (alert_uuid,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return self._alert_from_row(row)

    @staticmethod
    def _where_clause(
        conditions: list[str],
    ) -> str:
        if not conditions:
            return ""

        return "WHERE " + " AND ".join(conditions)

    @staticmethod
    def _alert_from_row(
        row: tuple[Any, ...],
    ) -> dict[str, Any]:
        return {
            "alert_uuid": row[0],
            "assessment_uuid": row[1],
            "correlation_uuid": row[2],
            "correlation_rule_id": row[3],
            "title": row[4],
            "risk_score": row[5],
            "risk_level": row[6],
            "status": row[7],
            "source_host": row[8],
            "first_event_time": row[9],
            "last_event_time": row[10],
            "created_at": row[11],
            "summary": row[12],
            "evidence": row[13],
        }
