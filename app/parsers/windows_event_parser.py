from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
import xml.etree.ElementTree as ET


EVENT_NAMESPACE = {
    "e": "http://schemas.microsoft.com/win/2004/08/events/event"
}

LEVELS = {
    "0": "LogAlways",
    "1": "Critical",
    "2": "Error",
    "3": "Warning",
    "4": "Information",
    "5": "Verbose",
}


class WindowsEventParser:
    def __init__(self, default_computer: str) -> None:
        self.default_computer = default_computer

    def parse(self, event_xml: str) -> dict[str, Any]:
        root = ET.fromstring(event_xml)

        system = root.find("e:System", EVENT_NAMESPACE)
        event_data = root.find("e:EventData", EVENT_NAMESPACE)
        user_data = root.find("e:UserData", EVENT_NAMESPACE)

        provider = (
            system.find("e:Provider", EVENT_NAMESPACE).attrib.get("Name", "")
            if system is not None
            and system.find("e:Provider", EVENT_NAMESPACE) is not None
            else ""
        )

        event_id = self._node_text(
            system,
            "EventID",
            default="0",
        )
        record_id = self._node_text(
            system,
            "EventRecordID",
            default="0",
        )
        level = self._node_text(
            system,
            "Level",
            default="4",
        )
        computer = self._node_text(
            system,
            "Computer",
            default=self.default_computer,
        )

        time_node = (
            system.find("e:TimeCreated", EVENT_NAMESPACE)
            if system is not None
            else None
        )
        created = (
            time_node.attrib.get("SystemTime")
            if time_node is not None
            else None
        )

        data = self._event_data_to_dict(event_data)
        user = (
            self._element_to_dict(user_data)
            if user_data is not None
            else {}
        )

        return {
            "provider": provider,
            "event_id": int(event_id),
            "record_id": int(record_id),
            "severity": LEVELS.get(level, level),
            "time_created": self._parse_windows_time(created),
            "computer": computer,
            "message": self._build_message(data, user),
            "raw": {
                "provider": provider,
                "event_id": int(event_id),
                "record_id": int(record_id),
                "level": level,
                "computer": computer,
                "event_data": data,
                "user_data": user,
            },
        }

    @staticmethod
    def _node_text(
        parent: ET.Element | None,
        tag: str,
        default: str = "",
    ) -> str:
        if parent is None:
            return default

        node = parent.find(f"e:{tag}", EVENT_NAMESPACE)

        if node is None or node.text is None:
            return default

        return node.text

    @staticmethod
    def _event_data_to_dict(
        event_data: ET.Element | None,
    ) -> dict[str, str]:
        if event_data is None:
            return {}

        values: dict[str, str] = {}

        for index, node in enumerate(
            event_data.findall("e:Data", EVENT_NAMESPACE)
        ):
            name = node.attrib.get("Name", f"Data{index}")
            values[name] = node.text or ""

        return values

    def _element_to_dict(
        self,
        element: ET.Element,
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}

        for child in list(element):
            tag = child.tag.split("}", 1)[-1]

            if list(child):
                result[tag] = self._element_to_dict(child)
            else:
                result[tag] = child.text or ""

        return result

    @staticmethod
    def _build_message(
        event_data: dict[str, Any],
        user_data: dict[str, Any],
    ) -> str:
        data = event_data or user_data

        if not data:
            return ""

        return " ".join(
            f"{key}={value}"
            for key, value in data.items()
        )

    @staticmethod
    def _parse_windows_time(
        value: str | None,
    ) -> datetime:
        if not value:
            return datetime.now(timezone.utc)

        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )