# Project Overview

Enterprise Telemetry Platform is a security engineering project for collecting endpoint telemetry, normalizing it, and storing it in a database for later search, analysis, dashboards, and detections.

## Purpose

The project starts with Windows telemetry because Windows Event Logs and Sysmon provide rich host activity data. The long-term goal is to support a broader lab and enterprise-style telemetry stack.

## Goals

- Collect Windows event telemetry reliably.
- Preserve raw event data for investigation.
- Extract important structured fields into query-friendly tables.
- Track collector health and execution history.
- Build toward an API, dashboard, detections, and multi-platform collectors.

## Current Scope

- Windows Event Log ingestion
- Sysmon ingestion
- PostgreSQL storage
- Process event parsing
- Host health metrics
- Collector state tracking
- FastAPI query service
- Deterministic detection finding persistence
- Deterministic in-memory correlation foundation
- Deterministic in-memory risk assessment foundation
- Modular collector internals for configuration, database connections, collector orchestration, dependency construction, state, reading, parsing, host metrics, source handlers, and persistence

## Current Internal Modules

- `app/config.py` loads environment-based settings.
- `app/database.py` creates PostgreSQL connections.
- `app/collector.py` coordinates collector execution.
- `app/collector_factory.py` constructs the collector and its dependencies.
- `app/ingest.py` configures logging and starts the collector process.
- `app/windows_reader.py` reads rendered XML from Windows Event Logs.
- `app/parsers/windows_event_parser.py` parses and normalizes Windows event XML.
- `app/health_metrics.py` collects host-health snapshots.
- `app/source_handlers.py` executes source-specific ingestion workflows.
- `app/correlation/` contains deterministic finding correlation models, rules, and evaluation.
- `app/detection/` contains deterministic rules, evaluation, and finding persistence.
- `app/risk/` contains deterministic risk models, policy, providers, and score aggregation.
- `app/repository.py` persists collector records using caller-controlled transactions.
- `app/sources.py` defines supported telemetry sources and dispatch categories.
- `app/state.py` manages checkpoint state.
- `app/api.py` exposes query endpoints.

## Future Scope

- Linux telemetry
- Proxmox telemetry
- Wazuh integration
- Correlation persistence, risk persistence, and detection API routes
- Alerting
- Dashboard views
- Docker deployment
