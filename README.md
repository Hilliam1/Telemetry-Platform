# Enterprise Telemetry Platform

Enterprise Telemetry Platform is a Python-based security telemetry project for collecting, normalizing, and storing Windows host events for analysis.

It is designed as an extensible platform for collecting, normalizing, storing, and querying system, security, and performance data across Windows, Linux, Proxmox, and future infrastructure.

The current version focuses on Windows Event Log and Sysmon collection, PostgreSQL storage, process event extraction, collector state tracking, host health metrics, deterministic detection finding persistence, persistable correlation matches, persistable risk assessments, persistable alerts, and a small FastAPI query service.

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
- Deterministic detection rules with PostgreSQL-backed finding persistence
- Deterministic correlation of detection findings with PostgreSQL persistence support
- Deterministic risk assessment for correlation matches with PostgreSQL persistence support
- Deterministic alert generation from risk assessments with PostgreSQL persistence support

## Current Architecture

Process startup:

```text
app.ingest
        |
        v
Collector Factory
        |
        v
Collector Service
        |
        v
Source Registry
        |
        v
Source Handler Registry
```

Windows event path:

```text
Windows Event Logs
        |
        v
Windows Event Reader
        |
        v
Windows Event Parser
        |
        v
Normalized Event
   |             |
   v             v
Telemetry     Detection
Repository     Engine
   |             |
   |             v
   |      Detection Repository
   |             |
   +------v------+
      PostgreSQL
        COMMIT
```

Host health metrics follow a parallel path:

```text
Collector Service
        |
        v
Source Handler Registry
        |
        v
HostMetricsCollector
        |
        v
Persistence Repository
        |
        v
PostgreSQL Database
```

Current intelligence chain:

```text
Telemetry
        |
        v
Normalization
        |
        v
Detection
        |
        v
Correlation
        |
        v
Risk Assessment
        |
        v
Alert Policy
        |
        v
Alert
```

Current intelligence persistence boundary:

```text
Normalized Event
        |
        +------------------------+
        |                        |
        v                        v
Telemetry Persistence        Detection
                                 |
                                 v
                         Detection Persistence
                                 |
                                 v
                            Correlation
                                 |
                                 v
                       Correlation Persistence
                                 |
                                 v
                               Risk
                                 |
                                 v
                         Risk Persistence
                                 |
                                 v
                              Alert
                                 |
                                 v
                         Alert Persistence
```

## Planned Target Architecture

```text
Windows, Linux, Network, Cloud, and Future Sources
        |
        v
Collector / Integration Layer
        |
        v
Normalization
        |
        +--------------------+
        |                    |
        v                    v
Telemetry Persistence    Detection
                             |
                             v
                         Correlation
                             |
                             v
                           Risk
                             |
                             v
                           Alert
                             |
                             v
                    Intelligence Persistence
                             |
                             v
                         REST API
                             |
                    +--------+--------+
                    |                 |
                    v                 v
                Dashboard        Notifications
```

## Repository Layout

```text
Telemetry-Platform/
|-- app/
|   |-- __init__.py
|   |-- api.py
|   |-- alerts/
|   |   |-- __init__.py
|   |   |-- engine.py
|   |   |-- models.py
|   |   |-- policy.py
|   |   `-- repository.py
|   |-- collector.py
|   |-- collector_factory.py
|   |-- config.py
|   |-- database.py
|   |-- correlation/
|   |   |-- __init__.py
|   |   |-- engine.py
|   |   |-- models.py
|   |   |-- repository.py
|   |   `-- rules.py
|   |-- detection/
|   |   |-- __init__.py
|   |   |-- engine.py
|   |   |-- models.py
|   |   |-- repository.py
|   |   `-- rules.py
|   |-- health_metrics.py
|   |-- ingest.py
|   |-- repository.py
|   |-- risk/
|   |   |-- __init__.py
|   |   |-- engine.py
|   |   |-- models.py
|   |   |-- policy.py
|   |   |-- providers.py
|   |   `-- repository.py
|   |-- source_handlers.py
|   |-- sources.py
|   |-- state.py
|   |-- windows_reader.py
|   `-- parsers/
|       |-- __init__.py
|       `-- windows_event_parser.py
|-- sql/
|   |-- 001_create_tables.sql
|   |-- 002_create_indexes.sql
|   |-- 003_create_detection_findings.sql
|   |-- 004_create_detection_indexes.sql
|   |-- 005_create_correlation_matches.sql
|   |-- 006_create_risk_assessments.sql
|   |-- 007_create_alerts.sql
|   |-- 008_create_intelligence_indexes.sql
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
|   |-- 08_Troubleshooting.md
|   |-- 09_Architecture_Decisions.md
|   |-- 10_Detection_Engine.md
|   |-- 11_Detection_Persistence.md
|   |-- 12_Correlation_Engine.md
|   |-- 13_Risk_Engine.md
|   |-- 14_Alert_Engine.md
|   `-- 15_Intelligence_Persistence.md
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
py -m app.ingest
```

5. Run the API.

```powershell
py -m uvicorn app.api:app --reload
```

## Documentation

The `docs/` directory is written like an engineering manual. It explains the project goals, architecture, ingestion logic, database design, event parsing strategy, deployment process, and troubleshooting workflow.

For a beginner-friendly explanation of the collector code, start with `docs/breakdown.md`.

## Status

This project is in early development. The current milestone is a working Windows telemetry collector, a basic API, reproducible SQL setup files, professional documentation, and a clean foundation for future dashboard, Linux, Proxmox, and Wazuh integrations.
