# Deployment

## Prerequisites

- Windows host
- Python 3
- PostgreSQL
- Sysmon
- Python dependencies from `requirements.txt`

## Install Dependencies

```powershell
pip install -r requirements.txt
```

## Configure Environment

```powershell
copy .env.example .env
```

Update `.env` with local PostgreSQL settings.

## Run Collector

```powershell
python app\ingest.py
```

## Run API

```powershell
uvicorn app.api:app --reload
```

The API uses the same PostgreSQL environment variables as the collector.

## Permissions

Some Windows Event Log channels require elevated permissions. If Security logs fail with access denied, run the collector as administrator or add the collector account to the Event Log Readers group.
