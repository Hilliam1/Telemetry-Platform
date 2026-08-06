from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from app.detection.models import (
    DetectionFinding,
    DetectionRule,
    DetectionSeverity,
    FieldCondition,
)


def make_rule() -> DetectionRule:
    return DetectionRule(
        rule_id="TP-TEST-0001",
        version=1,
        name="Test Rule",
        description="Test",
        severity=DetectionSeverity.LOW,
        source_type="sysmon",
        event_id=1,
        conditions=(
            FieldCondition(
                field_path="raw.event_data.Image",
                operator="ends_with_any",
                values=("powershell.exe",),
            ),
        ),
        explanation="Test explanation",
    )


def test_rule_is_immutable():
    rule = make_rule()

    with pytest.raises(FrozenInstanceError):
        rule.name = "Changed"


def test_finding_is_created_from_event():
    rule = make_rule()
    event_time = datetime.now(timezone.utc)

    event = {
        "computer": "HOST-01",
        "source_type": "sysmon",
        "event_id": 1,
        "record_id": 42,
        "time_created": event_time,
    }

    finding = DetectionFinding.from_match(
        rule=rule,
        event=event,
        evidence={"Image": "powershell.exe"},
    )

    assert finding.rule_id == "TP-TEST-0001"
    assert finding.rule_version == 1
    assert finding.source_host == "HOST-01"
    assert finding.event_record_id == 42
    assert finding.event_time == event_time
    assert finding.evidence == {
        "Image": "powershell.exe"
    }


def test_finding_ignores_invalid_record_id():
    rule = make_rule()

    finding = DetectionFinding.from_match(
        rule=rule,
        event={
            "computer": "HOST-01",
            "source_type": "sysmon",
            "event_id": 1,
            "record_id": "not-a-number",
        },
        evidence={},
    )

    assert finding.event_record_id is None


def test_finding_evidence_is_read_only():
    rule = make_rule()

    finding = DetectionFinding.from_match(
        rule=rule,
        event={
            "computer": "HOST-01",
            "source_type": "sysmon",
            "event_id": 1,
        },
        evidence={"Image": "powershell.exe"},
    )

    with pytest.raises(TypeError):
        finding.evidence["Image"] = "changed.exe"
