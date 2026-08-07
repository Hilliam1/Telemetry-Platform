ALTER TABLE correlation_matches
    ADD COLUMN IF NOT EXISTS correlation_key TEXT;

CREATE UNIQUE INDEX IF NOT EXISTS
    uq_correlation_matches_key
ON correlation_matches(correlation_key)
WHERE correlation_key IS NOT NULL;
