# Ingestion Layer

The ingestion layer is coordinated by `app/ingest.py`, with Windows
Event Log access implemented in `app/windows_reader.py` and rendered
Windows event parsing implemented in
`app/parsers/windows_event_parser.py`.

## Responsibilities

### `app/ingest.py`

- Coordinate enabled telemetry sources.
- Insert normalized event records.
- Extract Sysmon process creation events.
- Collect host metrics when `psutil` is available.
- Commit successful ingestion before advancing collector state.

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

## Source Control

Enabled sources are controlled by the `COLLECTOR_SOURCES` environment variable. If the variable is not set, the collector uses the default source list.

## State Tracking

The collector tracks the latest processed `EventRecordID` per source and channel. This avoids repeatedly processing the same event logs.

Checkpoint loading, validation, updates, and persistence are handled by `app/state.py`.

## Batch Processing

The collector reads up to `COLLECTOR_BATCH_SIZE` events per channel per polling run.

## Error Handling

Database failures trigger a rollback. Windows access-denied errors are logged so restricted channels do not stop the whole collection cycle.
