-- TEAS P0 production temporal spine persistence (Wave 01 extension)

CREATE TABLE IF NOT EXISTS te_canonical_events (
    event_id VARCHAR(64) PRIMARY KEY,
    entity_key VARCHAR(256) NOT NULL,
    event_type VARCHAR(128) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}',
    observation JSONB NOT NULL,
    provenance JSONB NOT NULL,
    record_version VARCHAR(64) NOT NULL,
    correction_or_revision_reference VARCHAR(64),
    conflict_metadata JSONB,
    idempotency_key VARCHAR(128) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_te_canonical_events_entity
    ON te_canonical_events(entity_key, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_te_canonical_events_type
    ON te_canonical_events(event_type, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_te_canonical_events_available
    ON te_canonical_events((observation->'available_at'->>'value'));

CREATE TABLE IF NOT EXISTS te_evidence_records (
    evidence_id VARCHAR(64) PRIMARY KEY,
    evidence_class VARCHAR(64) NOT NULL,
    producer VARCHAR(128) NOT NULL,
    record_payload JSONB NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    source_table VARCHAR(64),
    source_record_id VARCHAR(64),
    immutable BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_te_evidence_records_class
    ON te_evidence_records(evidence_class, created_at DESC);

CREATE TABLE IF NOT EXISTS te_forward_shadow_receipts (
    receipt_id VARCHAR(64) PRIMARY KEY,
    prediction_id VARCHAR(64) NOT NULL,
    subject_identity VARCHAR(256) NOT NULL,
    receipt_payload JSONB NOT NULL,
    payload_hash VARCHAR(64) NOT NULL,
    evidence_class VARCHAR(64) NOT NULL DEFAULT 'FORWARD_SHADOW',
    issued_at TIMESTAMPTZ NOT NULL,
    immutable BOOLEAN NOT NULL DEFAULT true,
    idempotency_key VARCHAR(128) UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_te_forward_shadow_subject
    ON te_forward_shadow_receipts(subject_identity, issued_at DESC);

CREATE TABLE IF NOT EXISTS te_forward_shadow_corrections (
    correction_id VARCHAR(64) PRIMARY KEY,
    receipt_id VARCHAR(64) NOT NULL REFERENCES te_forward_shadow_receipts(receipt_id),
    correction_payload JSONB NOT NULL,
    provenance JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_te_forward_shadow_corrections_receipt
    ON te_forward_shadow_corrections(receipt_id, created_at DESC);

CREATE TABLE IF NOT EXISTS te_contamination_registry (
    entry_id VARCHAR(64) PRIMARY KEY,
    dataset_id VARCHAR(128) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,
    window_end TIMESTAMPTZ NOT NULL,
    usage_purpose VARCHAR(64) NOT NULL,
    model_version VARCHAR(128),
    config_version VARCHAR(128),
    dataset_version VARCHAR(128),
    exposure_count INTEGER NOT NULL DEFAULT 1,
    contamination_state VARCHAR(32) NOT NULL DEFAULT 'clean',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (dataset_id, window_start, window_end, usage_purpose, model_version, config_version, dataset_version)
);

CREATE INDEX IF NOT EXISTS idx_te_contamination_dataset
    ON te_contamination_registry(dataset_id, window_start, window_end);

CREATE TABLE IF NOT EXISTS te_walk_forward_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    dataset_id VARCHAR(128) NOT NULL,
    model_version VARCHAR(128) NOT NULL,
    config_version VARCHAR(128) NOT NULL,
    dataset_version VARCHAR(128) NOT NULL,
    train_start TIMESTAMPTZ NOT NULL,
    train_end TIMESTAMPTZ NOT NULL,
    eval_start TIMESTAMPTZ NOT NULL,
    eval_end TIMESTAMPTZ NOT NULL,
    purge_gap_seconds INTEGER NOT NULL DEFAULT 0,
    embargo_gap_seconds INTEGER NOT NULL DEFAULT 0,
    frozen BOOLEAN NOT NULL DEFAULT true,
    provenance JSONB NOT NULL DEFAULT '{}',
    result_payload JSONB,
    contamination_checked BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_te_walk_forward_dataset
    ON te_walk_forward_runs(dataset_id, eval_start, eval_end);

CREATE TABLE IF NOT EXISTS te_reality_anchor_observations (
    observation_id VARCHAR(64) PRIMARY KEY,
    anchor_id VARCHAR(128) NOT NULL,
    receipt_id VARCHAR(64),
    forward_time_passage_verified BOOLEAN NOT NULL DEFAULT false,
    simulated_time_used BOOLEAN NOT NULL DEFAULT true,
    live_data_required BOOLEAN NOT NULL DEFAULT true,
    external_evidence_pending BOOLEAN NOT NULL DEFAULT true,
    external_gate_requirement_id VARCHAR(32),
    observation_payload JSONB NOT NULL DEFAULT '{}',
    observed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_te_reality_anchor_anchor
    ON te_reality_anchor_observations(anchor_id, observed_at DESC);

CREATE TABLE IF NOT EXISTS te_spine_runs (
    run_id VARCHAR(64) PRIMARY KEY,
    pipeline_stage VARCHAR(64) NOT NULL,
    status VARCHAR(32) NOT NULL,
    input_idempotency_key VARCHAR(128),
    event_id VARCHAR(64),
    evidence_id VARCHAR(64),
    receipt_id VARCHAR(64),
    error_code VARCHAR(64),
    observability JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_te_spine_runs_stage
    ON te_spine_runs(pipeline_stage, created_at DESC);
