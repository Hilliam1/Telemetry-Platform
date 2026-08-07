"""API response models for persisted intelligence."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.alerts.models import AlertStatus
from app.detection.models import DetectionSeverity
from app.risk.models import RiskLevel


class IntelligenceResponse(BaseModel):
    """Base API model for intelligence responses."""

    model_config = ConfigDict(
        from_attributes=True,
    )


class DetectionFindingResponse(IntelligenceResponse):
    finding_uuid: UUID
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

    investigation_steps: list[str]
    evidence: dict[str, Any]
    tags: list[str]


class CorrelationMatchResponse(IntelligenceResponse):
    correlation_uuid: UUID

    rule_id: str
    rule_version: int

    title: str
    severity: DetectionSeverity

    source_host: str

    first_event_time: datetime
    last_event_time: datetime

    matched_finding_ids: list[UUID]
    matched_detection_rule_ids: list[str]

    explanation: str
    investigation_steps: list[str]

    evidence: dict[str, Any]
    tags: list[str]


class RiskAssessmentResponse(IntelligenceResponse):
    assessment_uuid: UUID
    correlation_uuid: UUID
    correlation_rule_id: str

    score: int
    level: RiskLevel
    base_score: int

    contributions: list[dict[str, Any]]

    source_host: str

    first_event_time: datetime
    last_event_time: datetime
    assessed_at: datetime

    explanation: str
    evidence: dict[str, Any]


class AlertResponse(IntelligenceResponse):
    alert_uuid: UUID

    assessment_uuid: UUID
    correlation_uuid: UUID
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
    evidence: dict[str, Any]
