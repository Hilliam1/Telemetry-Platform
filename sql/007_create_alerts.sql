CREATE TABLE IF NOT EXISTS alerts (
    id BIGSERIAL PRIMARY KEY,

    alert_uuid UUID NOT NULL UNIQUE,

    assessment_uuid UUID NOT NULL,
    correlation_uuid UUID NOT NULL,
    correlation_rule_id TEXT NOT NULL,

    title TEXT NOT NULL,

    risk_score INTEGER NOT NULL,
    risk_level TEXT NOT NULL,

    status TEXT NOT NULL,

    source_host TEXT NOT NULL,

    first_event_time TIMESTAMP NOT NULL,
    last_event_time TIMESTAMP NOT NULL,

    created_at TIMESTAMP NOT NULL,

    summary TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,

    inserted_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_alert_risk_score
        CHECK (risk_score BETWEEN 0 AND 100),

    CONSTRAINT ck_alert_risk_level
        CHECK (
            risk_level IN (
                'informational',
                'low',
                'medium',
                'high',
                'critical'
            )
        ),

    CONSTRAINT ck_alert_status
        CHECK (
            status IN (
                'new',
                'acknowledged',
                'resolved',
                'suppressed'
            )
        )
);
