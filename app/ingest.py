import logging
import os
import socket
import sys
import time
from datetime import datetime, timezone

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
from app.source_handlers import (
    HostMetricsSourceHandler,
    SourceHandler,
    WindowsEventSourceHandler,
)
from app.sources import (
    SourceKind,
    TelemetrySource,
    get_sources,
)
from app.state import CollectorState
from app.windows_reader import WindowsEventReader

LOG = logging.getLogger("sysmon_collector")


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
        self.source_handlers: dict[SourceKind, SourceHandler] = {
            SourceKind.WINDOWS_EVENT: WindowsEventSourceHandler(
                conn=self.conn,
                repository=self.repository,
                reader=self.reader,
                parser=self.parser,
                state=self.state,
                hostname=self.hostname,
            ),
            SourceKind.HOST_METRICS: HostMetricsSourceHandler(
                conn=self.conn,
                repository=self.repository,
                metrics_collector=self.metrics_collector,
            ),
        }

    def _enabled_sources(
        self,
    ) -> tuple[TelemetrySource, ...]:
        source_names = (
            DEFAULT_SOURCES
            if self.settings.enabled_sources is None
            else self.settings.enabled_sources
        )

        return get_sources(source_names)

    def _ingest_source(
        self,
        source: TelemetrySource,
    ) -> int:
        try:
            handler = self.source_handlers[source.kind]
        except KeyError as exc:
            raise ValueError(
                f"No handler registered for source kind {source.kind!r}"
            ) from exc

        return handler.ingest(source)

    def close(self):
        self.conn.close()

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
                total += self._ingest_source(source)

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
