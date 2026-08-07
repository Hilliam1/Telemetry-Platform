import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

from app.correlation.models import CorrelationMatch
from app.correlation.repository import CorrelationRepository
from app.detection.models import DetectionSeverity


def make_repository():
    conn = Mock()
    cursor = Mock()
    cursor_context = MagicMock()

    cursor_context.__enter__.return_value = cursor
    cursor_context.__exit__.return_value = False
    conn.cursor.return_value = cursor_context

    return CorrelationRepository(conn), conn, cursor


def make_match() -> CorrelationMatch:
    now = datetime.now(timezone.utc)

    return CorrelationMatch(
        correlation_id="3f76fcd5-4c78-4fa1-bf42-f49dddc15b72",
        rule_id="TP-CORR-WIN-0002",
        rule_version=1,
        title="Repeated Encoded PowerShell Activity",
        severity=DetectionSeverity.HIGH,
        source_host="HOST-01",
        first_event_time=now,
        last_event_time=now,
        matched_finding_ids=(
            "7de59353-d009-4ff1-b3ef-10c8d1585647",
            "78d21297-731e-4265-abf3-4dd3fb0560c1",
        ),
        matched_detection_rule_ids=(
            "TP-WIN-SYSMON-0002",
            "TP-WIN-SYSMON-0002",
        ),
        explanation="Repeated encoded PowerShell was detected.",
        investigation_steps=("Compare encoded payloads.",),
        evidence={
            "group_key": ("HOST-01",),
            "nested": {
                "count": 2,
            },
        },
        tags=("powershell", "repeated_activity"),
    )


def test_insert_match_executes_insert():
    repository, conn, cursor = make_repository()

    cursor.fetchone.return_value = (1,)

    inserted = repository.insert_match(make_match())

    assert inserted
    cursor.execute.assert_called_once()
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_insert_match_serializes_fields():
    repository, _, cursor = make_repository()
    match = make_match()
    cursor.fetchone.return_value = (1,)

    repository.insert_match(match)

    parameters = cursor.execute.call_args.args[1]

    assert parameters[0] == match.correlation_id
    assert len(parameters[1]) == 64
    assert parameters[5] == "high"
    assert parameters[9] == list(match.matched_finding_ids)
    assert parameters[10] == list(
        match.matched_detection_rule_ids
    )
    assert json.loads(parameters[12]) == [
        "Compare encoded payloads."
    ]
    assert json.loads(parameters[13]) == {
        "group_key": ["HOST-01"],
        "nested": {
            "count": 2,
        },
    }
    assert parameters[14] == [
        "powershell",
        "repeated_activity",
    ]


def test_repository_does_not_own_transaction():
    repository, conn, _ = make_repository()
    conn.cursor.return_value.__enter__.return_value.fetchone.return_value = (
        1,
    )

    repository.insert_match(make_match())

    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_insert_match_returns_false_for_duplicate_key():
    repository, _, cursor = make_repository()
    cursor.fetchone.return_value = None

    inserted = repository.insert_match(make_match())

    assert not inserted
