from datetime import datetime, timezone

import pytest

from app.alerts.policy import AlertPolicy
from app.risk.models import RiskAssessment, RiskLevel


def make_assessment(
    *,
    score: int,
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
        contributions=(),
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        assessed_at=now,
        explanation="test",
        evidence={},
    )


def test_score_below_threshold_does_not_alert():
    policy = AlertPolicy(minimum_score=40)

    assert not policy.should_alert(make_assessment(score=39))


def test_score_at_threshold_alerts():
    policy = AlertPolicy(minimum_score=40)

    assert policy.should_alert(make_assessment(score=40))


def test_score_above_threshold_alerts():
    policy = AlertPolicy(minimum_score=40)

    assert policy.should_alert(make_assessment(score=80))


@pytest.mark.parametrize(
    "minimum_score",
    (-1, 101),
)
def test_invalid_threshold_is_rejected(
    minimum_score,
):
    with pytest.raises(ValueError):
        AlertPolicy(
            minimum_score=minimum_score
        )


@pytest.mark.parametrize(
    "minimum_score",
    (40.5, "40", None, True),
)
def test_non_integer_threshold_is_rejected(
    minimum_score,
):
    with pytest.raises(TypeError):
        AlertPolicy(
            minimum_score=minimum_score
        )


def test_policy_builds_title_and_summary():
    policy = AlertPolicy()
    assessment = make_assessment(
        score=80,
        level=RiskLevel.CRITICAL,
    )

    assert policy.title_for(assessment) == (
        "Critical Risk Activity on HOST-01"
    )
    assert "score 80/100" in policy.summary_for(assessment)
