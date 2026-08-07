from datetime import datetime, timezone

from app.correlation.identity import correlation_key
from app.correlation.models import CorrelationMatch
from app.detection.models import DetectionSeverity


def make_match(
    *,
    finding_ids: tuple[str, ...],
    event_record_ids: tuple[int, ...],
) -> CorrelationMatch:
    now = datetime.now(timezone.utc)

    return CorrelationMatch(
        correlation_id="3f76fcd5-4c78-4fa1-bf42-f49dddc15b72",
        rule_id="TP-CORR-WIN-0001",
        rule_version=1,
        title="Encoded PowerShell Execution",
        severity=DetectionSeverity.MEDIUM,
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        matched_finding_ids=finding_ids,
        matched_detection_rule_ids=(
            "TP-WIN-SYSMON-0001",
            "TP-WIN-SYSMON-0002",
        ),
        explanation="test",
        investigation_steps=(),
        evidence={},
        tags=(),
        matched_event_keys=tuple(
            sorted(
                (
                    "HOST-01|sysmon|1|"
                    f"{event_record_id}|{rule_id}|1"
                )
                for event_record_id, rule_id in zip(
                    event_record_ids,
                    (
                        "TP-WIN-SYSMON-0001",
                        "TP-WIN-SYSMON-0002",
                    ),
                    strict=True,
                )
            )
        ),
    )


def test_correlation_key_survives_regenerated_finding_ids():
    first_match = make_match(
        finding_ids=("uuid-a", "uuid-b"),
        event_record_ids=(100, 100),
    )
    replayed_match = make_match(
        finding_ids=("uuid-c", "uuid-d"),
        event_record_ids=(100, 100),
    )

    assert correlation_key(first_match) == correlation_key(
        replayed_match
    )


def test_correlation_key_changes_for_different_source_events():
    event_100 = make_match(
        finding_ids=("uuid-a", "uuid-b"),
        event_record_ids=(100, 100),
    )
    event_101 = make_match(
        finding_ids=("uuid-c", "uuid-d"),
        event_record_ids=(101, 101),
    )

    assert correlation_key(event_100) != correlation_key(event_101)
