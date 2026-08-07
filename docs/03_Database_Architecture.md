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

### `detection_findings`

Stores deterministic detection findings produced from normalized Windows
events.

Expected fields:

- `finding_uuid`
- `rule_id`
- `rule_version`
- `title`
- `severity`
- `source_host`
- `source_type`
- `event_id`
- `event_record_id`
- `event_time`
- `evaluated_at`
- `explanation`
- `investigation_steps`
- `evidence`
- `tags`

### `correlation_matches`

Stores deterministic correlation matches produced from detection findings.

Expected fields:

- `correlation_uuid`
- `correlation_key`
- `rule_id`
- `rule_version`
- `title`
- `severity`
- `source_host`
- `first_event_time`
- `last_event_time`
- `matched_finding_ids`
- `matched_detection_rule_ids`
- `explanation`
- `investigation_steps`
- `evidence`
- `tags`

### `risk_assessments`

Stores deterministic risk assessments produced from correlation matches.

Expected fields:

- `assessment_uuid`
- `correlation_uuid`
- `correlation_rule_id`
- `score`
- `level`
- `base_score`
- `contributions`
- `source_host`
- `first_event_time`
- `last_event_time`
- `assessed_at`
- `explanation`
- `evidence`

### `alerts`

Stores operator-facing alerts produced from risk assessments.

Expected fields:

- `alert_uuid`
- `assessment_uuid`
- `correlation_uuid`
- `correlation_rule_id`
- `title`
- `risk_score`
- `risk_level`
- `status`
- `source_host`
- `first_event_time`
- `last_event_time`
- `created_at`
- `summary`
- `evidence`

## Persistence Ownership

Collector persistence SQL lives in `app/repository.py`.

`TelemetryRepository` inserts rows into:

- `log_events`
- `process_events`
- `host_metrics`
- `collector_runs`

Detection finding persistence SQL lives in `app/detection/repository.py`.

`DetectionRepository` inserts rows into:

- `detection_findings`

Intelligence persistence SQL lives in dedicated repositories:

- `app/correlation/repository.py` inserts `correlation_matches`
- `app/risk/repository.py` inserts `risk_assessments`
- `app/alerts/repository.py` inserts `alerts`

Repositories do not commit or roll back transactions. Source handlers control
source-level transaction boundaries, and `app/collector.py` controls
collector-run transaction boundaries. Windows event handlers still commit
database rows before advancing checkpoint state.

## Transaction Ordering

For Windows event ingestion, the safe order is:

```text
stage log, process, and detection finding rows
-> commit PostgreSQL transaction
-> update collector state
-> save collector state file
```

This prevents the collector from advancing its checkpoint when database writes
fail. If detection finding persistence fails, the source transaction rolls back
with the raw event and process rows.

Phase 16 connects historical detection lookup to the live Windows source
transaction. The intelligence service can query previously committed findings
and newly staged findings on the same PostgreSQL connection before the source
transaction commits.

Correlation deduplication is handled by `correlation_key`, a stable SHA-256
fingerprint of the correlation rule identity, host, event window, and matched
finding IDs. The database enforces uniqueness for non-null keys.
