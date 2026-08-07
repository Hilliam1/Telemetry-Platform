"""PostgreSQL persistence for deterministic correlation matches."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from psycopg2.extensions import connection

from app.correlation.models import CorrelationMatch


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


class CorrelationRepository:
    """Persist correlation matches using an existing transaction."""

    def __init__(
        self,
        conn: connection,
    ) -> None:
        self.conn = conn

    def insert_match(
        self,
        match: CorrelationMatch,
    ) -> None:
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO correlation_matches (
                    correlation_uuid,
                    rule_id,
                    rule_version,
                    title,
                    severity,
                    source_host,
                    first_event_time,
                    last_event_time,
                    matched_finding_ids,
                    matched_detection_rule_ids,
                    explanation,
                    investigation_steps,
                    evidence,
                    tags
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s, %s, %s::uuid[], %s::text[],
                    %s, %s::jsonb, %s::jsonb, %s::text[]
                )
                """,
                (
                    match.correlation_id,
                    match.rule_id,
                    match.rule_version,
                    match.title,
                    match.severity.value,
                    match.source_host,
                    match.first_event_time,
                    match.last_event_time,
                    list(match.matched_finding_ids),
                    list(match.matched_detection_rule_ids),
                    match.explanation,
                    json.dumps(
                        list(match.investigation_steps)
                    ),
                    json.dumps(
                        _jsonable(match.evidence),
                        sort_keys=True,
                        default=str,
                    ),
                    list(match.tags),
                ),
            )
