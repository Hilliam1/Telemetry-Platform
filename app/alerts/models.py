"""Typed models for deterministic alert generation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from app.risk.models import RiskAssessment, RiskLevel


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {key: _freeze(item) for key, item in value.items()}
        )

    if isinstance(value, tuple):
        return tuple(_freeze(item) for item in value)

    if isinstance(value, list):
        return tuple(_freeze(item) for item in value)

    return value


class AlertStatus(str, Enum):
    """Supported alert lifecycle states."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass(frozen=True)
class Alert:
    """Operator-facing alert generated from a risk assessment."""

    alert_id: str
    assessment_id: str
    correlation_id: str
    correlation_rule_id: str
    title: str
    risk_score: int
    risk_level: RiskLevel
    status: AlertStatus
    source_host: str
    first_event_time: datetime
    last_event_time: datetime
    created_at: datetime
    summary: str
    evidence: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        *,
        assessment: RiskAssessment,
        title: str,
        summary: str,
        created_at: datetime,
    ) -> Alert:
        return cls(
            alert_id=str(uuid4()),
            assessment_id=assessment.assessment_id,
            correlation_id=assessment.correlation_id,
            correlation_rule_id=assessment.correlation_rule_id,
            title=title,
            risk_score=assessment.score,
            risk_level=assessment.level,
            status=AlertStatus.NEW,
            source_host=assessment.source_host,
            first_event_time=assessment.first_event_time,
            last_event_time=assessment.last_event_time,
            created_at=created_at,
            summary=summary,
            evidence=_freeze(
                {
                    "base_score": assessment.base_score,
                    "contribution_count": len(
                        assessment.contributions
                    ),
                    "risk_evidence": dict(assessment.evidence),
                }
            ),
        )
