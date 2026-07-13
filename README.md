# Enterprise Telemetry Platform

Enterprise Telemetry Platform is a Python-based security telemetry project for collecting, normalizing, and storing Windows host events for analysis.

It is designed as an extensible platform for collecting, normalizing, storing, and querying system, security, and performance data across Windows, Linux, Proxmox, and future infrastructure.

The current version focuses on Windows Event Log and Sysmon collection, PostgreSQL storage, process event extraction, collector state tracking, host health metrics, and a small FastAPI query service.

## Current Features

- Windows System, Application, Security, PowerShell, Defender, Task Scheduler, and Sysmon ingestion
- Sysmon Event ID 1 process creation parsing
- PostgreSQL-backed event storage
- Collector run tracking
- Local state file support to avoid reprocessing old events
- Optional host metrics with `psutil`
- Environment-based configuration
- SQL schema, index, and starter query files
- FastAPI endpoints for logs, metrics, search, and event counts

## Current Architecture

```text
Windows Event Logs
        |
        v
Collector Layer
        |
        v
Parsing and Normalization
        |
        v
PostgreSQL Database
        |
        v
FastAPI Query Service
```

## Target Architecture

```text
Windows, Linux, Proxmox, and Future Sources
        |
        v
Collector Layer
        |
        v
Normalization Layer
        |
        v
PostgreSQL Database
        |
        v
REST API
        |
        v
Dashboard and Detection Layer
```

## Repository Layout

```text
Telemetry-Platform/
|-- app/
|   |-- api.py
|   `-- ingest.py
|-- sql/
|   |-- 001_create_tables.sql
|   |-- 002_create_indexes.sql
|   `-- basic_queries.sql
|-- docs/
|   |-- adr/
|   |-- 00_Project_Overview.md
|   |-- 01_System_Architecture.md
|   |-- 02_Ingestion_Layer.md
|   |-- 03_Database_Architecture.md
|   |-- 04_API_Reference.md
|   |-- 05_SQL_Guide.md
|   |-- 06_Event_Parsing.md
|   |-- 07_Deployment.md
|   `-- 08_Troubleshooting.md
|-- diagrams/
|-- screenshots/
|-- tests/
|-- requirements.txt
|-- .env.example
|-- CHANGELOG.md
|-- ROADMAP.md
|-- CONTRIBUTING.md
`-- README.md
```

## Quick Start

1. Install Python dependencies.

```powershell
pip install -r requirements.txt
```

2. Create a local environment file.

```powershell
copy .env.example .env
```

3. Update `.env` with your PostgreSQL credentials.

4. Run the collector.

```powershell
python app\ingest.py
```

5. Run the API.

```powershell
uvicorn app.api:app --reload
```

## Documentation

The `docs/` directory is written like an engineering manual. It explains the project goals, architecture, ingestion logic, database design, event parsing strategy, deployment process, and troubleshooting workflow.

For a beginner-friendly explanation of the collector code, start with `docs/breakdown.md`.

## Status

This project is in early development. The current milestone is a working Windows telemetry collector, a basic API, reproducible SQL setup files, professional documentation, and a clean foundation for future dashboard, Linux, Proxmox, and Wazuh integrations.
