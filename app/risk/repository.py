"""PostgreSQL persistence for deterministic risk assessments."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from psycopg2.extensions import connection

from app.risk.models import RiskAssessment


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


class RiskRepository:
    """Persist risk assessments using an existing transaction."""

    def __init__(
        self,
        conn: connection,
    ) -> None:
        self.conn = conn

    def insert_assessment(
        self,
        assessment: RiskAssessment,
    ) -> None:
        contributions = [
            {
                "provider": contribution.provider,
                "reason": contribution.reason,
                "score_delta": contribution.score_delta,
                "evidence": _jsonable(contribution.evidence),
            }
            for contribution in assessment.contributions
        ]

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO risk_assessments (
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
                )
                VALUES (
                    %s, %s, %s, %s, %s,
                    %s, %s::jsonb, %s, %s, %s,
                    %s, %s, %s::jsonb
                )
                """,
                (
                    assessment.assessment_id,
                    assessment.correlation_id,
                    assessment.correlation_rule_id,
                    assessment.score,
                    assessment.level.value,
                    assessment.base_score,
                    json.dumps(
                        contributions,
                        sort_keys=True,
                        default=str,
                    ),
                    assessment.source_host,
                    assessment.first_event_time,
                    assessment.last_event_time,
                    assessment.assessed_at,
                    assessment.explanation,
                    json.dumps(
                        _jsonable(assessment.evidence),
                        sort_keys=True,
                        default=str,
                    ),
                ),
            )
