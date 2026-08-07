CREATE TABLE IF NOT EXISTS correlation_matches (
    id BIGSERIAL PRIMARY KEY,

    correlation_uuid UUID NOT NULL UNIQUE,

    rule_id TEXT NOT NULL,
    rule_version INTEGER NOT NULL,

    title TEXT NOT NULL,
    severity TEXT NOT NULL,

    source_host TEXT NOT NULL,

    first_event_time TIMESTAMP NOT NULL,
    last_event_time TIMESTAMP NOT NULL,

    matched_finding_ids UUID[] NOT NULL,
    matched_detection_rule_ids TEXT[] NOT NULL,

    explanation TEXT NOT NULL,
    investigation_steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,
    tags TEXT[] NOT NULL DEFAULT '{}',

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_correlation_rule_version_positive
        CHECK (rule_version > 0),

    CONSTRAINT ck_correlation_severity
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
