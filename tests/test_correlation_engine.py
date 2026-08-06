from datetime import datetime, timedelta, timezone

from app.correlation.engine import CorrelationEngine
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