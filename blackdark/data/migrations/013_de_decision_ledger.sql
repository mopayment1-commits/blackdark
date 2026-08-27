CREATE TABLE IF NOT EXISTS de_decision_ledger (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    decision_id VARCHAR(64) NOT NULL UNIQUE,
    prediction_id VARCHAR(64) NOT NULL,
    decision_action VARCHAR(16) NOT NULL CHECK (decision_action IN ('act', 'wait')),
    symbol VARCHAR(32) NOT NULL,
    rationale TEXT,
    evidence_hash VARCHAR(64),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_de_decision_ledger_prediction
    ON de_decision_ledger(prediction_id);
