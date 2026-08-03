# Phase 5: Host Health Metrics Refactor

This document explains the Phase 5 refactor that moved host-health measurement out of `app/ingest.py` and into `app/health_metrics.py`.

Phase 5 is a behavior-preserving refactor. The collector still supports the `health_metrics` source, returns the same metric keys, writes to the same `host_metrics` table, and keeps the same transaction behavior. The main change is that `ingest.py` no longer imports `psutil` or calculates local machine health values itself.

## Why This Refactor Exists

Before Phase 5, `ingest.py` handled local host-health collection directly.

That meant the collector owned:

- optional `psutil` import handling
- hostname resolution for metrics
- `SYSTEMDRIVE` lookup
- CPU percentage collection
- memory percentage collection
- disk usage collection
- boot-time collection
- host-health dictionary formatting

Those details are not part of collector orchestration. They are local measurement concerns.

Phase 5 creates a focused module:

```text
app/health_metrics.py
```

The collector now asks that module for a normalized metrics snapshot.

## Target Layout

```text
app/
|-- __init__.py
|-- api.py
|-- config.py
|-- database.py
|-- health_metrics.py
|-- ingest.py
|-- state.py
|-- windows_reader.py
`-- parsers/
    |-- __init__.py
    `-- windows_event_parser.py

tests/
|-- test_health_metrics.py
|-- test_ingest_state.py
|-- test_state.py
|-- test_windows_event_parser.py
`-- test_windows_reader.py
```

## New File: `app/health_metrics.py`

`app/health_metrics.py` introduces `HostMetricsCollector`.

The metrics collector owns:

- resolving the hostname
- resolving the Windows system drive
- detecting whether `psutil` is available
- collecting CPU utilization
- collecting memory utilization
- collecting disk utilization
- collecting boot time
- returning a normalized host-health snapshot

## Metrics Input and Output

The collector can be created with explicit values:

```python
HostMetricsCollector(
    hostname="HOST-01",
    system_drive="C:",
)
```

If those values are not provided:

- `hostname` defaults to `socket.gethostname()`
- `system_drive` defaults to `SYSTEMDRIVE`, or `C:` if the environment variable is missing

The `collect()` method returns a dictionary.

When `psutil` is available, the dictionary includes:

- `collector_time`
- `host`
- `psutil_available`
- `cpu_percent`
- `memory_percent`
- `disk_percent`
- `boot_time`

When `psutil` is unavailable, the dictionary includes:

- `collector_time`
- `host`
- `psutil_available`

That preserves the existing behavior: `ingest.py` skips inserting host metrics when `psutil_available` is false.

## Disk Root Normalization

The metrics collector normalizes the drive root before calling `psutil.disk_usage()`.

For example:

```text
C:
C:\
```

both become:

```text
C:\
```

This keeps disk usage collection predictable.

## Changes in `app/ingest.py`

`ingest.py` now imports:

```python
from app.health_metrics import HostMetricsCollector
```

The collector constructor creates the metrics collector:

```python
self.metrics_collector = HostMetricsCollector(
    hostname=self.hostname
)
```

`ingest_health_metrics()` now delegates collection:

```python
metrics = self.metrics_collector.collect()
```

`ingest.py` still owns the database insert and transaction:

```python
self.conn.commit()
```

This keeps Phase 5 narrow. Persistence is extracted later.

## What Stayed in `app/ingest.py`

Phase 5 intentionally keeps these responsibilities in `ingest.py`:

- deciding whether the `health_metrics` source is enabled
- requesting a metrics snapshot
- skipping insertion when `psutil` is unavailable
- inserting host metrics into PostgreSQL
- committing the host-metrics transaction

## What Moved Out of `app/ingest.py`

These responsibilities moved into `app/health_metrics.py`:

- `psutil` import
- `SYSTEMDRIVE` lookup
- CPU measurement
- memory measurement
- disk measurement
- boot-time measurement
- metrics dictionary construction

## Tests

`tests/test_health_metrics.py` covers:

- supplied hostname values
- supplied drive values
- disk root normalization
- mocked CPU collection
- mocked memory collection
- mocked disk collection
- mocked boot-time collection
- timezone-aware timestamps
- missing `psutil` behavior

The tests use mocks, so they do not require PostgreSQL, Windows Event Log access, or actual host metrics.

## Verification

Phase 5 validation:

```powershell
py -m pytest -v
py -m compileall app tests
```

Ownership check:

```powershell
rg -n "psutil|SYSTEMDRIVE|cpu_percent|virtual_memory|disk_usage|boot_time|_collect_health_metrics" app tests
```

Expected ownership:

- direct `psutil` usage appears in `app/health_metrics.py`.
- `app/ingest.py` imports `HostMetricsCollector`, not `psutil`.

## Acceptance Criteria

Phase 5 passes when:

- `app/health_metrics.py` owns all direct `psutil` interaction.
- `ingest.py` no longer imports `psutil`.
- `ingest.py` no longer calculates CPU, memory, disk, or boot-time values.
- `ingest.py` still owns the `host_metrics` database insert.
- returned metric keys remain unchanged.
- `health_metrics` remains an enabled source.
- no API or SQL schema changes occur.
- unit tests work without Windows Event Log access or PostgreSQL.
- full collector ingestion remains functional.

## What Phase 5 Does Not Do

Phase 5 does not:

- change API routes
- change SQL schema
- move database inserts into a repository
- change Windows event collection
- change Windows event parsing
- change checkpoint state behavior

Those belong in later phases.

