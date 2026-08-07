from datetime import datetime, timezone
from unittest.mock import Mock

import pytest

from app.correlation.models import CorrelationMatch
from app.detection.models import DetectionSeverity
from app.risk.engine import RiskEngine
from app.risk.models import (
    RiskContribution,
    RiskLevel,
)
from app.risk.policy import RiskPolicy
from app.risk.providers import (
    RepeatedActivityRiskProvider,
    RiskProvider,
)


def make_correlation(
    *,
    rule_id: str = "TP-CORR-WIN-0001",
    severity: DetectionSeverity = (
        DetectionSeverity.MEDIUM
    ),
) -> CorrelationMatch:
    now = datetime.now(timezone.utc)

    return CorrelationMatch(
        correlation_id="corr-1",
        rule_id=rule_id,
        rule_version=1,
        title="test",
        severity=severity,
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        matched_finding_ids=("one", "two"),
        matched_detection_rule_ids=(
            "TP-WIN-SYSMON-0001",
            "TP-WIN-SYSMON-0002",
        ),
        explanation="test",
        investigation_steps=(),
        evidence={},
        tags=(),
    )


def test_medium_correlation_starts_at_40():
    engine = RiskEngine(
        policy=RiskPolicy()
    )

    assessment = engine.assess(
        make_correlation()
    )

    assert assessment.base_score == 40
    assert assessment.score == 40
    assert assessment.level is RiskLevel.MEDIUM


def test_provider_contribution_changes_score():
    engine = RiskEngine(
        policy=RiskPolicy(),
        providers=(
            RepeatedActivityRiskProvider(),
        ),
    )

    assessment = engine.assess(
        make_correlation(
            rule_id="TP-CORR-WIN-0002",
            severity=DetectionSeverity.HIGH,
        )
    )

    assert assessment.base_score == 65
    assert assessment.score == 80
    assert assessment.level is RiskLevel.CRITICAL


def test_score_is_clamped_to_100():
    provider = Mock(spec=RiskProvider)
    provider.name = "test"
    provider.evaluate.return_value = (
        RiskContribution.create(
            provider="test",
            reason="large increase",
            score_delta=100,
        ),
    )

    engine = RiskEngine(
        policy=RiskPolicy(),
        providers=(provider,),
    )

    assessment = engine.assess(
        make_correlation(
            severity=DetectionSeverity.CRITICAL
        )
    )

    assert assessment.score == 100


def test_duplicate_provider_names_are_rejected():
    first = Mock(spec=RiskProvider)
    second = Mock(spec=RiskProvider)

    first.name = "duplicate"
    second.name = "duplicate"

    with pytest.raises(
        ValueError,
        match="Duplicate risk provider name",
    ):
        RiskEngine(
            policy=RiskPolicy(),
            providers=(first, second),
        )