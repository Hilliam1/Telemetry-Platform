from datetime import datetime, timezone
from unittest.mock import MagicMock, Mock

from app.repository import TelemetryRepository


def make_repository():
    conn = Mock()
    cursor = Mock()
    cursor_context = MagicMock()

    cursor_context.__enter__.return_value = cursor
    cursor_context.__exit__.return_value = False
    conn.cursor.return_value = cursor_context

    return TelemetryRepository(conn), conn, cursor


def test_insert_log_event_executes_insert():
    repository, conn, cursor = make_repository()

    repository.insert_log_event(
        source_host="HOST-01",
        source_type="sysmon",
        provider_name="Microsoft-Windows-Sysmon",
        event_id=1,
        event_record_id=42,
        severity="Information",
        time_created=datetime.now(timezone.utc),
        message="test",
        raw_data="{}",
    )

    cursor.execute.assert_called_once()
    conn.commit.assert_not_called()


def test_non_sysmon_event_does_not_insert_process():
    repository, _, cursor = make_repository()

    inserted = repository.insert_process_event(
        {
            "source_type": "windows_system",
            "event_id": 1,
        }
    )

    assert inserted is False
    cursor.execute.assert_not_called()


def test_sysmon_process_event_is_inserted():
    repository, conn, cursor = make_repository()

    inserted = repository.insert_process_event(
        {
            "source_type": "sysmon",
            "event_id": 1,
            "computer": "HOST-01",
            "time_created": datetime.now(timezone.utc),
            "raw": {
                "event_data": {
                    "ProcessGuid": "{guid}",
                    "ProcessId": "1234",
                    "Image": "powershell.exe",
                    "CommandLine": "powershell.exe",
                    "ParentImage": "explorer.exe",
                    "ParentCommandLine": "explorer.exe",
                    "User": "DOMAIN\\user",
                    "Hashes": "MD5=abc,SHA256=def123",
                }
            },
        }
    )

    assert inserted is True
    cursor.execute.assert_called_once()
    conn.commit.assert_not_called()


def test_extract_sha256_is_case_insensitive():
    result = TelemetryRepository._extract_sha256("MD5=abc, sha256=def123")

    assert result == "def123"


def test_repository_does_not_own_transactions():
    repository, conn, _ = make_repository()

    repository.insert_host_metrics(
        {
            "host": "HOST-01",
            "cpu_percent": 10.0,
            "memory_percent": 50.0,
            "disk_percent": 60.0,
            "boot_time": datetime.now(timezone.utc),
        }
    )

    conn.commit.assert_not_called()
    conn.rollback.assert_not_called()
