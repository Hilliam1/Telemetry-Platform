-- Recent logs
SELECT *
FROM log_events
ORDER BY inserted_at DESC
LIMIT 50;

-- Count logs by source type
SELECT source_type, COUNT(*)
FROM log_events
GROUP BY source_type
ORDER BY COUNT(*) DESC;

-- Count logs by provider
SELECT provider_name, COUNT(*)
FROM log_events
GROUP BY provider_name
ORDER BY COUNT(*) DESC;

-- Count logs by event ID
SELECT event_id, COUNT(*)
FROM log_events
GROUP BY event_id
ORDER BY COUNT(*) DESC;

-- Latest host metrics
SELECT *
FROM host_metrics
ORDER BY collected_at DESC
LIMIT 20;

-- High memory usage
SELECT *
FROM host_metrics
WHERE memory_percent > 80
ORDER BY collected_at DESC;

-- High disk usage
SELECT *
FROM host_metrics
WHERE disk_percent > 80
ORDER BY collected_at DESC;

-- Recent process events
SELECT
    source_host,
    image,
    command_line,
    parent_image,
    user_name,
    created_at
FROM process_events
ORDER BY inserted_at DESC
LIMIT 50;

-- Search PowerShell activity
SELECT *
FROM process_events
WHERE image ILIKE '%powershell%'
   OR command_line ILIKE '%powershell%'
ORDER BY created_at DESC;

-- Collector run history
SELECT *
FROM collector_runs
ORDER BY started_at DESC
LIMIT 50;

