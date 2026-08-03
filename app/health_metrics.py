"""Local host-health metric collection."""

from __future__ import annotations

import os
import socket
from datetime import datetime, timezone
from typing import Any

try:
    import psutil
except ImportError:
    psutil = None


class HostMetricsCollector:
    """Collect CPU, memory, disk, and boot-time telemetry."""

    def __init__(
        self,
        hostname: str | None = None,
        system_drive: str | None = None,
    ) -> None:
        self.hostname = hostname or socket.gethostname()
        self.system_drive = (
            system_drive
            or os.getenv("SYSTEMDRIVE", "C:")
        )

    @property
    def available(self) -> bool:
        """Return whether psutil is available."""

        return psutil is not None

    def collect(self) -> dict[str, Any]:
        """Collect a host-health snapshot."""

        metrics: dict[str, Any] = {
            "collector_time": datetime.now(
                timezone.utc
            ).isoformat(),
            "host": self.hostname,
            "psutil_available": self.available,
        }

        if not self.available:
            return metrics

        disk = psutil.disk_usage(
            self._disk_root()
        )
        memory = psutil.virtual_memory()

        metrics.update(
            {
                "cpu_percent": psutil.cpu_percent(
                    interval=0.1
                ),
                "memory_percent": memory.percent,
                "disk_percent": disk.percent,
                "boot_time": datetime.fromtimestamp(
                    psutil.boot_time(),
                    timezone.utc,
                ).isoformat(),
            }
        )

        return metrics

    def _disk_root(self) -> str:
        """Return the Windows drive root used for disk metrics."""

        return self.system_drive.rstrip("\\") + "\\"