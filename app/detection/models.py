"""Typed models used by the deterministic detection subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class DetectionSeverity(str, Enum):
    """Supported finding severity levels."""

    INFORMATIONAL = "informational"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class FieldCondition:
    """One deterministic field comparison within a detection rule."""

    field_path: str
    operator: str
    values: tuple[str, ...]
    case_sensitive: bool = False


@dataclass(frozen=True)
class DetectionRule:
    """Versioned deterministic rule evaluated against normalized events."""

    rule_id: str
    version: int
    name: str
    description: str
    severity: DetectionSeverity
    source_type: str
    event_id: int
    conditions: tuple[FieldCondition, ...]
    explanation: str
    investigation_steps: tuple[str, ...] = ()
    enabled: bool = True
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class DetectionFinding:
    """Structured evidence that a normalized event matched a rule."""

    finding_id: str
    rule_id: str
    rule_version: int
    title: str
    severity: DetectionSeverity
    source_host: str
    source_type: str
    event_id: int
    event_record_id: int | None
    event_time: datetime
    evaluated_at: datetime
    explanation: str
    investigation_steps: tuple[str, ...]
    evidence: dict[str, Any] = field(default_factory=dict)
    tags: tuple[str, ...] = ()

    @classmethod
    def from_match(
        cls,
        *,
        rule: DetectionRule,
        event: dict[str, Any],
        evidence: dict[str, Any],
    ) -> DetectionFinding:
        event_time = event.get("time_created")

        if not isinstance(event_time, datetime):
            event_time = datetime.now(timezone.utc)

        record_id = event.get("record_id")
        event_record_id = None

        if record_id is not None:
            try:
                event_record_id = int(record_id)
            except (TypeError, ValueError):
                event_record_id = None

        return cls(
            finding_id=str(uuid4()),
            rule_id=rule.rule_id,
            rule_version=rule.version,
            title=rule.name,
            severity=rule.severity,
            source_host=event.get("computer", ""),
            source_type=event.get("source_type", ""),
            event_id=int(event.get("event_id", 0) or 0),
            event_record_id=event_record_id,
            event_time=event_time,
            evaluated_at=datetime.now(timezone.utc),
            explanation=rule.explanation,
            investigation_steps=rule.investigation_steps,
            evidence=dict(evidence),
            tags=rule.tags,
        )
