CREATE TABLE IF NOT EXISTS de_outcome_evaluations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    prediction_id VARCHAR(64) NOT NULL,
    outcome VARCHAR(16) NOT NULL CHECK (outcome IN ('hit', 'miss', 'pending')),
    evaluated_at TIMESTAMPTZ DEFAULT NOW(),
    actual_price DECIMAL(36,18),
    predicted_direction VARCHAR(16),
    pnl_pct DECIMAL(12,6),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_de_outcome_eval_prediction
    ON de_outcome_evaluations(prediction_id, evaluated_at DESC);
