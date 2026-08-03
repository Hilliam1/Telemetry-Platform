from datetime import datetime
from unittest.mock import Mock, patch

from app.health_metrics import HostMetricsCollector


def test_uses_supplied_hostname_and_drive():
    collector = HostMetricsCollector(
        hostname="FINANCE-01",
        system_drive="D:",
    )

    assert collector.hostname == "FINANCE-01"
    assert collector._disk_root() == "D:\\"


@patch("app.health_metrics.psutil")
def test_collects_health_metrics(mock_psutil):
    mock_psutil.cpu_percent.return_value = 12.5

    memory = Mock()
    memory.percent = 68.4
    mock_psutil.virtual_memory.return_value = memory

    disk = Mock()
    disk.percent = 74.2
    mock_psutil.disk_usage.return_value = disk

    mock_psutil.boot_time.return_value = 1_700_000_000

    collector = HostMetricsCollector(
        hostname="FINANCE-01",
        system_drive="C:",
    )

    metrics = collector.collect()

    assert metrics["host"] == "FINANCE-01"
    assert metrics["psutil_available"] is True
    assert metrics["cpu_percent"] == 12.5
    assert metrics["memory_percent"] == 68.4
    assert metrics["disk_percent"] == 74.2

    assert datetime.fromisoformat(
        metrics["collector_time"]
    ).tzinfo is not None

    assert datetime.fromisoformat(
        metrics["boot_time"]
    ).tzinfo is not None

    mock_psutil.cpu_percent.assert_called_once_with(
        interval=0.1
    )
    mock_psutil.virtual_memory.assert_called_once_with()
    mock_psutil.disk_usage.assert_called_once_with(
        "C:\\"
    )
    mock_psutil.boot_time.assert_called_once_with()


@patch("app.health_metrics.psutil", None)
def test_returns_availability_status_without_psutil():
    collector = HostMetricsCollector(
        hostname="FINANCE-01"
    )

    metrics = collector.collect()

    assert metrics["host"] == "FINANCE-01"
    assert metrics["psutil_available"] is False
    assert "cpu_percent" not in metrics
    assert "memory_percent" not in metrics
    assert "disk_percent" not in metrics
    assert "boot_time" not in metrics


def test_normalizes_drive_with_trailing_slash():
    collector = HostMetricsCollector(
        hostname="FINANCE-01",
        system_drive="C:\\",
    )

    assert collector._disk_root() == "C:\\"