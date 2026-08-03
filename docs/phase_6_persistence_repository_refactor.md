# Phase 6: Persistence Repository Refactor

This document explains the Phase 6 refactor that moved collector SQL insert operations out of `app/ingest.py` and into `app/repository.py`.

Phase 6 is a behavior-preserving refactor. The collector still inserts the same rows, uses the same database schema, returns the same counts, and preserves commit-before-checkpoint ordering. The main change is that `ingest.py` now decides what should be persisted, while `TelemetryRepository` owns how that data is inserted into PostgreSQL.

## Why This Refactor Exists

Before Phase 6, `ingest.py` still contained SQL for four tables:

- `log_events`
- `process_events`
- `host_metrics`
- `collector_runs`

That made the collector responsible for both orchestration and SQL persistence.

Those are different jobs:

- `ingest.py` should coordinate reading, parsing, persistence requests, commits, rollbacks, and checkpoint state.
- `repository.py` should execute SQL statements using the connection it is given.

Phase 6 separates those jobs.

## Target Flow

```text
app/ingest.py
    |
    | read
    | parse
    | coordinate
    v
TelemetryRepository
    |
    | insert log event
    | insert process event
    | insert host metrics
    | insert collector run
    v
PostgreSQL
```

## New File: `app/repository.py`

`app/repository.py` introduces `TelemetryRepository`.

The repository owns:

- inserting normalized events into `log_events`
- inserting Sysmon process creation events into `process_events`
- inserting host-health snapshots into `host_metrics`
- inserting collector polling results into `collector_runs`
- extracting SHA-256 values for Sysmon process records

The repository receives an existing PostgreSQL connection:

```python
TelemetryRepository(self.conn)
```

It does not create its own connection.

## Transaction Ownership

This is the most important Phase 6 boundary:

```text
TelemetryRepository does not commit.
TelemetryRepository does not roll back.
```

`app/ingest.py` still owns:

- `self.conn.commit()`
- `self.conn.rollback()`

That preserves the existing transaction lifecycle.

For Windows event ingestion, the required ordering remains:

```text
stage log/process rows
-> commit PostgreSQL transaction
-> advance in-memory checkpoint
-> save checkpoint file
```

This matters because advancing the checkpoint before a successful commit could skip events after a database failure.

## Repository Methods

### `insert_log_event`

Persists one normalized event into `log_events`.

The collector passes keyword arguments such as:

- source host
- source type
- provider name
- event ID
- record ID
- severity
- timestamp
- message
- raw JSON

### `insert_process_event`

Persists Sysmon Event ID 1 process creation records into `process_events`.

The method returns:

```python
True
```

when it inserts a process record, and:

```python
False
```

when the event is not a Sysmon process creation event.

This preserves the old behavior from `ingest.py`.

### `insert_host_metrics`

Persists one host-health snapshot into `host_metrics`.

The metrics still use the same keys:

- `host`
- `cpu_percent`
- `memory_percent`
- `disk_percent`
- `boot_time`

### `insert_collector_run`

Persists one collector run summary into `collector_runs`.

This records:

- source host
- status
- inserted event count
- start time
- optional error message

## Changes in `app/ingest.py`

`ingest.py` now imports:

```python
from app.repository import TelemetryRepository
```

The collector constructor creates the repository after creating the database connection:

```python
self.conn = create_connection()
self.repository = TelemetryRepository(self.conn)
```

`ingest_health_metrics()` now delegates the insert:

```python
self.repository.insert_host_metrics(metrics)
self.conn.commit()
```

`_ingest_channel()` now delegates event persistence:

```python
self.repository.insert_log_event(...)
self.repository.insert_process_event(event)
```

`run_once()` now delegates collector-run persistence:

```python
self.repository.insert_collector_run(...)
self.conn.commit()
```

## What Stayed in `app/ingest.py`

Phase 6 intentionally keeps these responsibilities in `ingest.py`:

- source orchestration
- reader coordination
- parser coordination
- repository coordination
- commit and rollback ownership
- checkpoint update ordering
- access-denied handling
- returned insert counts

## What Moved Out of `app/ingest.py`

These responsibilities moved into `app/repository.py`:

- `INSERT INTO log_events`
- `INSERT INTO process_events`
- `INSERT INTO host_metrics`
- `INSERT INTO collector_runs`
- Sysmon SHA-256 extraction for persisted process records

## Tests

`tests/test_repository.py` covers:

- log event insert execution
- non-Sysmon events skipping process inserts
- Sysmon Event ID 1 process insert execution
- case-insensitive SHA-256 extraction
- repository methods not calling `commit()`
- repository methods not calling `rollback()`

`tests/test_ingest_state.py` was updated so collector orchestration tests use a fake repository instead of patching removed `_insert_event` and `_insert_process_event` methods.

## Verification

Phase 6 validation:

```powershell
py -m pytest -v
py -m compileall app tests
```

Ruff validation for the Phase 6 Python files:

```powershell
py -m ruff check app/ingest.py app/repository.py tests/test_ingest_state.py tests/test_repository.py
py -m ruff format --check app/ingest.py app/repository.py tests/test_ingest_state.py tests/test_repository.py
```

Ownership check:

```powershell
rg -n "INSERT INTO|commit\(|rollback\(|TelemetryRepository" app tests
```

Expected ownership:

- `INSERT INTO` collector persistence SQL appears in `app/repository.py`.
- `commit()` and `rollback()` remain in `app/ingest.py`.
- `app/repository.py` does not commit or roll back.

## Acceptance Criteria

Phase 6 passes when:

- `app/repository.py` owns collector persistence SQL.
- `ingest.py` contains no collector `INSERT INTO` statements.
- `ingest.py` delegates persistence through `TelemetryRepository`.
- transaction ownership remains in `ingest.py`.
- checkpoint updates still happen after successful database commits.
- no schema migration is required.
- existing SQL scripts remain unchanged.
- API behavior remains unchanged.
- all tests pass.

## Architectural Note

`insert_process_event()` still performs some Sysmon-specific interpretation:

- checks `source_type`
- checks Event ID 1
- reads process event fields
- extracts SHA-256
- converts process ID

That preserves existing behavior and is acceptable for Phase 6.

Longer term, a Sysmon-specific normalizer could prepare structured process data before persistence. That would let the repository accept already-normalized process records and focus only on SQL.

That future cleanup is intentionally outside Phase 6.

