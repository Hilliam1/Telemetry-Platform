# Database Architecture

The platform uses PostgreSQL as the telemetry storage backend.

## Current Tables

### `log_events`

Stores normalized Windows event records.

Expected fields:

- `source_host`
- `source_type`
- `provider_name`
- `event_id`
- `event_record_id`
- `severity`
- `time_created`
- `message`
- `raw_data`

### `process_events`

Stores structured process creation events from Sysmon Event ID 1.

Expected fields:

- `source_host`
- `process_guid`
- `process_id`
- `image`
- `command_line`
- `parent_image`
- `parent_command_line`
- `user_name`
- `sha256`
- `created_at`

### `host_metrics`

Stores host health metrics.

Expected fields:

- `host_name`
- `cpu_percent`
- `memory_percent`
- `disk_percent`
- `boot_time`

### `collector_runs`

Stores collector execution status.

Expected fields:

- `source_host`
- `status`
- `events_inserted`
- `started_at`
- `error_message`

## Persistence Ownership

Collector persistence SQL lives in `app/repository.py`.

`TelemetryRepository` inserts rows into:

- `log_events`
- `process_events`
- `host_metrics`
- `collector_runs`

`TelemetryRepository` does not commit or roll back transactions. `app/ingest.py` controls transaction boundaries so event rows and checkpoint updates remain ordered safely.

## Transaction Ordering

For Windows event ingestion, the safe order is:

```text
stage log and process rows
-> commit PostgreSQL transaction
-> update collector state
-> save collector state file
```

This prevents the collector from advancing its checkpoint when database writes fail.
