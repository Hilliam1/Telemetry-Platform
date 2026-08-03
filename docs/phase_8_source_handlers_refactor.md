# Phase 8 Source Handlers Refactor

Phase 8 is the next planned refactor after the source registry work from
Phase 7. Phase 7 gave the collector explicit source definitions. Phase 8
should move the source-specific execution logic out of `app/ingest.py` and
into dedicated source handlers.

This is the first phase where polymorphism becomes a practical design tool in
the collector.

## Current Problem

After Phase 7, `app/ingest.py` no longer uses dynamic `getattr()` calls to
choose collector methods. It resolves configured source names through
`app/sources.py` and dispatches by `SourceKind`.

That is a major improvement, but `Collector` still knows too much about how
each source works.

Today, `Collector` still owns or coordinates details such as:

- Windows Event Log channel loops.
- Windows access-denied handling.
- XML parsing and event persistence calls.
- Per-channel transaction commits.
- Checkpoint updates after Windows event commits.
- Host-health metric collection and insertion.

Those details are source-specific. They should live behind a shared handler
interface so the collector can stay focused on orchestration.

## Goal

After Phase 8, `Collector` should:

1. Load enabled source definitions.
2. Find the handler registered for each source kind.
3. Call `handler.ingest(source)`.
4. Record the overall collector run.
5. Control the polling loop.

It should not know the internal process for Windows event ingestion or host
metrics ingestion.

## Planned Module

Phase 8 should add:

```text
app/source_handlers.py
```

That module should define a common handler interface and concrete handlers for
the current source categories.

Planned structure:

```text
SourceHandler
|-- WindowsEventSourceHandler
`-- HostMetricsSourceHandler
```

## `SourceHandler`

`SourceHandler` should be an abstract base class. It defines the behavior every
source handler must provide.

Expected interface:

```python
class SourceHandler(ABC):
    @property
    @abstractmethod
    def kind(self) -> SourceKind:
        """Return the source category handled by this object."""

    @abstractmethod
    def ingest(self, source: TelemetrySource) -> int:
        """Collect and persist data for one telemetry source."""
```

The important idea is that every handler can be used through the same method:

```python
handler.ingest(source)
```

The collector does not need to know whether the handler reads Windows Event
Logs, collects host metrics, or eventually reads another telemetry source.

## `WindowsEventSourceHandler`

`WindowsEventSourceHandler` should own the Windows Event Log workflow currently
inside the collector.

Responsibilities:

- Loop through the Windows channels listed on a `TelemetrySource`.
- Ask `CollectorState` for the last processed record ID.
- Ask `WindowsEventReader` for rendered XML events newer than the checkpoint.
- Ask `WindowsEventParser` to normalize each XML event.
- Sort parsed events by record ID.
- Ask `TelemetryRepository` to stage raw log event inserts.
- Ask `TelemetryRepository` to stage Sysmon process event inserts.
- Commit the database transaction before advancing the checkpoint.
- Save collector state after the successful commit.
- Roll back the database transaction if a channel fails.
- Keep access-denied handling local to the Windows source workflow.

The safe ordering must remain:

```text
read events
-> parse events
-> stage database rows
-> commit PostgreSQL transaction
-> update in-memory checkpoint
-> save checkpoint file
```

This ordering prevents the collector from skipping events that were parsed but
not committed to the database.

## `HostMetricsSourceHandler`

`HostMetricsSourceHandler` should own the host-health workflow currently inside
the collector.

Responsibilities:

- Ask `HostMetricsCollector` for a normalized snapshot.
- Skip persistence if `psutil` is unavailable.
- Ask `TelemetryRepository` to insert the host metrics row.
- Commit the transaction after the insert.

The handler will receive a `TelemetrySource` argument even though the current
host metrics workflow does not need fields from it. That keeps all handlers on
the same interface.

## Collector After Phase 8

The collector should build a handler registry during initialization.

Expected shape:

```python
self.source_handlers: dict[SourceKind, SourceHandler] = {
    SourceKind.WINDOWS_EVENT: WindowsEventSourceHandler(...),
    SourceKind.HOST_METRICS: HostMetricsSourceHandler(...),
}
```

Then dispatch becomes:

```python
def _ingest_source(self, source: TelemetrySource) -> int:
    try:
        handler = self.source_handlers[source.kind]
    except KeyError as exc:
        raise ValueError(
            f"No handler registered for source kind {source.kind!r}"
        ) from exc

    return handler.ingest(source)
```

This means `Collector` no longer switches directly on `SourceKind`. The source
kind is used only as a registry key.

## Planned Flow

```text
Configuration
    |
    v
Source Registry
    |
    v
Collector
    |
    v
Source Handler Registry
    |
    +-- WindowsEventSourceHandler
    |       |
    |       v
    |   WindowsEventReader
    |       |
    |       v
    |   WindowsEventParser
    |
    +-- HostMetricsSourceHandler
            |
            v
        HostMetricsCollector

Handlers
    |
    v
TelemetryRepository
    |
    v
PostgreSQL
```

## Why This Matters

This refactor makes the collector easier to grow.

Without handlers, every new source category adds more conditional logic to
`Collector`. Over time, `ingest.py` would become a large file that knows the
details of every telemetry source.

With handlers, new source categories can be added by creating a new concrete
handler and registering it.

Examples:

- `LinuxJournalSourceHandler`
- `ProxmoxTaskSourceHandler`
- `WazuhAlertSourceHandler`
- `NetworkDeviceSourceHandler`

The collector can stay stable while source-specific code grows around it.

## Beginner Explanation

Polymorphism means different objects can be used through the same interface.

In this project, both a Windows event handler and a host metrics handler should
support:

```python
handler.ingest(source)
```

They do different work internally, but the collector does not need to care.

That is useful because the collector can treat every source the same way:

```text
get source
find handler
ask handler to ingest it
add result to total
```

The handler owns the source-specific work.

## Testing Focus

Phase 8 tests should cover:

- `HostMetricsSourceHandler.kind`.
- `HostMetricsSourceHandler` inserts metrics when `psutil` data is available.
- `HostMetricsSourceHandler` skips insertion when `psutil` is unavailable.
- `WindowsEventSourceHandler.kind`.
- Windows event handler channel ingestion.
- Windows event handler checkpoint update after commit.
- Windows event handler rollback on channel failure.
- Collector dispatch to the registered handler.
- Collector failure when no handler is registered for a source kind.

The tests should verify behavior without requiring live Windows Event Log or
PostgreSQL access.

## Acceptance Criteria

Phase 8 is complete when:

- `SourceHandler` defines the common handler interface.
- Windows and health sources use separate concrete handlers.
- `Collector` contains no Windows channel-processing logic.
- `Collector` contains no host-metrics ingestion logic.
- `Collector` does not switch directly on `SourceKind`.
- Source dispatch uses a handler registry.
- Windows channel rollback behavior remains unchanged.
- Commit-before-checkpoint behavior remains unchanged.
- Collector-run recording remains in `Collector`.
- No API, schema, or SQL changes are introduced.
- Existing and new tests pass.

## Suggested Commit

```text
refactor: extract source handlers
```
