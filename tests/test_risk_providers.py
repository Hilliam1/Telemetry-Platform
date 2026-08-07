from datetime import datetime, timezone

from app.correlation.models import CorrelationMatch
from app.detection.models import DetectionSeverity
from app.risk.providers import (
    RepeatedActivityRiskProvider,
)


def make_correlation(
    rule_id: str,
) -> CorrelationMatch:
    now = datetime.now(timezone.utc)

    return CorrelationMatch(
        correlation_id="corr-1",
        rule_id=rule_id,
        rule_version=1,
        title="test",
        severity=DetectionSeverity.HIGH,
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        matched_finding_ids=("one", "two"),
        matched_detection_rule_ids=(
            "TP-WIN-SYSMON-0002",
            "TP-WIN-SYSMON-0002",
        ),
        explanation="test",
        investigation_steps=(),
        evidence={},
        tags=(),
    )


def test_repeated_activity_provider_adds_risk():
    provider = RepeatedActivityRiskProvider()

    contributions = provider.evaluate(
        make_correlation("TP-CORR-WIN-0002")
    )

    assert len(contributions) == 1
    assert contributions[0].score_delta == 15


def test_repeated_activity_provider_ignores_other_rules():
    provider = RepeatedActivityRiskProvider()

    assert (
        provider.evaluate(
            make_correlation("TP-CORR-WIN-0001")
        )
        == ()
    )