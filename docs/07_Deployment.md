# Deployment

## Prerequisites

- Windows host
- Python 3
- PostgreSQL
- Sysmon
- Python dependencies from `requirements.txt`

## Install Dependencies

```powershell
py -m pip install -r requirements.txt
```

## Configure Environment

```powershell
copy .env.example .env
```

Update `.env` with local PostgreSQL settings.

## Run Collector

```powershell
py -m app.ingest
```

## Run API

```powershell
py -m uvicorn app.api:app --reload
```

The API uses the same PostgreSQL environment variables as the collector.

## Validate Before Running

From the repository root:

```powershell
py -m pytest -v
py -m compileall app tests
```

For the currently formatted Phase 6 files:

```powershell
py -m ruff check app/ingest.py app/repository.py tests/test_ingest_state.py tests/test_repository.py
py -m ruff format --check app/ingest.py app/repository.py tests/test_ingest_state.py tests/test_repository.py
```

## Environment Variables

The collector and API read PostgreSQL settings through `app/config.py`.

Common values:

```powershell
$env:PGHOST="localhost"
$env:PGPORT="5432"
$env:PGDATABASE="sysmon_lab"
$env:PGUSER="postgres"
$env:PGPASSWORD="your_postgres_password"
```

Collector settings:

```powershell
$env:COLLECTOR_POLL_SECONDS="5"
$env:COLLECTOR_BATCH_SIZE="100"
$env:COLLECTOR_STATE_FILE="collector_state.json"
```

To isolate one source:

```powershell
$env:COLLECTOR_SOURCES="health_metrics"
py -u -m app.ingest
```

Restore default sources:

```powershell
Remove-Item Env:COLLECTOR_SOURCES
```

## Permissions

Some Windows Event Log channels require elevated permissions. If Security logs fail with access denied, run the collector as administrator or add the collector account to the Event Log Readers group.
