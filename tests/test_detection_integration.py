from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

from app.detection.engine import DetectionEngine
from app.detection.repository import DetectionRepository
from app.detection.rules import BUILTIN_RULES


def test_encoded_powershell_event_reaches_repository():
    event = {
        "computer": "HOST-01",
        "source_type": "sysmon",
        "event_id": 1,
        "record_id": 100,
        "time_created": datetime.now(timezone.utc),
        "raw": {
            "event_data": {
                "Image": (
                    r"C:\Windows\System32"
                    r"\WindowsPowerShell\v1.0"
                    r"\powershell.exe"
                ),
                "CommandLine": (
                    "powershell.exe "
                    "-EncodedCommand SQBFAFgA"
                ),
            }
        },
    }

    engine = DetectionEngine(BUILTIN_RULES)
    findings = engine.evaluate(event)

    conn = Mock()
    cursor = Mock()
    cursor_context = MagicMock()
    cursor_context.__enter__.return_value = cursor
    conn.cursor.return_value = cursor_context

    repository = DetectionRepository(conn)
    count = repository.insert_findings(findings)

    assert count == 2
    assert cursor.execute.call_count == 2
    conn.commit.assert_not_called()
