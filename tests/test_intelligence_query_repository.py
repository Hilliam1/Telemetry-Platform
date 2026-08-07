from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock
from uuid import UUID

from app.intelligence.query_repository import (
    IntelligenceQueryRepository,
)


def make_repository():
    conn = Mock()
    cursor = Mock()
    cursor_context = MagicMock()

    cursor_context.__enter__.return_value = cursor
    cursor_context.__exit__.return_value = False
    conn.cursor.return_value = cursor_context

    return IntelligenceQueryRepository(conn), conn, cursor


def test_list_detections_uses_parameterized_filters():
    repository, conn, cursor = make_repository()
    now = datetime.now(timezone.utc)
    cursor.fetchall.return_value = [
        (
            UUID("7de59353-d009-4ff1-b3ef-10c8d1585647"),
            "TP-WIN-SYSMON-0002",
            1,
            "Encoded PowerShell Command",
            "medium",
            "HOST-01",
            "sysmon",
            1,
            42,
            now,
            now,
            "Encoded PowerShell was detected.",
            ["Decode the command."],
            {"command_line": "powershell.exe -enc SQBFAFgA"},
            ["powershell", "encoded_command"],
        )
    ]

    result = repository.list_detections(
        source_host="HOST-01",
        severity="medium",
        limit=25,
    )

    query, parameters = cursor.execute.call_args.args

    assert "FROM detection_findings" in query
    assert "source_host = %s" in query
    assert "severity = %s" in query
    assert "HOST-01" not in query
    assert parameters == ("HOST-01", "medium", 25)
    assert result[0]["finding_uuid"] == UUID(
        "7de59353-d009-4ff1-b3ef-10c8d1585647"
    )
    assert result[0]["investigation_steps"] == [
        "Decode the command."
    ]
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_list_detections_selects_response_columns():
    repository, _, cursor = make_repository()
    cursor.fetchall.return_value = []

    repository.list_detections(limit=100)

    query = cursor.execute.call_args.args[0]

    for column in (
        "finding_uuid",
        "rule_id",
        "rule_version",
        "title",
        "severity",
        "source_host",
        "source_type",
        "event_id",
        "event_record_id",
        "event_time",
        "evaluated_at",
        "explanation",
        "investigation_steps",
        "evidence",
        "tags",
    ):
        assert column in query


def test_list_correlations_casts_finding_ids_for_api_serialization():
    repository, _, cursor = make_repository()
    cursor.fetchall.return_value = []

    repository.list_correlations(limit=100)

    query = cursor.execute.call_args.args[0]

    assert "matched_finding_ids::text[]" in query


def test_list_correlations_filters_by_host_and_severity():
    repository, conn, cursor = make_repository()
    now = datetime.now(timezone.utc)
    cursor.fetchall.return_value = [
        (
            UUID("3f76fcd5-4c78-4fa1-bf42-f49dddc15b72"),
            "TP-CORR-WIN-0002",
            1,
            "Repeated Encoded PowerShell Activity",
            "high",
            "HOST-01",
            now,
            now,
            [
                UUID("7de59353-d009-4ff1-b3ef-10c8d1585647"),
            ],
            ["TP-WIN-SYSMON-0002"],
            "Repeated encoded PowerShell was detected.",
            ["Compare encoded payloads."],
            {"count": 2},
            ["powershell"],
        )
    ]

    result = repository.list_correlations(
        source_host="HOST-01",
        severity="high",
        limit=50,
    )

    query, parameters = cursor.execute.call_args.args

    assert "FROM correlation_matches" in query
    assert "source_host = %s" in query
    assert "severity = %s" in query
    assert parameters == ("HOST-01", "high", 50)
    assert result[0]["rule_id"] == "TP-CORR-WIN-0002"
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_list_risk_assessments_filters_by_minimum_score():
    repository, conn, cursor = make_repository()
    now = datetime.now(timezone.utc)
    cursor.fetchall.return_value = [
        (
            UUID("8b597820-0266-4493-a86f-a06f4a023fdf"),
            UUID("3f76fcd5-4c78-4fa1-bf42-f49dddc15b72"),
            "TP-CORR-WIN-0002",
            80,
            "critical",
            65,
            [{"provider": "repeated_activity"}],
            "HOST-01",
            now,
            now,
            now,
            "Risk score 80.",
            {"base_score": 65},
        )
    ]

    result = repository.list_risk_assessments(
        source_host="HOST-01",
        level="critical",
        minimum_score=60,
        limit=10,
    )

    query, parameters = cursor.execute.call_args.args

    assert "FROM risk_assessments" in query
    assert "score >= %s" in query
    assert parameters == ("HOST-01", "critical", 60, 10)
    assert result[0]["score"] == 80
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_list_alerts_filters_by_status_and_risk_level():
    repository, conn, cursor = make_repository()
    now = datetime.now(timezone.utc)
    alert_id = UUID("91823c91-b17a-48c3-bc96-3bc88766f839")
    cursor.fetchall.return_value = [
        (
            alert_id,
            UUID("8b597820-0266-4493-a86f-a06f4a023fdf"),
            UUID("3f76fcd5-4c78-4fa1-bf42-f49dddc15b72"),
            "TP-CORR-WIN-0002",
            "Critical Risk Activity on HOST-01",
            80,
            "critical",
            "new",
            "HOST-01",
            now,
            now,
            now,
            "Risk assessment produced score 80/100.",
            {"risk_score": 80},
        )
    ]

    result = repository.list_alerts(
        source_host="HOST-01",
        status="new",
        risk_level="critical",
        minimum_score=60,
        limit=10,
    )

    query, parameters = cursor.execute.call_args.args

    assert "FROM alerts" in query
    assert "status = %s" in query
    assert "risk_level = %s" in query
    assert "risk_score >= %s" in query
    assert parameters == (
        "HOST-01",
        "new",
        "critical",
        60,
        10,
    )
    assert result[0]["alert_uuid"] == alert_id
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_get_alert_returns_one_alert():
    repository, conn, cursor = make_repository()
    now = datetime.now(timezone.utc)
    alert_id = UUID("91823c91-b17a-48c3-bc96-3bc88766f839")
    cursor.fetchone.return_value = (
        alert_id,
        UUID("8b597820-0266-4493-a86f-a06f4a023fdf"),
        UUID("3f76fcd5-4c78-4fa1-bf42-f49dddc15b72"),
        "TP-CORR-WIN-0002",
        "Critical Risk Activity on HOST-01",
        80,
        "critical",
        "new",
        "HOST-01",
        now,
        now,
        now,
        "Risk assessment produced score 80/100.",
        {"risk_score": 80},
    )

    result = repository.get_alert(alert_id)

    query, parameters = cursor.execute.call_args.args

    assert "WHERE alert_uuid = %s" in query
    assert parameters == (alert_id,)
    assert result is not None
    assert result["alert_uuid"] == alert_id
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_get_alert_returns_none_when_missing():
    repository, _, cursor = make_repository()
    alert_id = UUID("91823c91-b17a-48c3-bc96-3bc88766f839")
    cursor.fetchone.return_value = None

    result = repository.get_alert(alert_id)

    assert result is None
