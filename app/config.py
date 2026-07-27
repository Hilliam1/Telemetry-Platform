"""Application configuration loaded from environment variables."""

from dataclasses import dataclass
import os
from pathlib import Path


@dataclass(frozen=True)
class DatabaseSettings:
    host: str
    database: str
    user: str
    password: str
    port: int


@dataclass(frozen=True)
class CollectorSettings:
    state_file: Path
    poll_seconds: int
    batch_size: int
    enabled_sources: tuple[str, ...] | None


DEFAULT_SOURCES = (
    "windows_system",
    "windows_application",
    "windows_security",
    "sysmon",
    "powershell",
    "defender",
    "task_scheduler",
    "health_metrics",
)


def load_database_settings() -> DatabaseSettings:
    return DatabaseSettings(
        host=os.getenv("PGHOST", "localhost"),
        database=os.getenv("PGDATABASE", "sysmon_lab"),
        user=os.getenv("PGUSER", "postgres"),
        password=os.getenv("PGPASSWORD", ""),
        port=int(os.getenv("PGPORT", "5432")),
    )


def load_collector_settings() -> CollectorSettings:
    raw_sources = os.getenv("COLLECTOR_SOURCES")

    enabled_sources = None
    if raw_sources:
        enabled_sources = tuple(
            source.strip()
            for source in raw_sources.split(",")
            if source.strip()
        )

    return CollectorSettings(
        state_file=Path(
            os.getenv("COLLECTOR_STATE_FILE", "collector_state.json")
        ),
        poll_seconds=int(os.getenv("COLLECTOR_POLL_SECONDS", "5")),
        batch_size=int(os.getenv("COLLECTOR_BATCH_SIZE", "100")),
        enabled_sources=enabled_sources,
    )