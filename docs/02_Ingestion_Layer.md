# Ingestion Layer

The ingestion layer is currently implemented in `app/ingest.py`.

## Responsibilities

- Connect to PostgreSQL.
- Read enabled event sources.
- Query Windows Event Log channels.
- Parse event XML.
- Insert normalized event records.
- Extract Sysmon process creation events.
- Collect host metrics when `psutil` is available.
- Save collector state after successful ingestion.

## Source Control

Enabled sources are controlled by the `COLLECTOR_SOURCES` environment variable. If the variable is not set, the collector uses the default source list.

## State Tracking

The collector tracks the latest processed `EventRecordID` per source and channel. This avoids repeatedly processing the same event logs.

## Batch Processing

The collector reads up to `COLLECTOR_BATCH_SIZE` events per channel per polling run.

## Error Handling

Database failures trigger a rollback. Windows access-denied errors are logged so restricted channels do not stop the whole collection cycle.

