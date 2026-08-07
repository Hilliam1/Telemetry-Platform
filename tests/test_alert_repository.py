import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

from app.alerts.models import Alert, AlertStatus
from app.alerts.repository import AlertRepository
from app.risk.models import RiskLevel


def make_repository():
    conn = Mock()
    cursor = Mock()
    cursor_context = MagicMock()

    cursor_context.__enter__.return_value = cursor
    cursor_context.__exit__.return_value = False
    conn.cursor.return_value = cursor_context

    return AlertRepository(conn), conn, cursor


def make_alert() -> Alert:
    now = datetime.now(timezone.utc)

    return Alert(
        alert_id="91823c91-b17a-48c3-bc96-3bc88766f839",
        assessment_id="8b597820-0266-4493-a86f-a06f4a023fdf",
        correlation_id="3f76fcd5-4c78-4fa1-bf42-f49dddc15b72",
        correlation_rule_id="TP-CORR-WIN-0002",
        title="Critical Risk Activity on HOST-01",
        risk_score=80,
        risk_level=RiskLevel.CRITICAL,
        status=AlertStatus.NEW,
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        created_at=now,
        summary="Risk assessment produced score 80/100.",
        evidence={
            "base_score": 65,
            "risk_evidence": {
                "matched_finding_ids": (
                    "7de59353-d009-4ff1-b3ef-10c8d1585647",
                    "78d21297-731e-4265-abf3-4dd3fb0560c1",
                ),
            },
        },
    )


def test_insert_alert_executes_insert():
    repository, conn, cursor = make_repository()

    repository.insert_alert(make_alert())

    cursor.execute.assert_called_once()
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_insert_alert_serializes_fields():
    repository, _, cursor = make_repository()
    alert = make_alert()

    repository.insert_alert(alert)

    parameters = cursor.execute.call_args.args[1]

    assert parameters[0] == alert.alert_id
    assert parameters[1] == alert.assessment_id
    assert parameters[2] == alert.correlation_id
    assert parameters[6] == "critical"
    assert parameters[7] == "new"
    assert json.loads(parameters[13]) == {
        "base_score": 65,
        "risk_evidence": {
            "matched_finding_ids": [
                "7de59353-d009-4ff1-b3ef-10c8d1585647",
                "78d21297-731e-4265-abf3-4dd3fb0560c1",
            ],
        },
    }


def test_repository_does_not_own_transaction():
    repository, conn, _ = make_repository()

    repository.insert_alert(make_alert())

    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()
