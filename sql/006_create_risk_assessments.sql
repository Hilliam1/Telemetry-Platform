CREATE TABLE IF NOT EXISTS risk_assessments (
    id BIGSERIAL PRIMARY KEY,

    assessment_uuid UUID NOT NULL UNIQUE,

    correlation_uuid UUID NOT NULL,

    correlation_rule_id TEXT NOT NULL,

    score INTEGER NOT NULL,
    level TEXT NOT NULL,
    base_score INTEGER NOT NULL,

    contributions JSONB NOT NULL DEFAULT '[]'::jsonb,

    source_host TEXT NOT NULL,

    first_event_time TIMESTAMP NOT NULL,
    last_event_time TIMESTAMP NOT NULL,
    assessed_at TIMESTAMP NOT NULL,

    explanation TEXT NOT NULL,
    evidence JSONB NOT NULL DEFAULT '{}'::jsonb,

    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT ck_risk_score
        CHECK (score BETWEEN 0 AND 100),

    CONSTRAINT ck_risk_base_score
        CHECK (base_score BETWEEN 0 AND 100),

    CONSTRAINT ck_risk_level
        CHECK (
            level IN (
                'informational',
                'low',
                'medium',
                'high',
                'critical'
            )
        )
);
