CREATE INDEX IF NOT EXISTS idx_correlation_rule
    ON correlation_matches(rule_id, rule_version);

CREATE INDEX IF NOT EXISTS idx_correlation_host
    ON correlation_matches(source_host);

CREATE INDEX IF NOT EXISTS idx_correlation_time
    ON correlation_matches(last_event_time);

CREATE INDEX IF NOT EXISTS idx_risk_correlation
    ON risk_assessments(correlation_uuid);

CREATE INDEX IF NOT EXISTS idx_risk_score
    ON risk_assessments(score);

CREATE INDEX IF NOT EXISTS idx_risk_level
    ON risk_assessments(level);

CREATE INDEX IF NOT EXISTS idx_risk_host
    ON risk_assessments(source_host);

CREATE INDEX IF NOT EXISTS idx_alert_status
    ON alerts(status);

CREATE INDEX IF NOT EXISTS idx_alert_risk_level
    ON alerts(risk_level);

CREATE INDEX IF NOT EXISTS idx_alert_host
    ON alerts(source_host);

CREATE INDEX IF NOT EXISTS idx_alert_created
    ON alerts(created_at);
