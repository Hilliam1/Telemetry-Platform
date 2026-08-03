# Ingestion Layer

The ingestion layer is coordinated by `app/collector.py`, with collector
dependency construction handled by `app/collector_factory.py`. Windows
Event Log access implemented in `app/windows_reader.py` and rendered
Windows event parsing implemented in
`app/parsers/windows_event_parser.py`. Database persistence is handled
by `app/repository.py` using transactions controlled by the source handlers
and collector service.
Telemetry source definitions and dispatch categories are defined in
`app/sources.py`, and source-specific execution lives in
`app/source_handlers.py`.

## Responsibilities

### `app/collector.py`

- Coordinate enabled telemetry sources.
- Dispatch each telemetry source to the handler registered for its source kind.
- Record collector-run status.
- Coordinate collector-run transactions.
- Own the polling loop.
- Close the shared database connection during shutdown.

### `app/collector_factory.py`

- Load collector configuration.
- Resolve the local hostname.
- Construct state, reader, parser, metrics, and repository components.
- Construct source-handler implementations.
- Register handlers by `SourceKind`.
- Return a fully configured `Collector`.

### `app/ingest.py`

- Configure process logging.
- Construct the collector through `create_collector()`.
- Start the polling process.
- Handle keyboard interruption and shutdown.

### `app/health_metrics.py`

- Detect whether `psutil` is available.
- Collect CPU utilization.
- Collect memory utilization.
- Collect system-drive utilization.
- Collect host boot time.
- Return a normalized host-health snapshot.

### `app/sources.py`

- Define supported telemetry sources.
- Associate source names with source categories.
- Associate Windows sources with their Event Log channels.
- Validate names supplied through `COLLECTOR_SOURCES`.
- Provide explicit source definitions to the ingestion orchestrator.

### `app/source_handlers.py`

- Define the common `SourceHandler` interface.
- Implement Windows Event Log source execution.
- Implement host-health source execution.
- Isolate source-specific transactions and error behavior.
- Allow the ingestion orchestrator to dispatch sources polymorphically.

Windows channel-processing logic and host metrics ingestion logic are no longer implemented directly in `app/collector.py` or `app/ingest.py`. The collector resolves the appropriate handler from the source kind and calls `handler.ingest(source)`.

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

`TelemetryRepository` does not commit or roll back transactions. Source-level transaction boundaries live in source handlers. Collector-run transaction ownership remains in `app/collector.py`.

## Persistence flow

```text
Configuration
-> Collector Factory
-> Source Registry
-> Collector
-> Source Handler
   |-> Windows Event Handler
   `-> Host Metrics Handler
-> TelemetryRepository
-> PostgreSQL
```

## Host-health collection

When `health_metrics` is enabled, `app/collector.py` dispatches the source to
`HostMetricsSourceHandler`. The handler requests a snapshot from
`HostMetricsCollector`, passes that snapshot to `TelemetryRepository`, and
commits the host metrics transaction.

## Source Control

Enabled source names are loaded from `COLLECTOR_SOURCES`. If the variable is not set, the collector uses the default source list from `app/config.py`.

`app/sources.py` resolves source names into explicit source definitions. Unknown names produce a configuration error listing the supported sources.

## State Tracking

The collector tracks the latest processed `EventRecordID` per source and channel. This avoids repeatedly processing the same event logs.

Checkpoint loading, validation, updates, and persistence are handled by `app/state.py`. Windows checkpoint updates are coordinated by `WindowsEventSourceHandler` after the database commit succeeds.

## Batch Processing

`WindowsEventSourceHandler` reads up to `COLLECTOR_BATCH_SIZE` events per channel per polling run through `WindowsEventReader`.

## Error Handling

Database failures trigger a rollback. Windows access-denied errors are handled by `WindowsEventSourceHandler` so restricted channels do not stop the whole collection cycle.
