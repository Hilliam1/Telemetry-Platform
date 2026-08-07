"""PostgreSQL persistence for operator-facing alerts."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from psycopg2.extensions import connection

from app.alerts.models import Alert


def _jsonable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _jsonable(item)
            for key, item in value.items()
        }

    if isinstance(value, tuple | list):
        return [
            _jsonable(item)
            for item in value
        ]

    return value


class AlertRepository:
    """Persist alerts using an existing transaction."""

    def __init__(
        self,
        conn: connection,
    ) -> None:
        self.conn = conn

    def insert_alert(
        self,
        alert: Alert,
    ) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO alerts (
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
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s::jsonb
                )
                """,
                (
                    alert.alert_id,
                    alert.assessment_id,
                    alert.correlation_id,
                    alert.correlation_rule_id,
                    alert.title,
                    alert.risk_score,
                    alert.risk_level.value,
                    alert.status.value,
                    alert.source_host,
                    alert.first_event_time,
                    alert.last_event_time,
                    alert.created_at,
                    alert.summary,
                    json.dumps(
                        _jsonable(alert.evidence),
                        sort_keys=True,
                        default=str,
                    ),
                ),
            )
