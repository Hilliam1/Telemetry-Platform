# Phase 1: Configuration and Database Refactor

This document explains the Phase 1 refactor that extracted two responsibilities out of the application entry files:

- configuration loading
- PostgreSQL connection creation

The goal was to make the first refactor small, safe, and easy to debug. Existing collector behavior, API routes, SQL queries, database schema, and state tracking were intentionally preserved.

## Why This Refactor Exists

Before Phase 1, both `app/ingest.py` and `app/api.py` knew how to create PostgreSQL connections. `ingest.py` also directly owned environment-variable parsing for collector settings such as poll interval, batch size, state file path, and enabled sources.

That worked for an early version, but it created repeated responsibility:

- the collector had database connection details
- the API had database connection details
- collector runtime settings were mixed into collector orchestration
- future code would likely copy the same environment-variable logic again

Phase 1 creates two reusable modules:

- `app/config.py`
- `app/database.py`

This gives the platform a cleaner foundation without changing the user-facing behavior.

## Target Layout

```text
app/
|-- __init__.py
|-- ingest.py
|-- config.py
|-- database.py
`-- api.py
```

## New File: `app/__init__.py`

`app/__init__.py` makes `app` an explicit Python package.

That matters because the refactor uses package imports such as:

```python
from app.config import load_collector_settings
from app.database import create_connection
```

Without `__init__.py`, tooling and some execution contexts may not recognize `app` as a package consistently.

## New File: `app/config.py`

`config.py` now owns environment-variable parsing.

It defines:

```python
DatabaseSettings
CollectorSettings
DEFAULT_SOURCES
load_database_settings()
load_collector_settings()
```

### Database Settings

Database settings are collected into a `DatabaseSettings` dataclass:

```python
DatabaseSettings(
    host=os.getenv("PGHOST", "localhost"),
    database=os.getenv("PGDATABASE", "sysmon_lab"),
    user=os.getenv("PGUSER", "postgres"),
    password=os.getenv("PGPASSWORD", ""),
    port=int(os.getenv("PGPORT", "5432")),
)
```

This keeps database configuration in one place.

### Collector Settings

Collector runtime settings are collected into a `CollectorSettings` dataclass:

```python
CollectorSettings(
    state_file=Path(os.getenv("COLLECTOR_STATE_FILE", "collector_state.json")),
    poll_seconds=int(os.getenv("COLLECTOR_POLL_SECONDS", "5")),
    batch_size=int(os.getenv("COLLECTOR_BATCH_SIZE", "100")),
    enabled_sources=enabled_sources,
)
```

This replaces module-level constants that previously lived in `ingest.py`:

- `STATE_FILE`
- `POLL_SECONDS`
- `BATCH_SIZE`
- `DEFAULT_SOURCES`

`DEFAULT_SOURCES` now lives in `config.py` because it is part of collector configuration.

## New File: `app/database.py`

`database.py` now owns PostgreSQL connection creation.

It provides two connection patterns:

```python
conn = create_connection()
```

for long-running processes like the collector, and:

```python
with database_connection() as conn:
```

for short-lived API requests.

The actual `psycopg2.connect(...)` call now lives only in `database.py`.

That means the rest of the app does not need to know how PostgreSQL credentials are loaded or passed into `psycopg2`.

## Changes in `app/ingest.py`

`ingest.py` no longer directly parses collector environment variables and no longer constructs PostgreSQL connections directly.

It now imports:

```python
from app.config import (
    DEFAULT_SOURCES,
    load_collector_settings,
)
from app.database import create_connection
```

The collector constructor now does this:

```python
self.settings = load_collector_settings()
self.state = self._load_state()
self.conn = create_connection()
```

### Poll Interval

Old responsibility:

```python
POLL_SECONDS
```

New responsibility:

```python
self.settings.poll_seconds
```

### Batch Size

Old responsibility:

```python
BATCH_SIZE
```

New responsibility:

```python
self.settings.batch_size
```

### State File

Old responsibility:

```python
STATE_FILE
```

New responsibility:

```python
self.settings.state_file
```

This preserves the existing state-file behavior. If the same `COLLECTOR_STATE_FILE` value is used, the collector continues from the same state file.

### Enabled Sources

`_enabled_sources()` now reads already-parsed settings:

```python
def _enabled_sources(self):
    if self.settings.enabled_sources is None:
        return DEFAULT_SOURCES

    return self.settings.enabled_sources
```

## What Stayed in `app/ingest.py`

Phase 1 intentionally leaves these responsibilities in `ingest.py`:

- Windows channel polling
- XML parsing
- state tracking behavior
- health metrics
- process parsing
- collector orchestration
- Windows channel map
- severity map

This keeps Phase 1 focused. Those areas can be split later after configuration and database ownership are stable.

## Changes in `app/api.py`

`api.py` no longer constructs PostgreSQL connections directly.

It now imports:

```python
from app.database import database_connection
```

Each route uses:

```python
with database_connection() as conn:
    with conn.cursor() as cur:
        cur.execute(...)
```

No route paths, SQL queries, response fields, or limits were intentionally changed during Phase 1.

## Direct Execution Support

`ingest.py` can be run from the repository root in the normal direct style:

```powershell
python app\ingest.py
```

It can also be loaded as a package module:

```powershell
python -m app.ingest
```

The small path bootstrap at the top of `ingest.py` exists to support direct execution from the repository root while keeping the new package imports.

## Acceptance Criteria

Phase 1 acceptance criteria:

- `config.py` owns environment-variable parsing.
- `database.py` owns PostgreSQL connection creation.
- `ingest.py` no longer constructs PostgreSQL connections directly.
- `api.py` no longer constructs PostgreSQL connections directly.
- Existing collector and API behavior remains unchanged.
- No schema migration is required.
- Existing SQL scripts remain unchanged.
- Collector state continues from the current state file.
- Python modules compile and load from the repository root.

## Verification Commands

Compile the changed modules:

```powershell
python -B -m py_compile app\ingest.py app\config.py app\database.py app\api.py app\__init__.py
```

Verify package imports:

```powershell
python -B -c "import app.api; import app.ingest; print('imports ok')"
```

Verify direct-path loading without starting the collector:

```powershell
python -B -c "import runpy; runpy.run_path('app/ingest.py', run_name='not_main'); print('direct path load ok')"
```

Verify the API can start from the repository root:

```powershell
python -m uvicorn app.api:app --host 127.0.0.1 --port 8017
```

Then browse or request:

```text
http://127.0.0.1:8017/
```

Expected response:

```json
{"status":"log api online"}
```

## What Phase 1 Does Not Do

Phase 1 does not:

- change database schema
- modify SQL migration files
- refactor XML parsing
- refactor Windows Event Log polling
- add new API routes
- change API response shapes
- add authentication
- add connection pooling
- change process event parsing

Those belong in later work.

## Suggested Commit

```text
refactor: extract configuration and database access
```

