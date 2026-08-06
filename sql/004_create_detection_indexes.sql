CREATE INDEX IF NOT EXISTS idx_detection_findings_rule
    ON detection_findings(rule_id, rule_version);

CREATE INDEX IF NOT EXISTS idx_detection_findings_severity
    ON detection_findings(severity);

CREATE INDEX IF NOT EXISTS idx_detection_findings_host
    ON detection_findings(source_host);

CREATE INDEX IF NOT EXISTS idx_detection_findings_source
    ON detection_findings(source_type);

CREATE INDEX IF NOT EXISTS idx_detection_findings_event
    ON detection_findings(event_id);

CREATE INDEX IF NOT EXISTS idx_detection_findings_event_time
    ON detection_findings(event_time);

CREATE INDEX IF NOT EXISTS idx_detection_findings_evaluated_at
    ON detection_findings(evaluated_at);