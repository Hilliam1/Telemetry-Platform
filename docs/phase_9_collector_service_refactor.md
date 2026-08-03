# Phase 9 Collector Service Refactor

Phase 9 separates collector orchestration from dependency construction and
process startup.

Before this phase, `app/ingest.py` had three jobs:

- Construct every concrete collector dependency.
- Define the `Collector` orchestration class.
- Configure logging and start the process.

After Phase 9, those responsibilities are split into focused modules.

## Added Modules

```text
app/collector.py
app/collector_factory.py
```

`app/ingest.py` remains the executable entry point.

## Current Structure

```text
app/ingest.py
    |
    v
app/collector_factory.py
    |
    v
app/collector.py
    |
    v
app/source_handlers.py
```

## `app/collector.py`

`app/collector.py` owns the collector orchestration service.

It is responsible for:

- Resolving enabled telemetry sources.
- Dispatching each source to its registered handler.
- Recording overall polling-run status.
- Committing collector-run records.
- Running the continuous polling loop.
- Closing the shared database connection during shutdown.

The `Collector` no longer constructs concrete dependencies. It receives them
through its constructor.

That is dependency injection: code outside the class builds the objects, and
the class receives the objects it needs.

## `app/collector_factory.py`

`app/collector_factory.py` is the composition root.

It is responsible for:

- Resolving the local hostname.
- Loading collector settings.
- Constructing `CollectorState`.
- Constructing `WindowsEventReader`.
- Constructing `WindowsEventParser`.
- Constructing `HostMetricsCollector`.
- Opening the PostgreSQL connection.
- Constructing `TelemetryRepository`.
- Constructing source handlers.
- Registering source handlers by `SourceKind`.
- Returning a fully configured `Collector`.

The factory also closes the PostgreSQL connection if construction fails after
the connection is opened.

## `app/ingest.py`

`app/ingest.py` is now intentionally thin.

It is responsible for:

- Configuring logging.
- Calling `create_collector()`.
- Starting `collector.run_forever()`.
- Handling keyboard interruption.
- Closing the collector during shutdown.

The startup command remains:

```powershell
py -m app.ingest
```

Direct script execution is no longer part of the supported path for this phase.

## Runtime Flow

```text
py -m app.ingest
    |
    v
configure logging
    |
    v
create_collector()
    |
    v
load settings and construct dependencies
    |
    v
return Collector
    |
    v
collector.run_forever()
    |
    v
collector.run_once()
    |
    v
source handler registry
    |
    v
TelemetryRepository
    |
    v
PostgreSQL
```

## What Did Not Change

Phase 9 does not change telemetry behavior.

Unchanged behavior:

- The collector still starts with `py -m app.ingest`.
- Enabled source names still come from `COLLECTOR_SOURCES`.
- Default source behavior is unchanged.
- Windows source dispatch still uses source handlers.
- Host metrics dispatch still uses source handlers.
- Source-level transaction behavior is unchanged.
- Commit-before-checkpoint behavior is unchanged.
- Collector-run records are still written once per polling cycle.
- No API, SQL, or schema changes are introduced.

## Testing

Phase 9 adds direct tests for:

- Collector source dispatch.
- Missing handler errors.
- Successful collector-run recording.
- Failed collector-run recording.
- Collector shutdown.
- Factory dependency construction.
- Factory connection cleanup after construction failure.

The tests use mocks so they do not require live PostgreSQL or Windows Event Log
access.

## Beginner Explanation

Think of the collector startup in three parts:

1. `ingest.py` presses the start button.
2. `collector_factory.py` builds the machine.
3. `collector.py` runs the machine.

This makes the code easier to test because tests can create a `Collector` with
mock dependencies. The collector can be tested without opening PostgreSQL,
reading Windows Event Logs, or loading real environment settings.

## Acceptance Criteria

Phase 9 is complete when:

- `Collector` lives in `app/collector.py`.
- Dependency construction lives in `app/collector_factory.py`.
- `app/ingest.py` is a thin executable entry point.
- Tests import `Collector` from `app.collector`.
- Factory tests verify construction without real external services.
- Factory failures close an opened database connection.
- Existing collector behavior remains unchanged.
- Existing and new tests pass.
