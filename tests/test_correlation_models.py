
from datetime import datetime, timezone

import pytest

from app.correlation.models import (
    CorrelationMatch,
)
from app.correlation.rules import (
    ENCODED_POWERSHELL_EXECUTION,
)
from app.detection.models import (
    DetectionFinding,
    DetectionSeverity,
)


def make_finding(
    finding_id: str,
    rule_id: str,
) -> DetectionFinding:
    now = datetime.now(timezone.utc)

    return DetectionFinding(
        finding_id=finding_id,
        rule_id=rule_id,
        rule_version=1,
        title=rule_id,
        severity=DetectionSeverity.MEDIUM,
        source_host="HOST-01",
        source_type="sysmon",
        event_id=1,
        event_record_id=100,
        event_time=now,
        evaluated_at=now,
        explanation="test",
        investigation_steps=(),
        evidence={},
        tags=(),
    )


def test_correlation_evidence_is_read_only():
    match = CorrelationMatch.from_findings(
        rule=ENCODED_POWERSHELL_EXECUTION,
        findings=(
            make_finding(
                "finding-1",
                "TP-WIN-SYSMON-0001",
            ),
            make_finding(
                "finding-2",
                "TP-WIN-SYSMON-0002",
            ),
        ),
        evidence={"finding_count": 2},
    )

    with pytest.raises(TypeError):
        match.evidence["finding_count"] = 3


def test_correlation_preserves_finding_ids():
    match = CorrelationMatch.from_findings(
        rule=ENCODED_POWERSHELL_EXECUTION,
        findings=(
            make_finding(
                "finding-1",
                "TP-WIN-SYSMON-0001",
            ),
            make_finding(
                "finding-2",
                "TP-WIN-SYSMON-0002",
            ),
        ),
        evidence={},
    )

    assert set(match.matched_finding_ids) == {
        "finding-1",
        "finding-2",
    }


def test_correlation_preserves_stable_event_keys():
    match = CorrelationMatch.from_findings(
        rule=ENCODED_POWERSHELL_EXECUTION,
        findings=(
            make_finding(
                "finding-1",
                "TP-WIN-SYSMON-0001",
            ),
            make_finding(
                "finding-2",
                "TP-WIN-SYSMON-0002",
            ),
        ),
        evidence={},
    )

    assert match.matched_event_keys == (
        "HOST-01|sysmon|1|100|TP-WIN-SYSMON-0001|1",
        "HOST-01|sysmon|1|100|TP-WIN-SYSMON-0002|1",
    )


def test_correlation_match_requires_at_least_one_finding():
    with pytest.raises(
        ValueError,
        match="requires at least one finding",
    ):
        CorrelationMatch.from_findings(
            rule=ENCODED_POWERSHELL_EXECUTION,
            findings=(),
            evidence={},
        )
