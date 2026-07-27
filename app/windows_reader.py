"""Windows Event Log query and rendering support."""

from __future__ import annotations

from typing import Any

import pywintypes
import win32evtlog


ERROR_NO_MORE_ITEMS = 259
DEFAULT_NATIVE_BATCH_SIZE = 25


class WindowsEventReader:
    """Read rendered XML events from Windows Event Log channels."""

    def __init__(
        self,
        batch_size: int,
        native_batch_size: int = DEFAULT_NATIVE_BATCH_SIZE,
    ) -> None:
        if batch_size <= 0:
            raise ValueError("batch_size must be greater than zero")

        if native_batch_size <= 0:
            raise ValueError(
                "native_batch_size must be greater than zero"
            )

        self.batch_size = batch_size
        self.native_batch_size = native_batch_size

    def read_channel(
        self,
        channel: str,
        last_record_id: int = 0,
    ) -> list[str]:
        """Return rendered XML events newer than the checkpoint."""

        if last_record_id < 0:
            raise ValueError("last_record_id cannot be negative")

        query = self._build_query(last_record_id)

        query_handle = win32evtlog.EvtQuery(
            channel,
            win32evtlog.EvtQueryChannelPath,
            query,
        )

        try:
            event_handles = self._read_handles(query_handle)

            return [
                win32evtlog.EvtRender(
                    event_handle,
                    win32evtlog.EvtRenderEventXml,
                )
                for event_handle in event_handles
            ]
        finally:
            query_handle.Close()

    def _read_handles(self, query_handle: Any) -> list[Any]:
        events: list[Any] = []

        while len(events) < self.batch_size:
            requested = min(
                self.native_batch_size,
                self.batch_size - len(events),
            )

            try:
                batch = win32evtlog.EvtNext(
                    query_handle,
                    requested,
                )
            except pywintypes.error as exc:
                if exc.winerror == ERROR_NO_MORE_ITEMS:
                    break
                raise

            if not batch:
                break

            events.extend(batch)

        return events

    @staticmethod
    def _build_query(last_record_id: int) -> str:
        if last_record_id == 0:
            return "*"

        return (
            "*[System[EventRecordID > "
            f"{last_record_id}"
            "]]"
        )
