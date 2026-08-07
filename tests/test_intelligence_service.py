from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from app.alerts.engine import AlertEngine
from app.alerts.policy import AlertPolicy
from app.correlation.engine import CorrelationEngine
from app.correlation.models import (
    CorrelationMode,
    CorrelationRule,
)
from app.correlation.rules import BUILTIN_CORRELATION_RULES
from app.detection.models import DetectionFinding, DetectionSeverity
from app.intelligence.service import IntelligenceService
from app.risk.engine import RiskEngine
from app.risk.models import RiskLevel
from app.risk.policy import RiskPolicy
from app.risk.providers import RepeatedActivityRiskProvider


def make_finding(
    *,
    finding_id: str,
    rule_id: str = "TP-WIN-SYSMON-0002",
    event_time: datetime,
    source_host: str = "HOST-01",
    event_record_id: int = 42,
) -> DetectionFinding:
    return DetectionFinding(
        finding_id=finding_id,
        rule_id=rule_id,
        rule_version=1,
        title="Encoded PowerShell Command",
        severity=DetectionSeverity.MEDIUM,
        source_host=source_host,
        source_type="sysmon",
        event_id=1,
        event_record_id=event_record_id,
        event_time=event_time,
        evaluated_at=event_time,
        explanation="Encoded PowerShell was detected.",
        investigation_steps=("Decode the command.",),
        evidence={
            "raw.event_data.CommandLine":
                "powershell.exe -enc SQBFAFgA"
        },
        tags=("powershell", "encoded_command"),
    )


def make_service(
    *,
    rules=BUILTIN_CORRELATION_RULES,
    providers=None,
):
    if providers is None:
        providers = (RepeatedActivityRiskProvider(),)

    detection_repository = Mock()
    correlation_repository = Mock()
    risk_repository = Mock()
    alert_repository = Mock()

    correlation_repository.insert_match.return_value = True

    service = IntelligenceService(
        detection_repository=detection_repository,
        correlation_engine=CorrelationEngine(rules),
        correlation_repository=correlation_repository,
        risk_engine=RiskEngine(
            policy=RiskPolicy(),
            providers=providers,
        ),
        risk_repository=risk_repository,
        alert_engine=AlertEngine(
            policy=AlertPolicy(),
        ),
        alert_repository=alert_repository,
    )

    return (
        service,
        detection_repository,
        correlation_repository,
        risk_repository,
        alert_repository,
    )


def test_no_findings_do_no_work():
    (
        service,
        detection_repository,
        correlation_repository,
        risk_repository,
        alert_repository,
    ) = make_service()

    result = service.process(())

    assert result.correlations_created == 0
    assert result.assessments_created == 0
    assert result.alerts_created == 0
    detection_repository.find_recent_findings.assert_not_called()
    correlation_repository.insert_match.assert_not_called()
    risk_repository.insert_assessment.assert_not_called()
    alert_repository.insert_alert.assert_not_called()


def test_same_event_encoded_powershell_creates_correlation_risk_and_alert():
    now = datetime.now(timezone.utc)
    general = make_finding(
        finding_id="0b54437d-01be-4316-a94d-52fcf1d3f137",
        rule_id="TP-WIN-SYSMON-0001",
        event_time=now,
    )
    encoded = make_finding(
        finding_id="86d76e7c-38ef-40c1-8350-c1405e6f44e9",
        event_time=now,
    )
    (
        service,
        detection_repository,
        correlation_repository,
        risk_repository,
        alert_repository,
    ) = make_service()

    detection_repository.find_recent_findings.return_value = (
        general,
        encoded,
    )

    result = service.process((encoded,))

    assert result.correlations_created == 1
    assert result.assessments_created == 1
    assert result.alerts_created == 1
    match = correlation_repository.insert_match.call_args.args[0]
    assessment = risk_repository.insert_assessment.call_args.args[0]
    alert = alert_repository.insert_alert.call_args.args[0]
    assert match.rule_id == "TP-CORR-WIN-0001"
    assert assessment.score == 40
    assert alert.risk_score == 40


def test_two_encoded_findings_within_window_create_temporal_alert():
    now = datetime.now(timezone.utc)
    historical = make_finding(
        finding_id="0b54437d-01be-4316-a94d-52fcf1d3f137",
        event_time=now - timedelta(minutes=5),
        event_record_id=41,
    )
    current = make_finding(
        finding_id="86d76e7c-38ef-40c1-8350-c1405e6f44e9",
        event_time=now,
        event_record_id=42,
    )
    (
        service,
        detection_repository,
        correlation_repository,
        risk_repository,
        alert_repository,
    ) = make_service()

    detection_repository.find_recent_findings.return_value = (
        historical,
        current,
    )

    result = service.process((current,))

    match = correlation_repository.insert_match.call_args.args[0]
    assessment = risk_repository.insert_assessment.call_args.args[0]
    alert = alert_repository.insert_alert.call_args.args[0]
    assert result.correlations_created == 1
    assert match.rule_id == "TP-CORR-WIN-0002"
    assert assessment.score == 80
    assert assessment.level is RiskLevel.CRITICAL
    assert alert.risk_score == 80
    assert alert.risk_level is RiskLevel.CRITICAL


def test_findings_outside_window_do_not_correlate():
    now = datetime.now(timezone.utc)
    historical = make_finding(
        finding_id="0b54437d-01be-4316-a94d-52fcf1d3f137",
        event_time=now - timedelta(minutes=11),
        event_record_id=41,
    )
    current = make_finding(
        finding_id="86d76e7c-38ef-40c1-8350-c1405e6f44e9",
        event_time=now,
        event_record_id=42,
    )
    (
        service,
        detection_repository,
        correlation_repository,
        risk_repository,
        alert_repository,
    ) = make_service()

    detection_repository.find_recent_findings.return_value = (
        historical,
        current,
    )

    result = service.process((current,))

    assert result.correlations_created == 0
    correlation_repository.insert_match.assert_not_called()
    risk_repository.insert_assessment.assert_not_called()
    alert_repository.insert_alert.assert_not_called()


def test_findings_on_another_host_are_ignored():
    now = datetime.now(timezone.utc)
    other_host = make_finding(
        finding_id="0b54437d-01be-4316-a94d-52fcf1d3f137",
        event_time=now,
        source_host="HOST-02",
    )
    current = make_finding(
        finding_id="86d76e7c-38ef-40c1-8350-c1405e6f44e9",
        event_time=now,
    )
    (
        service,
        detection_repository,
        correlation_repository,
        _risk_repository,
        _alert_repository,
    ) = make_service()

    detection_repository.find_recent_findings.return_value = (
        other_host,
        current,
    )

    result = service.process((current,))

    assert result.correlations_created == 0
    correlation_repository.insert_match.assert_not_called()


def test_duplicate_correlation_does_not_create_risk_or_alert():
    now = datetime.now(timezone.utc)
    historical = make_finding(
        finding_id="0b54437d-01be-4316-a94d-52fcf1d3f137",
        event_time=now - timedelta(minutes=5),
        event_record_id=41,
    )
    current = make_finding(
        finding_id="86d76e7c-38ef-40c1-8350-c1405e6f44e9",
        event_time=now,
        event_record_id=42,
    )
    (
        service,
        detection_repository,
        correlation_repository,
        risk_repository,
        alert_repository,
    ) = make_service()

    detection_repository.find_recent_findings.return_value = (
        historical,
        current,
    )
    correlation_repository.insert_match.return_value = False

    result = service.process((current,))

    assert result.correlations_created == 0
    risk_repository.insert_assessment.assert_not_called()
    alert_repository.insert_alert.assert_not_called()


def test_low_risk_assessment_persists_without_alert():
    now = datetime.now(timezone.utc)
    low_rule = CorrelationRule(
        rule_id="TP-CORR-LOW-0001",
        version=1,
        name="Low Risk Test Correlation",
        description="Test low-risk correlation.",
        severity=DetectionSeverity.LOW,
        mode=CorrelationMode.TEMPORAL_COUNT,
        required_detection_rule_ids=("TP-WIN-SYSMON-0002",),
        group_by=("source_host",),
        window_seconds=600,
        minimum_matches=2,
        explanation="Low risk test.",
    )
    historical = make_finding(
        finding_id="0b54437d-01be-4316-a94d-52fcf1d3f137",
        event_time=now - timedelta(minutes=5),
        event_record_id=41,
    )
    current = make_finding(
        finding_id="86d76e7c-38ef-40c1-8350-c1405e6f44e9",
        event_time=now,
        event_record_id=42,
    )
    (
        service,
        detection_repository,
        _correlation_repository,
        risk_repository,
        alert_repository,
    ) = make_service(
        rules=(low_rule,),
        providers=(),
    )

    detection_repository.find_recent_findings.return_value = (
        historical,
        current,
    )

    result = service.process((current,))

    assert result.correlations_created == 1
    assert result.assessments_created == 1
    assert result.alerts_created == 0
    assessment = risk_repository.insert_assessment.call_args.args[0]
    assert assessment.score == 25
    alert_repository.insert_alert.assert_not_called()


def test_correlation_must_include_new_finding():
    now = datetime.now(timezone.utc)
    old_one = make_finding(
        finding_id="0b54437d-01be-4316-a94d-52fcf1d3f137",
        event_time=now - timedelta(minutes=5),
        event_record_id=41,
    )
    old_two = make_finding(
        finding_id="86d76e7c-38ef-40c1-8350-c1405e6f44e9",
        event_time=now - timedelta(minutes=4),
        event_record_id=42,
    )
    current = make_finding(
        finding_id="83f27e87-397c-4012-bdf0-d9ebdbe2a52d",
        event_time=now,
        event_record_id=43,
    )
    (
        service,
        detection_repository,
        correlation_repository,
        risk_repository,
        alert_repository,
    ) = make_service()

    detection_repository.find_recent_findings.return_value = (
        old_one,
        old_two,
    )

    result = service.process((current,))

    assert result.correlations_created == 0
    correlation_repository.insert_match.assert_not_called()
    risk_repository.insert_assessment.assert_not_called()
    alert_repository.insert_alert.assert_not_called()


def test_replayed_same_event_does_not_create_repeated_activity():
    now = datetime.now(timezone.utc)
    first = make_finding(
        finding_id="0b54437d-01be-4316-a94d-52fcf1d3f137",
        event_time=now,
        event_record_id=100,
    )
    replay = make_finding(
        finding_id="86d76e7c-38ef-40c1-8350-c1405e6f44e9",
        event_time=now,
        event_record_id=100,
    )
    (
        service,
        detection_repository,
        correlation_repository,
        risk_repository,
        alert_repository,
    ) = make_service()

    detection_repository.find_recent_findings.return_value = (
        first,
        replay,
    )

    result = service.process((replay,))

    assert result.correlations_created == 0
    correlation_repository.insert_match.assert_not_called()
    risk_repository.insert_assessment.assert_not_called()
    alert_repository.insert_alert.assert_not_called()
