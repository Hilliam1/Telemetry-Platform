from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

from app.alerts.engine import AlertEngine
from app.alerts.models import AlertStatus
from app.alerts.policy import AlertPolicy
from app.alerts.repository import AlertRepository
from app.correlation.engine import CorrelationEngine
from app.correlation.repository import CorrelationRepository
from app.correlation.rules import BUILTIN_CORRELATION_RULES
from app.detection.models import DetectionFinding, DetectionSeverity
from app.risk.engine import RiskEngine
from app.risk.models import RiskLevel
from app.risk.policy import RiskPolicy
from app.risk.providers import RepeatedActivityRiskProvider
from app.risk.repository import RiskRepository


def make_encoded_powershell_finding(
    *,
    finding_id: str,
    event_time: datetime,
    event_record_id: int,
) -> DetectionFinding:
    return DetectionFinding(
        finding_id=finding_id,
        rule_id="TP-WIN-SYSMON-0002",
        rule_version=1,
        title="Encoded PowerShell Command",
        severity=DetectionSeverity.MEDIUM,
        source_host="HOST-01",
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


def test_intelligence_outputs_can_be_persisted_without_database():
    started_at = datetime.now(timezone.utc)
    findings = (
        make_encoded_powershell_finding(
            finding_id="7de59353-d009-4ff1-b3ef-10c8d1585647",
            event_time=started_at,
            event_record_id=42,
        ),
        make_encoded_powershell_finding(
            finding_id="78d21297-731e-4265-abf3-4dd3fb0560c1",
            event_time=started_at + timedelta(minutes=5),
            event_record_id=43,
        ),
    )

    correlations = CorrelationEngine(
        BUILTIN_CORRELATION_RULES
    ).evaluate(findings)

    repeated_correlation = next(
        correlation
        for correlation in correlations
        if correlation.rule_id == "TP-CORR-WIN-0002"
    )

    risk = RiskEngine(
        policy=RiskPolicy(),
        providers=(RepeatedActivityRiskProvider(),),
    ).assess(repeated_correlation)

    alert = AlertEngine(
        policy=AlertPolicy(),
    ).evaluate(risk)

    correlation_repository = Mock(spec=CorrelationRepository)
    risk_repository = Mock(spec=RiskRepository)
    alert_repository = Mock(spec=AlertRepository)

    correlation_repository.insert_match(repeated_correlation)
    risk_repository.insert_assessment(risk)
    alert_repository.insert_alert(alert)

    assert repeated_correlation.rule_id == "TP-CORR-WIN-0002"
    assert risk.score == 80
    assert risk.level is RiskLevel.CRITICAL
    assert alert is not None
    assert alert.status is AlertStatus.NEW
    assert alert.risk_level is RiskLevel.CRITICAL
    assert alert.correlation_id == repeated_correlation.correlation_id
    assert alert.assessment_id == risk.assessment_id
    correlation_repository.insert_match.assert_called_once_with(
        repeated_correlation
    )
    risk_repository.insert_assessment.assert_called_once_with(risk)
    alert_repository.insert_alert.assert_called_once_with(alert)
