import json
from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

from app.detection.models import (
    DetectionFinding,
    DetectionSeverity,
)
from app.detection.repository import DetectionRepository


def make_repository():
    conn = Mock()
    cursor = Mock()
    cursor_context = MagicMock()

    cursor_context.__enter__.return_value = cursor
    cursor_context.__exit__.return_value = False
    conn.cursor.return_value = cursor_context

    return DetectionRepository(conn), conn, cursor


def make_finding() -> DetectionFinding:
    now = datetime.now(timezone.utc)

    return DetectionFinding(
        finding_id="8d0ea328-ef8d-4bca-a56e-313ef8c8a870",
        rule_id="TP-WIN-SYSMON-0002",
        rule_version=1,
        title="Encoded PowerShell Command",
        severity=DetectionSeverity.MEDIUM,
        source_host="HOST-01",
        source_type="sysmon",
        event_id=1,
        event_record_id=42,
        event_time=now,
        evaluated_at=now,
        explanation="Encoded PowerShell was detected.",
        investigation_steps=("Decode the command.",),
        evidence={
            "raw.event_data.CommandLine":
                "powershell.exe -enc SQBFAFgA"
        },
        tags=("powershell", "encoded_command"),
    )


def test_insert_finding_executes_insert():
    repository, conn, cursor = make_repository()

    repository.insert_finding(make_finding())

    cursor.execute.assert_called_once()
    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()


def test_insert_finding_serializes_structured_fields():
    repository, _, cursor = make_repository()

    finding = make_finding()
    repository.insert_finding(finding)

    parameters = cursor.execute.call_args.args[1]

    assert json.loads(parameters[12]) == [
        "Decode the command."
    ]
    assert json.loads(parameters[13]) == {
        "raw.event_data.CommandLine":
            "powershell.exe -enc SQBFAFgA"
    }
    assert parameters[14] == [
        "powershell",
        "encoded_command",
    ]


def test_insert_findings_returns_count():
    repository, _, cursor = make_repository()
    finding = make_finding()

    count = repository.insert_findings(
        (finding, finding)
    )

    assert count == 2
    assert cursor.execute.call_count == 2
