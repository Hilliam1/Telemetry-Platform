# System Architecture

The platform is designed as a layered telemetry pipeline. The current codebase now separates collection, parsing, state management, host metrics, and PostgreSQL persistence into focused modules.

```text
Windows Hosts
    |
    v
Source Registry
    |
    v
WindowsEventReader
    |
    v
WindowsEventParser
    |
    v
Collector Orchestrator
    |
    v
TelemetryRepository
    |
    v
PostgreSQL Database
    |
    v
FastAPI Query Service
    |
    v
Dashboard and Analysis Layer
```

## Collector Orchestrator

`app/ingest.py` coordinates enabled telemetry sources. It decides which sources run, asks helper modules for data, calls the repository to stage database writes, owns commit and rollback behavior, and advances checkpoints only after successful commits.

The collector is still the entry point:

```powershell
py -m app.ingest
```

## Source Registry

`app/sources.py` defines the supported telemetry sources. It maps source names to source categories and, for Windows event sources, to one or more Event Log channels.

The registry replaces dynamic `getattr()` dispatch with explicit source definitions. Unknown source names now raise a readable configuration error that lists supported sources.

## Windows Event Reader

`app/windows_reader.py` owns direct Windows Event Log access. It builds checkpoint-aware queries, calls `EvtQuery`, reads batches with `EvtNext`, renders events with `EvtRender`, and closes Windows query and event handles.

## Parsing and Normalization Layer

`app/parsers/windows_event_parser.py` parses rendered Windows event XML into normalized Python dictionaries.

It owns:

- provider extraction
- event ID conversion
- record ID conversion
- severity mapping
- timestamp parsing
- `EventData` conversion
- nested `UserData` conversion

## Host Metrics Layer

`app/health_metrics.py` owns local host-health collection through optional `psutil` support. It returns normalized CPU, memory, disk, and boot-time values.

## Persistence Layer

`app/repository.py` owns collector SQL insert operations for:

- `log_events`
- `process_events`
- `host_metrics`
- `collector_runs`

The repository does not commit or roll back. Transaction ownership remains in `app/ingest.py`.

## State Layer

`app/state.py` owns checkpoint loading, validation, monotonic record ID updates, and atomic state-file persistence.

The critical event-ingestion order is:

```text
read events
-> parse events
-> stage database rows
-> commit PostgreSQL transaction
-> advance checkpoint
-> save checkpoint
```

## Database Layer

PostgreSQL stores raw events, process events, host metrics, and collector run records.

## API Layer

`app/api.py` exposes queryable FastAPI endpoints for logs, event counts, search, and host metrics.

## Dashboard Layer

The dashboard layer is planned. It will show event trends, host activity, process creation, collector health, and investigation views.
