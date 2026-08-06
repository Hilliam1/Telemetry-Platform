"""Typed models for deterministic detection correlation."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from types import MappingProxyType
from typing import Any
from uuid import uuid4

from app.detection.models import DetectionFinding, DetectionSeverity


class CorrelationMode(str, Enum):
    """Supported correlation strategies."""

    SAME_EVENT = "same_event"
    TEMPORAL_COUNT = "temporal_count"


@dataclass(frozen=True)
class CorrelationRule:
    """Versioned rule for correlating detection findings."""

    rule_id: str
    version: int
    name: str
    description: str
    severity: DetectionSeverity
    mode: CorrelationMode
    required_detection_rule_ids: tuple[str, ...]
    group_by: tuple[str, ...]
    window_seconds: int
    minimum_matches: int
    explanation: str
    investigation_steps: tuple[str, ...] = ()
    enabled: bool = True
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class CorrelationMatch:
    """Structured result produced by a correlation rule."""

    correlation_id: str
    rule_id: str
    rule_version: int
    title: str
    severity: DetectionSeverity
    source_host: str
    first_event_time: datetime
    last_event_time: datetime
    matched_finding_ids: tuple[str, ...]
    matched_detection_rule_ids: tuple[str, ...]
    explanation: str
    investigation_steps: tuple[str, ...]
    evidence: Mapping[str, Any]
    tags: tuple[str, ...]

    @classmethod
    def from_findings(
        cls,
        *,
        rule: CorrelationRule,
        findings: tuple[DetectionFinding, ...],
        evidence: dict[str, Any],
    ) -> CorrelationMatch:
        if not findings:
            raise ValueError(
                "CorrelationMatch requires at least one finding"
            )

        ordered = tuple(
            sorted(
                findings,
                key=lambda finding: finding.event_time,
            )
        )

        return cls(
            correlation_id=str(uuid4()),
            rule_id=rule.rule_id,
            rule_version=rule.version,
            title=rule.name,
            severity=rule.severity,
            source_host=ordered[0].source_host,
            first_event_time=ordered[0].event_time,
            last_event_time=ordered[-1].event_time,
            matched_finding_ids=tuple(
                finding.finding_id
                for finding in ordered
            ),
            matched_detection_rule_ids=tuple(
                finding.rule_id
                for finding in ordered
            ),
            explanation=rule.explanation,
            investigation_steps=rule.investigation_steps,
            evidence=MappingProxyType(dict(evidence)),
            tags=rule.tags,
        )
