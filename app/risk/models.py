"""Typed models for deterministic risk assessment."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from app.correlation.models import CorrelationMatch


class RiskLevel(str, Enum):
    """Normalized platform risk levels."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class RiskContribution:
    """One explainable adjustment applied to a risk score."""

    provider: str
    reason: str
    score_delta: int
    evidence: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        *,
        provider: str,
        reason: str,
        score_delta: int,
        evidence: dict[str, Any] | None = None,
    ) -> RiskContribution:
        return cls(
            provider=provider,
            reason=reason,
            score_delta=score_delta,
            evidence=MappingProxyType(
                dict(evidence or {})
            ),
        )


@dataclass(frozen=True)
class RiskAssessment:
    """Deterministic risk result for one correlation match."""

    assessment_id: str
    correlation_id: str
    correlation_rule_id: str
    score: int
    level: RiskLevel
    base_score: int
    contributions: tuple[RiskContribution, ...]
    source_host: str
    first_event_time: datetime
    last_event_time: datetime
    assessed_at: datetime
    explanation: str
    evidence: Mapping[str, Any]

    @classmethod
    def create(
        cls,
        *,
        correlation: CorrelationMatch,
        score: int,
        level: RiskLevel,
        base_score: int,
        contributions: tuple[RiskContribution, ...],
        assessed_at: datetime,
    ) -> RiskAssessment:
        explanation = (
            f"Risk score {score} ({level.value}) derived from "
            f"base score {base_score} and "
            f"{len(contributions)} contribution(s)."
        )

        return cls(
            assessment_id=str(uuid4()),
            correlation_id=correlation.correlation_id,
            correlation_rule_id=correlation.rule_id,
            score=score,
            level=level,
            base_score=base_score,
            contributions=contributions,
            source_host=correlation.source_host,
            first_event_time=correlation.first_event_time,
            last_event_time=correlation.last_event_time,
            assessed_at=assessed_at,
            explanation=explanation,
            evidence=MappingProxyType(
                {
                    "correlation_title": correlation.title,
                    "correlation_severity": (
                        correlation.severity.value
                    ),
                    "matched_finding_ids": (
                        correlation.matched_finding_ids
                    ),
                }
            ),
        )