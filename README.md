# Enterprise Telemetry Platform

Enterprise Telemetry Platform is a Python-based security telemetry project for collecting, normalizing, and storing Windows host events for analysis.

The current version focuses on Windows Event Log and Sysmon collection, PostgreSQL storage, process event extraction, collector state tracking, and host health metrics.

## Current Features

- Windows System, Application, Security, PowerShell, Defender, Task Scheduler, and Sysmon ingestion
- Sysmon Event ID 1 process creation parsing
- PostgreSQL-backed event storage
- Collector run tracking
- Local state file support to avoid reprocessing old events
- Optional host metrics with `psutil`
- Environment-based configuration

## Architecture

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
API and Dashboard Layer
```

## Repository Layout

```text
Telemetry-Platform/
|-- app/
|   `-- ingest.py
|-- sql/
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

## Documentation

The `docs/` directory is written like an engineering manual. It explains the project goals, architecture, ingestion logic, database design, event parsing strategy, deployment process, and troubleshooting workflow.

For a beginner-friendly explanation of the collector code, start with `docs/breakdown.md`.

## Status

This project is in early development. The current milestone is a working Windows telemetry collector with professional documentation and a clean foundation for future API, dashboard, Linux, Proxmox, and Wazuh integrations.
