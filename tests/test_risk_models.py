"""Tests for risk model contracts."""

from datetime import datetime, timezone

import pytest

from app.correlation.models import CorrelationMatch
from app.detection.models import DetectionSeverity
from app.risk.models import (
    RiskAssessment,
    RiskContribution,
    RiskLevel,
)


def make_correlation() -> CorrelationMatch:
    now = datetime.now(timezone.utc)

    return CorrelationMatch(
        correlation_id="corr-1",
        rule_id="TP-CORR-WIN-0001",
        rule_version=1,
        title="Encoded PowerShell Execution",
        severity=DetectionSeverity.MEDIUM,
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        matched_finding_ids=("finding-1", "finding-2"),
        matched_detection_rule_ids=(
            "TP-WIN-SYSMON-0001",
            "TP-WIN-SYSMON-0002",
        ),
        explanation="test",
        investigation_steps=(),
        evidence={},
        tags=(),
    )


def test_risk_contribution_evidence_is_read_only():
    contribution = RiskContribution.create(
        provider="test",
        reason="test contribution",
        score_delta=5,
        evidence={"host": "HOST-01"},
    )

    with pytest.raises(TypeError):
        contribution.evidence["host"] = "HOST-02"


def test_risk_assessment_preserves_correlation_identity():
    correlation = make_correlation()
    now = datetime.now(timezone.utc)

    assessment = RiskAssessment.create(
        correlation=correlation,
        score=40,
        level=RiskLevel.MEDIUM,
        base_score=40,
        contributions=(),
        assessed_at=now,
    )

    assert assessment.correlation_id == correlation.correlation_id
    assert assessment.correlation_rule_id == correlation.rule_id


def test_risk_assessment_evidence_is_read_only():
    correlation = make_correlation()

    assessment = RiskAssessment.create(
        correlation=correlation,
        score=40,
        level=RiskLevel.MEDIUM,
        base_score=40,
        contributions=(),
        assessed_at=datetime.now(timezone.utc),
    )

    with pytest.raises(TypeError):
        assessment.evidence["correlation_title"] = "changed"