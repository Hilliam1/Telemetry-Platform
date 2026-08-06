from dataclasses import replace
from datetime import datetime, timezone

import pytest

from app.detection.engine import DetectionEngine
from app.detection.models import (
    DetectionRule,
    DetectionSeverity,
    FieldCondition,
)
from app.detection.rules import BUILTIN_RULES


def make_event(
    *,
    image: str = (
        r"C:\Windows\System32\WindowsPowerShell"
        r"\v1.0\powershell.exe"
    ),
    command_line: str = "powershell.exe Get-Process",
    source_type: str = "sysmon",
    event_id: int = 1,
) -> dict:
    return {
        "provider": "Microsoft-Windows-Sysmon",
        "event_id": event_id,
        "record_id": 100,
        "severity": "Information",
        "time_created": datetime.now(timezone.utc),
        "computer": "HOST-01",
        "source_type": source_type,
        "message": "",
        "raw": {
            "event_data": {
                "Image": image,
                "CommandLine": command_line,
                "ParentImage": (
                    r"C:\Windows\explorer.exe"
                ),
                "User": r"DOMAIN\user",
            },
            "user_data": {},
        },
    }


def test_normal_powershell_produces_low_finding():
    engine = DetectionEngine(BUILTIN_RULES)

    findings = engine.evaluate(make_event())

    assert len(findings) == 1
    assert findings[0].rule_id == "TP-WIN-SYSMON-0001"
    assert findings[0].severity is DetectionSeverity.LOW


def test_encoded_powershell_matches_both_rules():
    engine = DetectionEngine(BUILTIN_RULES)

    findings = engine.evaluate(
        make_event(
            command_line=(
                "powershell.exe -EncodedCommand SQBFAFgA"
            )
        )
    )

    assert {finding.rule_id for finding in findings} == {
        "TP-WIN-SYSMON-0001",
        "TP-WIN-SYSMON-0002",
    }


@pytest.mark.parametrize(
    "switch",
    (
        "-enc",
        "-ENC",
        "-EncodedCommand",
        "/enc",
    ),
)
def test_encoded_switch_variants_match(switch):
    engine = DetectionEngine(BUILTIN_RULES)

    findings = engine.evaluate(
        make_event(
            command_line=(
                f"powershell.exe {switch} SQBFAFgA"
            )
        )
    )

    assert any(
        finding.rule_id == "TP-WIN-SYSMON-0002"
        for finding in findings
    )


def test_non_powershell_process_does_not_match():
    engine = DetectionEngine(BUILTIN_RULES)

    findings = engine.evaluate(
        make_event(
            image=r"C:\Windows\System32\notepad.exe",
            command_line="notepad.exe",
        )
    )

    assert findings == ()


def test_wrong_source_does_not_match():
    engine = DetectionEngine(BUILTIN_RULES)

    findings = engine.evaluate(
        make_event(source_type="windows_system")
    )

    assert findings == ()


def test_wrong_event_id_does_not_match():
    engine = DetectionEngine(BUILTIN_RULES)

    findings = engine.evaluate(
        make_event(event_id=3)
    )

    assert findings == ()


def test_missing_fields_do_not_crash():
    engine = DetectionEngine(BUILTIN_RULES)

    findings = engine.evaluate(
        {
            "source_type": "sysmon",
            "event_id": 1,
            "raw": {},
        }
    )

    assert findings == ()


def test_disabled_rule_never_matches():
    disabled_rule = replace(
        BUILTIN_RULES[0],
        enabled=False,
    )
    engine = DetectionEngine((disabled_rule,))

    assert engine.evaluate(make_event()) == ()


def test_duplicate_rule_identity_is_rejected():
    rule = BUILTIN_RULES[0]

    with pytest.raises(
        ValueError,
        match="Duplicate detection rule identity",
    ):
        DetectionEngine((rule, rule))


def test_unknown_operator_is_rejected():
    invalid_rule = DetectionRule(
        rule_id="TP-TEST-INVALID",
        version=1,
        name="Invalid",
        description="Invalid operator",
        severity=DetectionSeverity.LOW,
        source_type="sysmon",
        event_id=1,
        conditions=(
            FieldCondition(
                field_path="raw.event_data.Image",
                operator="magic_operator",
                values=("test",),
            ),
        ),
        explanation="Invalid",
    )

    with pytest.raises(
        ValueError,
        match="unsupported operator",
    ):
        DetectionEngine((invalid_rule,))