CREATE TABLE IF NOT EXISTS de_signal_registry (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    signal_id VARCHAR(64) NOT NULL UNIQUE,
    symbol VARCHAR(32) NOT NULL,
    signal_type VARCHAR(64) NOT NULL,
    direction VARCHAR(16) NOT NULL CHECK (direction IN ('buy', 'sell', 'neutral')),
    confidence DECIMAL(8,4),
    features_hash VARCHAR(64),
    ingestion_run_id UUID REFERENCES ingestion_runs(id),
    model_version VARCHAR(32),
    provenance_hash VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_de_signal_registry_symbol_time
    ON de_signal_registry(symbol, created_at DESC);
