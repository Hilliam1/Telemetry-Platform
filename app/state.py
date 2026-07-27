"""Persistent checkpoint management for telemetry collectors."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any


LOG = logging.getLogger("telemetry_platform.state")


class CollectorState:
    """Track the latest processed EventRecordID for each event channel."""

    def __init__(self, state_file: Path) -> None:
        self.state_file = state_file
        self._values: dict[str, int] = self._load()

    def get_last_record_id(
        self,
        source_type: str,
        channel: str,
    ) -> int:
        """Return the latest checkpoint for a source and channel."""

        key = self._make_key(source_type, channel)
        return self._values.get(key, 0)

    def update_record_id(
        self,
        source_type: str,
        channel: str,
        record_id: int,
    ) -> None:
        """Advance a checkpoint without allowing it to move backward."""

        if record_id < 0:
            raise ValueError("record_id cannot be negative")

        key = self._make_key(source_type, channel)
        current_record_id = self._values.get(key, 0)

        if record_id > current_record_id:
            self._values[key] = record_id

    def save(self) -> None:
        """Persist checkpoints using an atomic file replacement."""

        self.state_file.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        temporary_file = self.state_file.with_name(
            f"{self.state_file.name}.tmp"
        )

        try:
            temporary_file.write_text(
                json.dumps(
                    self._values,
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            temporary_file.replace(self.state_file)

        except OSError:
            LOG.exception(
                "Unable to save collector state to %s.",
                self.state_file,
            )

            try:
                temporary_file.unlink(missing_ok=True)
            except OSError:
                LOG.warning(
                    "Unable to remove temporary state file %s.",
                    temporary_file,
                )

            raise

    def as_dict(self) -> dict[str, int]:
        """Return a copy of the current state."""

        return dict(self._values)

    def _load(self) -> dict[str, int]:
        if not self.state_file.exists():
            return {}

        try:
            raw_state: Any = json.loads(
                self.state_file.read_text(encoding="utf-8")
            )

        except json.JSONDecodeError:
            LOG.warning(
                "State file %s contains invalid JSON; starting empty.",
                self.state_file,
            )
            return {}

        except OSError:
            LOG.exception(
                "Unable to read collector state from %s.",
                self.state_file,
            )
            raise

        if not isinstance(raw_state, dict):
            LOG.warning(
                "State file %s does not contain a JSON object; starting empty.",
                self.state_file,
            )
            return {}

        validated_state: dict[str, int] = {}

        for key, value in raw_state.items():
            try:
                record_id = int(value)
            except (TypeError, ValueError):
                LOG.warning(
                    "Ignoring invalid state value for %s: %r",
                    key,
                    value,
                )
                continue

            if record_id < 0:
                LOG.warning(
                    "Ignoring negative state value for %s: %s",
                    key,
                    record_id,
                )
                continue

            validated_state[str(key)] = record_id

        return validated_state

    @staticmethod
    def _make_key(
        source_type: str,
        channel: str,
    ) -> str:
        return f"{source_type}:{channel}"