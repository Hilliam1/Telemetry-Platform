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
- Modular collector internals for configuration, database connections, state, reading, parsing, host metrics, and persistence

## Current Internal Modules

- `app/config.py` loads environment-based settings.
- `app/database.py` creates PostgreSQL connections.
- `app/ingest.py` coordinates collector execution.
- `app/windows_reader.py` reads rendered XML from Windows Event Logs.
- `app/parsers/windows_event_parser.py` parses and normalizes Windows event XML.
- `app/health_metrics.py` collects host-health snapshots.
- `app/repository.py` persists collector records using the orchestrator-controlled transaction.
- `app/state.py` manages checkpoint state.
- `app/api.py` exposes query endpoints.

## Future Scope

- Linux telemetry
- Proxmox telemetry
- Wazuh integration
- Detection rules
- Alerting
- Dashboard views
- Docker deployment
