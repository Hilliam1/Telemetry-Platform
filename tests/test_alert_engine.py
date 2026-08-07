from datetime import datetime, timezone

from app.alerts.engine import AlertEngine
from app.alerts.models import AlertStatus
from app.alerts.policy import AlertPolicy
from app.correlation.models import CorrelationMatch
from app.detection.models import DetectionSeverity
from app.risk.engine import RiskEngine
from app.risk.models import RiskAssessment, RiskLevel
from app.risk.policy import RiskPolicy
from app.risk.providers import RepeatedActivityRiskProvider


def make_assessment(
    *,
    score: int,
    level: RiskLevel,
) -> RiskAssessment:
    now = datetime.now(timezone.utc)

    return RiskAssessment(
        assessment_id="assessment-1",
        correlation_id="correlation-1",
        correlation_rule_id="TP-CORR-WIN-0001",
        score=score,
        level=level,
        base_score=40,
        contributions=(),
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        assessed_at=now,
        explanation="test",
        evidence={},
    )


def make_repeated_activity_correlation() -> CorrelationMatch:
    now = datetime.now(timezone.utc)

    return CorrelationMatch(
        correlation_id="correlation-1",
        rule_id="TP-CORR-WIN-0002",
        rule_version=1,
        title="Repeated Encoded PowerShell Activity",
        severity=DetectionSeverity.HIGH,
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        matched_finding_ids=("finding-1", "finding-2"),
        matched_detection_rule_ids=(
            "TP-WIN-SYSMON-0002",
            "TP-WIN-SYSMON-0002",
        ),
        explanation="test",
        investigation_steps=(),
        evidence={},
        tags=(),
    )


def test_low_risk_assessment_returns_none():
    engine = AlertEngine(policy=AlertPolicy(minimum_score=40))

    assert engine.evaluate(
        make_assessment(
            score=25,
            level=RiskLevel.LOW,
        )
    ) is None


def test_risk_at_threshold_creates_alert():
    engine = AlertEngine(policy=AlertPolicy(minimum_score=40))

    alert = engine.evaluate(
        make_assessment(
            score=40,
            level=RiskLevel.MEDIUM,
        )
    )

    assert alert is not None
    assert alert.status is AlertStatus.NEW
    assert alert.risk_score == 40


def test_high_risk_assessment_creates_alert():
    engine = AlertEngine(policy=AlertPolicy(minimum_score=40))

    alert = engine.evaluate(
        make_assessment(
            score=80,
            level=RiskLevel.CRITICAL,
        )
    )

    assert alert is not None
    assert alert.risk_score == 80


def test_engine_does_not_modify_assessment():
    assessment = make_assessment(
        score=80,
        level=RiskLevel.CRITICAL,
    )
    original = (
        assessment.assessment_id,
        assessment.score,
        assessment.level,
        assessment.evidence,
    )

    AlertEngine(policy=AlertPolicy()).evaluate(assessment)

    assert (
        assessment.assessment_id,
        assessment.score,
        assessment.level,
        assessment.evidence,
    ) == original


def test_correlation_to_risk_to_alert_chain():
    correlation = make_repeated_activity_correlation()
    risk_engine = RiskEngine(
        policy=RiskPolicy(),
        providers=(RepeatedActivityRiskProvider(),),
    )
    alert_engine = AlertEngine(
        policy=AlertPolicy(minimum_score=40),
    )

    assessment = risk_engine.assess(correlation)
    alert = alert_engine.evaluate(assessment)

    assert assessment.score == 80
    assert assessment.level is RiskLevel.CRITICAL
    assert alert is not None
    assert alert.assessment_id == assessment.assessment_id
    assert alert.correlation_id == correlation.correlation_id
    assert alert.risk_level is RiskLevel.CRITICAL
