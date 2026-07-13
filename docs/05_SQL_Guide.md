# SQL Guide

The repository includes starter SQL files in `sql/`.

- `001_create_tables.sql` creates the initial telemetry tables.
- `002_create_indexes.sql` adds query indexes.
- `basic_queries.sql` contains common operational and analysis queries.

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

## Collector Health

```sql
SELECT *
FROM collector_runs
ORDER BY started_at DESC
LIMIT 20;
```
