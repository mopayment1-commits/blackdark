CREATE TABLE IF NOT EXISTS de_failure_misses (
    id BIGSERIAL PRIMARY KEY,
    failure_type VARCHAR(64) NOT NULL CHECK (failure_type IN ('miss', 'false_positive', 'ingestion_error')),
    prediction_id VARCHAR(64),
    signal_id VARCHAR(64),
    symbol VARCHAR(32),
    error_message TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_de_failure_misses_type
    ON de_failure_misses(failure_type, created_at DESC);
