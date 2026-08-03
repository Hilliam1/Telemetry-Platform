# Ingestion Layer

The ingestion layer is coordinated by `app/ingest.py`, with Windows
Event Log access implemented in `app/windows_reader.py` and rendered
Windows event parsing implemented in
`app/parsers/windows_event_parser.py`. Database persistence is handled
by `app/repository.py` using the transaction controlled by `app/ingest.py`.

## Responsibilities

### `app/ingest.py`

- Coordinate enabled telemetry sources.
- Decide which telemetry records should be persisted.
- Commit and roll back database transactions.
- Commit successful ingestion before advancing collector state.

### `app/health_metrics.py`

- Detect whether `psutil` is available.
- Collect CPU utilization.
- Collect memory utilization.
- Collect system-drive utilization.
- Collect host boot time.
- Return a normalized host-health snapshot.

### `app/windows_reader.py`

- Build checkpoint-aware Windows Event Log queries.
- Execute `EvtQuery`.
- Read event batches with `EvtNext`.
- Render events as XML with `EvtRender`.
- Manage query and event-handle lifecycles.

### `app/parsers/windows_event_parser.py`

- Parse rendered Windows event XML.
- Normalize provider, event ID, record ID, severity, timestamp, and computer fields.
- Convert `EventData` and `UserData` into dictionaries.
- Build the normalized event message and raw event payload.

### `app/repository.py`

- Persist normalized events to `log_events`.
- Persist Sysmon process creation records to `process_events`.
- Persist host snapshots to `host_metrics`.
- Persist polling results to `collector_runs`.
- Execute SQL using the transaction supplied by the ingestion orchestrator.

`TelemetryRepository` does not commit or roll back transactions. Transaction ownership remains in `app/ingest.py`.

## Persistence flow

```text
WindowsEventReader
-> WindowsEventParser
-> Collector orchestration
-> TelemetryRepository
-> PostgreSQL
-> commit
-> checkpoint update
```

## Host-health collection

When `health_metrics` is enabled, `app/ingest.py` requests a snapshot
from `HostMetricsCollector`. The collector returns normalized CPU,
memory, disk, and boot-time values. The ingestion orchestrator passes
that snapshot to `TelemetryRepository`, which inserts it into the
`host_metrics` table using the orchestrator-controlled transaction.

## Source Control

Enabled sources are controlled by the `COLLECTOR_SOURCES` environment variable. If the variable is not set, the collector uses the default source list.

## State Tracking

The collector tracks the latest processed `EventRecordID` per source and channel. This avoids repeatedly processing the same event logs.

Checkpoint loading, validation, updates, and persistence are handled by `app/state.py`.

## Batch Processing

The collector reads up to `COLLECTOR_BATCH_SIZE` events per channel per polling run.

## Error Handling

Database failures trigger a rollback. Windows access-denied errors are logged so restricted channels do not stop the whole collection cycle.
