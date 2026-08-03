# Phase 7: Source Registry Refactor

This document explains the Phase 7 refactor that moved telemetry source definitions and source dispatch out of `app/ingest.py` and into `app/sources.py`.

Phase 7 is a behavior-preserving refactor. The collector still reads the same Windows Event Log channels, supports the same `health_metrics` source, preserves source ordering, keeps channel-level error isolation, and leaves transactions and checkpoint ownership in `app/ingest.py`.

## Why This Refactor Exists

Before Phase 7, `ingest.py` owned source definitions and dynamic source dispatch.

That meant `ingest.py` contained:

- the `EVENT_CHANNELS` dictionary
- seven repetitive `ingest_windows_*` forwarding methods
- dynamic dispatch with `getattr(self, f"ingest_{source}")()`

That worked, but it had two design problems.

First, source definitions were mixed into the collector orchestrator. Second, invalid `COLLECTOR_SOURCES` values failed with a generic `AttributeError` instead of a clear configuration message.

Phase 7 introduces an explicit source registry.

## Target Layout

```text
app/
|-- __init__.py
|-- api.py
|-- config.py
|-- database.py
|-- health_metrics.py
|-- ingest.py
|-- repository.py
|-- sources.py
|-- state.py
|-- windows_reader.py
`-- parsers/
    |-- __init__.py
    `-- windows_event_parser.py

tests/
|-- test_collector_sources.py
|-- test_sources.py
`-- ...
```

## New File: `app/sources.py`

`app/sources.py` introduces:

- `SourceKind`
- `TelemetrySource`
- `SOURCE_REGISTRY`
- `get_source()`
- `get_sources()`

The module does not collect telemetry. It only defines source metadata and validates source names.

## Source Kinds

`SourceKind` identifies how a source should be dispatched.

Current source kinds:

```python
SourceKind.WINDOWS_EVENT
SourceKind.HOST_METRICS
```

Windows event sources are handled through the Windows Event Log reader and parser.

Host metrics sources are handled through `HostMetricsCollector`.

## TelemetrySource

`TelemetrySource` describes one source:

```python
TelemetrySource(
    name="sysmon",
    kind=SourceKind.WINDOWS_EVENT,
    channels=("Microsoft-Windows-Sysmon/Operational",),
)
```

Fields:

- `name`: the source name used in `COLLECTOR_SOURCES`
- `kind`: the dispatch category
- `channels`: Windows Event Log channels for Windows event sources

The `health_metrics` source has no Windows channels:

```python
TelemetrySource(
    name="health_metrics",
    kind=SourceKind.HOST_METRICS,
)
```

## Source Registry

`SOURCE_REGISTRY` contains all currently supported source definitions:

- `windows_system`
- `windows_application`
- `windows_security`
- `sysmon`
- `powershell`
- `defender`
- `task_scheduler`
- `health_metrics`

The default source names still live in `app/config.py`. Phase 7 intentionally does not import the registry into `config.py`, which keeps configuration parsing independent from source implementation details.

## Clear Configuration Errors

`get_source()` raises a readable `ValueError` for unknown source names.

Example:

```text
Unknown telemetry source 'not_a_real_source'. Supported sources: defender, health_metrics, powershell, sysmon, task_scheduler, windows_application, windows_security, windows_system
```

This replaces the older dynamic dispatch failure:

```text
AttributeError: Collector has no attribute ingest_not_a_real_source
```

## Changes in `app/ingest.py`

`ingest.py` now imports:

```python
from app.sources import (
    SourceKind,
    TelemetrySource,
    get_sources,
)
```

The old `EVENT_CHANNELS` dictionary was removed.

The repetitive source methods were removed:

- `ingest_windows_system`
- `ingest_windows_application`
- `ingest_windows_security`
- `ingest_sysmon`
- `ingest_powershell`
- `ingest_defender`
- `ingest_task_scheduler`

`run_once()` now dispatches explicit source objects:

```python
for source in self._enabled_sources():
    total += self._ingest_source(source)
```

`_enabled_sources()` now resolves configured names into `TelemetrySource` objects:

```python
return get_sources(source_names)
```

## Explicit Dispatch

`_ingest_source()` dispatches by source kind:

```python
if source.kind is SourceKind.WINDOWS_EVENT:
    return self._ingest_event_source(source)

if source.kind is SourceKind.HOST_METRICS:
    return self.ingest_health_metrics()
```

That makes dispatch explicit and testable.

## Windows Event Source Handling

`_ingest_event_source()` replaces `_ingest_event_channels()`.

It loops through the channels attached to the `TelemetrySource`:

```python
for channel in source.channels:
    inserted += self._ingest_channel(source.name, channel)
```

Channel-level error isolation remains unchanged. If one channel fails, the collector rolls back that channel's staged work and continues with the next channel.

## What Stayed in `app/ingest.py`

Phase 7 intentionally keeps these responsibilities in `ingest.py`:

- source orchestration
- transaction ownership
- rollback behavior
- checkpoint updates
- Windows access-denied handling
- host metrics ingestion workflow

## What Moved Out of `app/ingest.py`

These responsibilities moved into `app/sources.py`:

- supported source definitions
- source categories
- Windows channel mapping
- source name validation

## Tests

`tests/test_sources.py` covers:

- Windows System source definition
- PowerShell channel definitions
- health metrics source kind
- source order preservation
- clear unknown-source errors
- registry coverage for all default sources

`tests/test_collector_sources.py` covers:

- dispatching Windows event sources to `_ingest_event_source()`
- dispatching host metrics sources to `ingest_health_metrics()`

## Verification

Phase 7 validation:

```powershell
py -m pytest -v
py -m compileall app tests
```

Focused Ruff validation:

```powershell
py -m ruff check app/ingest.py app/sources.py tests/test_sources.py tests/test_collector_sources.py
py -m ruff format --check app/ingest.py app/sources.py tests/test_sources.py tests/test_collector_sources.py
```

Ownership check:

```powershell
rg -n "EVENT_CHANNELS|getattr\\(|ingest_windows_|_ingest_event_channels" app tests
```

Expected result:

```text
no matches
```

Invalid-source smoke test:

```powershell
$env:COLLECTOR_SOURCES="not_a_real_source"
py -u -m app.ingest
```

Expected outcome:

```text
Unknown telemetry source 'not_a_real_source'
```

Restore defaults:

```powershell
Remove-Item Env:COLLECTOR_SOURCES
```

## Acceptance Criteria

Phase 7 passes when:

- `EVENT_CHANNELS` no longer exists in `ingest.py`.
- repetitive `ingest_windows_*` forwarding methods are removed.
- `getattr()` is no longer used for source dispatch.
- `sources.py` contains all current source definitions.
- invalid source names raise a readable error.
- source order remains configurable.
- channel-level error isolation remains unchanged.
- transaction and checkpoint ownership remain in `ingest.py`.
- no database, API, parser, or schema behavior changes occur.
- existing and new tests pass.

## What Phase 7 Does Not Do

Phase 7 does not:

- introduce plugin loading
- create source subclasses
- change database persistence
- change Windows reading
- change event parsing
- change host metrics collection
- change checkpoint behavior

Those are future expansion points.
