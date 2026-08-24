CREATE TABLE IF NOT EXISTS de_prediction_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id VARCHAR(64) NOT NULL UNIQUE,
    signal_id UUID REFERENCES de_signal_registry(id),
    symbol VARCHAR(32) NOT NULL,
    sealed_payload_hash VARCHAR(64) NOT NULL,
    sealed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    unlock_at TIMESTAMPTZ,
    model_version VARCHAR(32),
    direction VARCHAR(16),
    target_price DECIMAL(36,18),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_de_prediction_ledger_symbol
    ON de_prediction_ledger(symbol, sealed_at DESC);
