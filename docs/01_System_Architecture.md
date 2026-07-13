# System Architecture

The platform is designed as a layered telemetry pipeline.

```text
Windows Hosts
    |
    v
Collector Layer
    |
    v
Parsing and Normalization Layer
    |
    v
PostgreSQL Database
    |
    v
REST API
    |
    v
Dashboard and Analysis Layer
```

## Collector Layer

The collector reads events from Windows Event Log channels such as System, Application, Security, PowerShell, Defender, Task Scheduler, and Sysmon.

## Parsing and Normalization Layer

Windows events are rendered as XML. The collector parses that XML into Python dictionaries and stores both raw and structured versions.

## Database Layer

PostgreSQL stores raw events, process events, host metrics, and collector run records.

## API Layer

The planned API layer will expose telemetry through queryable endpoints for dashboards, search, and future detection workflows.

## Dashboard Layer

The planned dashboard will show event trends, host activity, process creation, collector health, and investigation views.

