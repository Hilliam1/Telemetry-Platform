from datetime import datetime, timezone

import pytest

from app.alerts.models import Alert, AlertStatus
from app.risk.models import (
    RiskAssessment,
    RiskContribution,
    RiskLevel,
)


def make_assessment(
    *,
    score: int = 40,
    level: RiskLevel = RiskLevel.MEDIUM,
) -> RiskAssessment:
    now = datetime.now(timezone.utc)

    return RiskAssessment(
        assessment_id="assessment-1",
        correlation_id="correlation-1",
        correlation_rule_id="TP-CORR-WIN-0001",
        score=score,
        level=level,
        base_score=40,
        contributions=(
            RiskContribution.create(
                provider="test",
                reason="test contribution",
                score_delta=0,
                evidence={"provider": "test"},
            ),
        ),
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        assessed_at=now,
        explanation="test",
        evidence={
            "correlation_title": "Encoded PowerShell Execution",
            "matched_finding_ids": ("finding-1", "finding-2"),
            "details": {
                "commands": [
                    {
                        "image": "powershell.exe",
                    }
                ],
            },
        },
    )


def make_alert() -> Alert:
    return Alert.create(
        assessment=make_assessment(),
        title="Medium Risk Activity on HOST-01",
        summary="Risk assessment assessment-1 produced score 40/100.",
        created_at=datetime.now(timezone.utc),
    )


def test_new_alert_starts_new():
    alert = make_alert()

    assert alert.status is AlertStatus.NEW


def test_alert_preserves_risk_and_correlation_identity():
    assessment = make_assessment()

    alert = Alert.create(
        assessment=assessment,
        title="Medium Risk Activity on HOST-01",
        summary="test",
        created_at=datetime.now(timezone.utc),
    )

    assert alert.assessment_id == assessment.assessment_id
    assert alert.correlation_id == assessment.correlation_id
    assert alert.correlation_rule_id == assessment.correlation_rule_id
    assert alert.risk_score == assessment.score
    assert alert.risk_level is assessment.level


def test_alert_evidence_is_read_only():
    alert = make_alert()

    with pytest.raises(TypeError):
        alert.evidence["base_score"] = 999


def test_alert_nested_risk_evidence_is_read_only():
    alert = make_alert()

    with pytest.raises(TypeError):
        alert.evidence["risk_evidence"]["correlation_title"] = "changed"


def test_alert_deep_nested_risk_evidence_is_read_only():
    alert = make_alert()

    with pytest.raises(TypeError):
        alert.evidence["risk_evidence"]["details"]["commands"][0][
            "image"
        ] = "cmd.exe"
