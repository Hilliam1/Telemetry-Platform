CREATE TABLE IF NOT EXISTS detection_findings (
    id BIGSERIAL PRIMARY KEY,
    finding_uuid UUID NOT NULL UNIQUE,
    rule_id TEXT NOT NULL,
    rule_version INTEGER NOT NULL,
    title TEXT NOT NULL,
    severity TEXT NOT NULL,
    source_host TEXT NOT NULL,
    source_type TEXT NOT NULL,
    event_id BIGINT NOT NULL,
    event_record_id BIGINT,
    event_time TIMESTAMP NOT NULL,
    evaluated_at TIMESTAMP NOT NULL,
    explanation TEXT NOT NULL,
    investigation_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    tags TEXT[] NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_detection_rule_version_positive
        CHECK (rule_version > 0),

    CONSTRAINT ck_detection_severity
        CHECK (
            severity IN (
                'informational',
                'low',
                'medium',
                'high',
                'critical'
            )
        )
);