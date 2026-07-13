import json
import logging
import os
import socket
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

import psycopg2
import pywintypes
import win32evtlog

try:
    import psutil
except ImportError:
    psutil = None


LOG = logging.getLogger("sysmon_collector")

STATE_FILE = Path(os.getenv("COLLECTOR_STATE_FILE", "collector_state.json"))
POLL_SECONDS = int(os.getenv("COLLECTOR_POLL_SECONDS", "5"))
BATCH_SIZE = int(os.getenv("COLLECTOR_BATCH_SIZE", "100"))

EVENT_CHANNELS = {
    "windows_system": ["System"],
    "windows_application": ["Application"],
    "windows_security": ["Security"],
    "sysmon": ["Microsoft-Windows-Sysmon/Operational"],
    "powershell": [
        "Windows PowerShell",
        "Microsoft-Windows-PowerShell/Operational",
    ],
    "defender": ["Microsoft-Windows-Windows Defender/Operational"],
    "task_scheduler": ["Microsoft-Windows-TaskScheduler/Operational"],
}

DEFAULT_SOURCES = [
    "windows_system",
    "windows_application",
    "windows_security",
    "sysmon",
    "powershell",
    "defender",
    "task_scheduler",
    "health_metrics",
]

LEVELS = {
    "0": "LogAlways",
    "1": "Critical",
    "2": "Error",
    "3": "Warning",
    "4": "Information",
    "5": "Verbose",
}


class Collector:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.state = self._load_state()
        self.conn = psycopg2.connect(
            host=os.getenv("PGHOST", "localhost"),
            database=os.getenv("PGDATABASE", "sysmon_lab"),
            user=os.getenv("PGUSER", "postgres"),
            password=os.getenv("PGPASSWORD", ""),
            port=int(os.getenv("PGPORT", "5432")),
        )

    def close(self):
        self.conn.close()

    def ingest_windows_system(self):
        return self._ingest_event_channels("windows_system")

    def ingest_windows_application(self):
        return self._ingest_event_channels("windows_application")

    def ingest_windows_security(self):
        return self._ingest_event_channels("windows_security")

    def ingest_sysmon(self):
        return self._ingest_event_channels("sysmon")

    def ingest_powershell(self):
        return self._ingest_event_channels("powershell")

    def ingest_defender(self):
        return self._ingest_event_channels("defender")

    def ingest_task_scheduler(self):
        return self._ingest_event_channels("task_scheduler")

    def ingest_health_metrics(self):
        metrics = self._collect_health_metrics()

        if not metrics.get("psutil_available"):
            return 0

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO host_metrics (
                    host_name,
                    cpu_percent,
                    memory_percent,
                    disk_percent,
                    boot_time
                )
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    metrics["host"],
                    metrics["cpu_percent"],
                    metrics["memory_percent"],
                    metrics["disk_percent"],
                    metrics["boot_time"],
                ),
            )

        self.conn.commit()
        return 1

    def run_forever(self):
        while True:
            total = self.run_once()
            LOG.info("Polling complete. Inserted %s events. Sleeping %s seconds.", total, POLL_SECONDS)
            time.sleep(POLL_SECONDS)

    def run_once(self):
        started_at = datetime.now(timezone.utc)
        total = 0
        status = "success"
        error_message = None

        try:
            for source in self._enabled_sources():
                total += getattr(self, f"ingest_{source}")()

        except Exception as exc:
            self.conn.rollback()
            status = "failed"
            error_message = str(exc)
            LOG.exception("Collector run failed.")

        self._insert_collector_run(
            status=status,
            events_inserted=total,
            started_at=started_at,
            error_message=error_message,
        )

        self.conn.commit()
        return total

    def _ingest_event_channels(self, source_type):
        inserted = 0
        for channel in EVENT_CHANNELS[source_type]:
            try:
                inserted += self._ingest_channel(source_type, channel)
            except pywintypes.error as exc:
                self.conn.rollback()
                if exc.winerror == 5:
                    LOG.warning(
                        "Access denied reading %s. Run elevated, add the collector account "
                        "to Event Log Readers, or remove %s from COLLECTOR_SOURCES.",
                        channel,
                        source_type,
                    )
                    continue
                LOG.exception("Failed to ingest channel %s", channel)
            except Exception:
                self.conn.rollback()
                LOG.exception("Failed to ingest channel %s", channel)
        return inserted

    def _enabled_sources(self):
        sources = os.getenv("COLLECTOR_SOURCES")
        if not sources:
            return DEFAULT_SOURCES
        return [source.strip() for source in sources.split(",") if source.strip()]

    def _ingest_channel(self, source_type, channel):
        state_key = f"{source_type}:{channel}"
        last_record_id = int(self.state.get(state_key, 0))
        query = f"*[System[EventRecordID > {last_record_id}]]" if last_record_id else "*"
        handle = win32evtlog.EvtQuery(
            channel,
            win32evtlog.EvtQueryChannelPath,
            query,
        )

        events = []
        while len(events) < BATCH_SIZE:
            try:
                batch = win32evtlog.EvtNext(handle, min(25, BATCH_SIZE - len(events)))
            except pywintypes.error as exc:
                if exc.winerror == 259:
                    break
                raise
            if not batch:
                break
            events.extend(batch)

        parsed_events = [
            self._parse_event_xml(win32evtlog.EvtRender(event, win32evtlog.EvtRenderEventXml))
            for event in events
        ]
        parsed_events.sort(key=lambda item: item["record_id"])

        inserted = 0
        for event in parsed_events:
            event["source_type"] = source_type
            self._insert_event(
                source_host=event["computer"] or self.hostname,
                source_type=source_type,
                provider_name=event["provider"],
                event_id=event["event_id"],
                event_record_id=event["record_id"],
                severity=event["severity"],
                time_created=event["time_created"],
                message=event["message"],
                raw_data=json.dumps(event["raw"], sort_keys=True),
            )
            self._insert_process_event(event)
            inserted += 1
            self.state[state_key] = max(int(self.state.get(state_key, 0)), event["record_id"])

        self.conn.commit()
        self._save_state()
        return inserted

    def _insert_process_event(self, event):
        raw = event["raw"]
        data = raw.get("event_data", {})

        if event["source_type"] != "sysmon":
            return

        if event["event_id"] != 1:
            return

        hashes = data.get("Hashes", "")
        sha256 = ""

        for item in hashes.split(","):
            if item.startswith("SHA256="):
                sha256 = item.replace("SHA256=", "")

        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO process_events (
                    source_host,
                    process_guid,
                    process_id,
                    image,
                    command_line,
                    parent_image,
                    parent_command_line,
                    user_name,
                    sha256,
                    created_at
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    event["computer"],
                    data.get("ProcessGuid", ""),
                    int(data.get("ProcessId", 0) or 0),
                    data.get("Image", ""),
                    data.get("CommandLine", ""),
                    data.get("ParentImage", ""),
                    data.get("ParentCommandLine", ""),
                    data.get("User", ""),
                    sha256,
                    event["time_created"],
                ),
            )

    def _insert_collector_run(
        self,
        status,
        events_inserted,
        started_at,
        error_message=None,
    ):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO collector_runs (
                    source_host,
                    status,
                    events_inserted,
                    started_at,
                    error_message
                )
                VALUES (%s,%s,%s,%s,%s)
                """,
                (
                    self.hostname,
                    status,
                    events_inserted,
                    started_at,
                    error_message,
                ),
            )

    def _insert_event(
        self,
        source_host,
        source_type,
        provider_name,
        event_id,
        event_record_id,
        severity,
        time_created,
        message,
        raw_data,
    ):
        with self.conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO log_events (
                    source_host,
                    source_type,
                    provider_name,
                    event_id,
                    event_record_id,
                    severity,
                    time_created,
                    message,
                    raw_data
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """,
                (
                    source_host,
                    source_type,
                    provider_name,
                    event_id,
                    event_record_id,
                    severity,
                    time_created,
                    message,
                    raw_data,
                ),
            )

    def _parse_event_xml(self, event_xml):
        root = ET.fromstring(event_xml)
        ns = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}
        system = root.find("e:System", ns)
        event_data = root.find("e:EventData", ns)
        user_data = root.find("e:UserData", ns)

        provider = system.find("e:Provider", ns).attrib.get("Name", "") if system is not None else ""
        event_id = self._node_text(system, "EventID", ns, "0")
        record_id = self._node_text(system, "EventRecordID", ns, "0")
        level = self._node_text(system, "Level", ns, "4")
        computer = self._node_text(system, "Computer", ns, self.hostname)
        time_node = system.find("e:TimeCreated", ns) if system is not None else None
        created = time_node.attrib.get("SystemTime") if time_node is not None else None
        data = self._event_data_to_dict(event_data, ns)
        user = self._element_to_dict(user_data) if user_data is not None else {}

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

    def _collect_health_metrics(self):
        metrics = {
            "collector_time": datetime.now(timezone.utc).isoformat(),
            "host": self.hostname,
        }
        if psutil is None:
            metrics["psutil_available"] = False
            return metrics

        disk = psutil.disk_usage(os.getenv("SYSTEMDRIVE", "C:") + "\\")
        metrics.update(
            {
                "psutil_available": True,
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_percent": disk.percent,
                "boot_time": datetime.fromtimestamp(psutil.boot_time(), timezone.utc).isoformat(),
            }
        )
        return metrics

    def _load_state(self):
        if not STATE_FILE.exists():
            return {}
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            LOG.warning("State file is invalid JSON; starting with empty state.")
            return {}

    def _save_state(self):
        STATE_FILE.write_text(json.dumps(self.state, indent=2, sort_keys=True), encoding="utf-8")

    def _node_text(self, parent, tag, ns, default=""):
        if parent is None:
            return default
        node = parent.find(f"e:{tag}", ns)
        return node.text if node is not None and node.text is not None else default

    def _event_data_to_dict(self, event_data, ns):
        if event_data is None:
            return {}
        values = {}
        for index, node in enumerate(event_data.findall("e:Data", ns)):
            name = node.attrib.get("Name", f"Data{index}")
            values[name] = node.text or ""
        return values

    def _element_to_dict(self, element):
        result = {}
        for child in list(element):
            tag = child.tag.split("}", 1)[-1]
            if list(child):
                result[tag] = self._element_to_dict(child)
            else:
                result[tag] = child.text or ""
        return result

    def _build_message(self, event_data, user_data):
        data = event_data or user_data
        if not data:
            return ""
        return " ".join(f"{key}={value}" for key, value in data.items())

    def _parse_windows_time(self, value):
        if not value:
            return datetime.now(timezone.utc)
        return datetime.fromisoformat(value.replace("Z", "+00:00"))


def main():
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    collector = Collector()
    try:
        collector.run_forever()
    except KeyboardInterrupt:
        LOG.info("Collector stopped.")
    finally:
        collector.close()


if __name__ == "__main__":
    main()

