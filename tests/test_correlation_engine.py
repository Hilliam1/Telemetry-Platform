from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from app.correlation.engine import CorrelationEngine
from app.correlation.models import CorrelationMode
from app.correlation.rules import (
    BUILTIN_CORRELATION_RULES,
)
from app.detection.models import (
    DetectionFinding,
    DetectionSeverity,
)

BASE_TIME = datetime.now(timezone.utc)


def make_finding(
    *,
    finding_id: str,
    rule_id: str,
    event_record_id: int,
    seconds: int = 0,
    host: str = "HOST-01",
) -> DetectionFinding:
    event_time = BASE_TIME + timedelta(seconds=seconds)

    return DetectionFinding(
        finding_id=finding_id,
        rule_id=rule_id,
        rule_version=1,
        title=rule_id,
        severity=DetectionSeverity.MEDIUM,
        source_host=host,
        source_type="sysmon",
        event_id=1,
        event_record_id=event_record_id,
        event_time=event_time,
        evaluated_at=event_time,
        explanation="test",
        investigation_steps=(),
        evidence={},
        tags=(),
    )


def test_same_event_correlation_matches():
    engine = CorrelationEngine(
        BUILTIN_CORRELATION_RULES
    )

    findings = (
        make_finding(
            finding_id="finding-1",
            rule_id="TP-WIN-SYSMON-0001",
            event_record_id=100,
        ),
        make_finding(
            finding_id="finding-2",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=100,
        ),
    )

    matches = engine.evaluate(findings)

    encoded_matches = tuple(
        match
        for match in matches
        if match.rule_id == "TP-CORR-WIN-0001"
    )

    assert len(encoded_matches) == 1
    assert encoded_matches[0].source_host == "HOST-01"
    assert set(
        encoded_matches[0].matched_detection_rule_ids
    ) == {
        "TP-WIN-SYSMON-0001",
        "TP-WIN-SYSMON-0002",
    }


def test_same_event_rule_rejects_different_record_ids():
    engine = CorrelationEngine(
        BUILTIN_CORRELATION_RULES
    )

    findings = (
        make_finding(
            finding_id="finding-1",
            rule_id="TP-WIN-SYSMON-0001",
            event_record_id=100,
        ),
        make_finding(
            finding_id="finding-2",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=101,
        ),
    )

    matches = engine.evaluate(findings)

    assert not any(
        match.rule_id == "TP-CORR-WIN-0001"
        for match in matches
    )


def test_same_event_rule_rejects_different_hosts():
    engine = CorrelationEngine(
        BUILTIN_CORRELATION_RULES
    )

    findings = (
        make_finding(
            finding_id="finding-1",
            rule_id="TP-WIN-SYSMON-0001",
            event_record_id=100,
            host="HOST-01",
        ),
        make_finding(
            finding_id="finding-2",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=100,
            host="HOST-02",
        ),
    )

    matches = engine.evaluate(findings)

    assert not any(
        match.rule_id == "TP-CORR-WIN-0001"
        for match in matches
    )


def test_repeated_encoded_activity_matches():
    engine = CorrelationEngine(
        BUILTIN_CORRELATION_RULES
    )

    findings = (
        make_finding(
            finding_id="finding-1",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=100,
            seconds=0,
        ),
        make_finding(
            finding_id="finding-2",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=101,
            seconds=300,
        ),
    )

    matches = engine.evaluate(findings)

    repeated = tuple(
        match
        for match in matches
        if match.rule_id == "TP-CORR-WIN-0002"
    )

    assert len(repeated) == 1
    assert len(
        repeated[0].matched_finding_ids
    ) == 2


def test_repeated_activity_rejects_outside_window():
    engine = CorrelationEngine(
        BUILTIN_CORRELATION_RULES
    )

    findings = (
        make_finding(
            finding_id="finding-1",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=100,
            seconds=0,
        ),
        make_finding(
            finding_id="finding-2",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=101,
            seconds=601,
        ),
    )

    matches = engine.evaluate(findings)

    assert not any(
        match.rule_id == "TP-CORR-WIN-0002"
        for match in matches
    )


def test_repeated_activity_does_not_cross_hosts():
    engine = CorrelationEngine(
        BUILTIN_CORRELATION_RULES
    )

    findings = (
        make_finding(
            finding_id="finding-1",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=100,
            host="HOST-01",
        ),
        make_finding(
            finding_id="finding-2",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=101,
            host="HOST-02",
            seconds=60,
        ),
    )

    matches = engine.evaluate(findings)

    assert not any(
        match.rule_id == "TP-CORR-WIN-0002"
        for match in matches
    )


def test_empty_findings_return_no_matches():
    engine = CorrelationEngine(
        BUILTIN_CORRELATION_RULES
    )

    assert engine.evaluate(()) == ()


def test_disabled_rule_does_not_match():
    disabled_rule = replace(
        BUILTIN_CORRELATION_RULES[0],
        enabled=False,
    )
    engine = CorrelationEngine((disabled_rule,))

    findings = (
        make_finding(
            finding_id="finding-1",
            rule_id="TP-WIN-SYSMON-0001",
            event_record_id=100,
        ),
        make_finding(
            finding_id="finding-2",
            rule_id="TP-WIN-SYSMON-0002",
            event_record_id=100,
        ),
    )

    assert engine.evaluate(findings) == ()


def test_duplicate_rule_identity_is_rejected():
    rule = BUILTIN_CORRELATION_RULES[0]

    with pytest.raises(
        ValueError,
        match="Duplicate correlation rule identity",
    ):
        CorrelationEngine((rule, rule))


def test_unknown_grouping_field_is_rejected():
    invalid_rule = replace(
        BUILTIN_CORRELATION_RULES[0],
        rule_id="TP-CORR-TEST-INVALID",
        group_by=("source_hots",),
    )

    with pytest.raises(
        ValueError,
        match="unsupported grouping fields",
    ):
        CorrelationEngine((invalid_rule,))


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    (
        ("required_detection_rule_ids", (), "requires no detection rules"),
        ("group_by", (), "has no grouping fields"),
        ("window_seconds", 0, "positive correlation window"),
        ("minimum_matches", 0, "at least one match"),
    ),
)
def test_invalid_rule_settings_are_rejected(
    field_name,
    value,
    message,
):
    invalid_rule = replace(
        BUILTIN_CORRELATION_RULES[0],
        rule_id=f"TP-CORR-TEST-{field_name}",
        **{field_name: value},
    )

    with pytest.raises(ValueError, match=message):
        CorrelationEngine((invalid_rule,))


def test_same_event_minimum_matches_must_cover_required_rules():
    invalid_rule = replace(
        BUILTIN_CORRELATION_RULES[0],
        rule_id="TP-CORR-TEST-MINIMUM",
        mode=CorrelationMode.SAME_EVENT,
        minimum_matches=1,
    )

    with pytest.raises(
        ValueError,
        match="requires fewer matches",
    ):
        CorrelationEngine((invalid_rule,))
