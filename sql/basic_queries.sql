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

-- Recent detection findings
SELECT
    finding_uuid,
    rule_id,
    rule_version,
    title,
    severity,
    source_host,
    source_type,
    event_id,
    event_record_id,
    event_time,
    evaluated_at,
    tags
FROM detection_findings
ORDER BY created_at DESC
LIMIT 50;

-- Detection finding counts by rule
SELECT
    rule_id,
    rule_version,
    title,
    severity,
    COUNT(*) AS finding_count
FROM detection_findings
GROUP BY
    rule_id,
    rule_version,
    title,
    severity
ORDER BY finding_count DESC;

-- Recent encoded PowerShell findings
SELECT
    finding_uuid,
    source_host,
    event_record_id,
    event_time,
    evidence
FROM detection_findings
WHERE rule_id = 'TP-WIN-SYSMON-0002'
ORDER BY event_time DESC
LIMIT 50;

-- Recent correlation matches
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
    matched_detection_rule_ids,
    tags
FROM correlation_matches
ORDER BY created_at DESC
LIMIT 50;

-- Correlation match counts by rule
SELECT
    rule_id,
    rule_version,
    title,
    severity,
    COUNT(*) AS match_count
FROM correlation_matches
GROUP BY
    rule_id,
    rule_version,
    title,
    severity
ORDER BY match_count DESC;

-- Recent risk assessments
SELECT
    assessment_uuid,
    correlation_uuid,
    correlation_rule_id,
    score,
    level,
    base_score,
    source_host,
    assessed_at,
    explanation
FROM risk_assessments
ORDER BY created_at DESC
LIMIT 50;

-- Highest risk assessments
SELECT
    assessment_uuid,
    correlation_uuid,
    correlation_rule_id,
    score,
    level,
    source_host,
    assessed_at,
    contributions
FROM risk_assessments
ORDER BY score DESC, assessed_at DESC
LIMIT 25;

-- Risk assessment counts by level
SELECT
    level,
    COUNT(*) AS assessment_count
FROM risk_assessments
GROUP BY level
ORDER BY assessment_count DESC;

-- Recent alerts
SELECT
    alert_uuid,
    assessment_uuid,
    correlation_uuid,
    correlation_rule_id,
    title,
    risk_score,
    risk_level,
    status,
    source_host,
    created_at
FROM alerts
ORDER BY inserted_at DESC
LIMIT 50;

-- Open alerts
SELECT
    alert_uuid,
    title,
    risk_score,
    risk_level,
    status,
    source_host,
    created_at,
    summary
FROM alerts
WHERE status IN ('new', 'acknowledged')
ORDER BY risk_score DESC, created_at DESC;

-- Alert counts by status
SELECT
    status,
    COUNT(*) AS alert_count
FROM alerts
GROUP BY status
ORDER BY alert_count DESC;

-- Alert counts by risk level
SELECT
    risk_level,
    COUNT(*) AS alert_count
FROM alerts
GROUP BY risk_level
ORDER BY alert_count DESC;

-- Alert investigation chain
SELECT
    a.alert_uuid,
    a.title AS alert_title,
    a.status,
    a.risk_score,
    a.risk_level,
    a.source_host,
    a.created_at AS alert_created_at,
    r.assessment_uuid,
    r.base_score,
    r.contributions,
    c.correlation_uuid,
    c.title AS correlation_title,
    c.matched_finding_ids
FROM alerts AS a
JOIN risk_assessments AS r
    ON r.assessment_uuid = a.assessment_uuid
JOIN correlation_matches AS c
    ON c.correlation_uuid = a.correlation_uuid
ORDER BY a.created_at DESC
LIMIT 25;

-- Intelligence activity by host
SELECT
    source_host,
    COUNT(*) AS alert_count,
    MAX(created_at) AS latest_alert_time,
    MAX(risk_score) AS highest_risk_score
FROM alerts
GROUP BY source_host
ORDER BY highest_risk_score DESC, alert_count DESC;

-- Verify Phase 15 intelligence tables exist
SELECT to_regclass('public.correlation_matches') AS correlation_matches;

SELECT to_regclass('public.risk_assessments') AS risk_assessments;

SELECT to_regclass('public.alerts') AS alerts;
