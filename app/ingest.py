import json
import logging
import os
import socket
import sys
import time
from datetime import datetime, timezone

import pywintypes

if __package__ in (None, ""):
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import (
    DEFAULT_SOURCES,
    load_collector_settings,
)
from app.database import create_connection
from app.health_metrics import HostMetricsCollector
from app.parsers.windows_event_parser import WindowsEventParser
from app.repository import TelemetryRepository
from app.state import CollectorState
from app.windows_reader import WindowsEventReader

LOG = logging.getLogger("sysmon_collector")

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


class Collector:
    def __init__(self):
        self.hostname = socket.gethostname()
        self.settings = load_collector_settings()
        self.state = CollectorState(self.settings.state_file)
        self.reader = WindowsEventReader(batch_size=self.settings.batch_size)
        self.parser = WindowsEventParser(default_computer=self.hostname)
        self.metrics_collector = HostMetricsCollector(hostname=self.hostname)
        self.conn = create_connection()
        self.repository = TelemetryRepository(self.conn)

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
        metrics = self.metrics_collector.collect()

        if not metrics.get("psutil_available"):
            return 0

        self.repository.insert_host_metrics(metrics)
        self.conn.commit()

        return 1

    def run_forever(self):
        while True:
            total = self.run_once()
            LOG.info(
                "Polling complete. Inserted %s events. Sleeping %s seconds.",
                total,
                self.settings.poll_seconds,
            )
            time.sleep(self.settings.poll_seconds)

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

        self.repository.insert_collector_run(
            source_host=self.hostname,
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
        if self.settings.enabled_sources is None:
            return DEFAULT_SOURCES

        return self.settings.enabled_sources

    def _ingest_channel(self, source_type, channel):
        last_record_id = self.state.get_last_record_id(
            source_type,
            channel,
        )

        event_xml_documents = self.reader.read_channel(
            channel=channel,
            last_record_id=last_record_id,
        )

        parsed_events = [
            self.parser.parse(event_xml) for event_xml in event_xml_documents
        ]

        parsed_events.sort(key=lambda item: item["record_id"])

        inserted = 0
        highest_record_id = None

        for event in parsed_events:
            event["source_type"] = source_type

            self.repository.insert_log_event(
                source_host=event["computer"] or self.hostname,
                source_type=source_type,
                provider_name=event["provider"],
                event_id=event["event_id"],
                event_record_id=event["record_id"],
                severity=event["severity"],
                time_created=event["time_created"],
                message=event["message"],
                raw_data=json.dumps(
                    event["raw"],
                    sort_keys=True,
                ),
            )

            self.repository.insert_process_event(event)

            inserted += 1
            highest_record_id = event["record_id"]

        self.conn.commit()

        if highest_record_id is not None:
            self.state.update_record_id(
                source_type,
                channel,
                highest_record_id,
            )
            self.state.save()

        return inserted


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
