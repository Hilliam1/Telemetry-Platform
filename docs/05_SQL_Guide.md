# SQL Guide

The repository includes starter SQL files in `sql/`.

- `001_create_tables.sql` creates the initial telemetry tables.
- `002_create_indexes.sql` adds query indexes.
- `003_create_detection_findings.sql` creates the durable detection findings table.
- `004_create_detection_indexes.sql` adds detection finding query indexes.
- `005_create_correlation_matches.sql` creates the durable correlation matches table.
- `006_create_risk_assessments.sql` creates the durable risk assessments table.
- `007_create_alerts.sql` creates the durable alerts table.
- `008_create_intelligence_indexes.sql` adds intelligence-layer indexes.
- `009_add_correlation_deduplication.sql` adds stable correlation deduplication keys.
- `010_add_detection_finding_deduplication.sql` adds stable detection finding deduplication for findings tied to Event Record IDs.
- `basic_queries.sql` contains common operational and analysis queries.

Apply the numbered SQL files in order:

```powershell
psql -U postgres -d sysmon_lab -f .\sql\001_create_tables.sql
psql -U postgres -d sysmon_lab -f .\sql\002_create_indexes.sql
psql -U postgres -d sysmon_lab -f .\sql\003_create_detection_findings.sql
psql -U postgres -d sysmon_lab -f .\sql\004_create_detection_indexes.sql
psql -U postgres -d sysmon_lab -f .\sql\005_create_correlation_matches.sql
psql -U postgres -d sysmon_lab -f .\sql\006_create_risk_assessments.sql
psql -U postgres -d sysmon_lab -f .\sql\007_create_alerts.sql
psql -U postgres -d sysmon_lab -f .\sql\008_create_intelligence_indexes.sql
psql -U postgres -d sysmon_lab -f .\sql\009_add_correlation_deduplication.sql
psql -U postgres -d sysmon_lab -f .\sql\010_add_detection_finding_deduplication.sql
```

## Latest Events

```sql
SELECT *
FROM log_events
ORDER BY time_created DESC
LIMIT 50;
```

## Event Counts by Source

```sql
SELECT source_type, COUNT(*) AS event_count
FROM log_events
GROUP BY source_type
ORDER BY event_count DESC;
```

## Event Counts by Provider

```sql
SELECT provider_name, COUNT(*) AS event_count
FROM log_events
GROUP BY provider_name
ORDER BY event_count DESC;
```

## Recent Process Events

```sql
SELECT source_host, image, command_line, user_name, created_at
FROM process_events
ORDER BY created_at DESC
LIMIT 50;
```

## Recent Detection Findings

```sql
SELECT
    finding_uuid,
    rule_id,
    rule_version,
    title,
    severity,
    source_host,
    event_id,
    event_record_id,
    event_time,
    evaluated_at,
    evidence,
    tags
FROM detection_findings
ORDER BY created_at DESC
LIMIT 20;
```

## Recent Correlation Matches

```sql
SELECT
    correlation_uuid,
    rule_id,
    rule_version,
    title,
    severity,
    source_host,
    first_event_time,
    last_event_time,
    matched_finding_ids,
    evidence
FROM correlation_matches
ORDER BY created_at DESC
LIMIT 20;
```

## Recent Risk Assessments

```sql
SELECT
    assessment_uuid,
    correlation_uuid,
    correlation_rule_id,
    score,
    level,
    source_host,
    assessed_at,
    contributions,
    evidence
FROM risk_assessments
ORDER BY created_at DESC
LIMIT 20;
```

## Recent Alerts

```sql
SELECT
    alert_uuid,
    assessment_uuid,
    correlation_uuid,
    title,
    risk_score,
    risk_level,
    status,
    source_host,
    created_at
FROM alerts
ORDER BY inserted_at DESC
LIMIT 20;
```

## Collector Health

```sql
SELECT *
FROM collector_runs
ORDER BY started_at DESC
LIMIT 20;
```
