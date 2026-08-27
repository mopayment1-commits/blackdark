CREATE TABLE IF NOT EXISTS de_evidence_store (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    evidence_id VARCHAR(64) NOT NULL UNIQUE,
    record_type VARCHAR(64) NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL,
    immutable BOOLEAN DEFAULT true,
    source_table VARCHAR(64),
    source_record_id VARCHAR(64),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_de_evidence_store_type
    ON de_evidence_store(record_type, created_at DESC);
