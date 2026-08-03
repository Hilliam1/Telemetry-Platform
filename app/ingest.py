"""Telemetry collector process entry point."""

import logging
import os

from app.collector_factory import create_collector

LOG = logging.getLogger("telemetry_platform.ingest")


def main() -> None:
    """Configure logging and run the telemetry collector."""

    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    collector = create_collector()

    try:
        collector.run_forever()
    except KeyboardInterrupt:
        LOG.info("Collector stopped.")
    finally:
        collector.close()


if __name__ == "__main__":
    main()
