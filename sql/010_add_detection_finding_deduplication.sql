CREATE UNIQUE INDEX IF NOT EXISTS
    uq_detection_findings_source_rule
ON detection_findings (
    rule_id,
    rule_version,
    source_host,
    source_type,
    event_id,
    event_record_id
)
WHERE event_record_id IS NOT NULL;
