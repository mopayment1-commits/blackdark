CREATE TABLE IF NOT EXISTS data_provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    ingestion_run_id UUID REFERENCES ingestion_runs(id),
    target_table VARCHAR(64) NOT NULL,
    target_record_id BIGINT NOT NULL,
    source_endpoint VARCHAR(255) NOT NULL,
    request_headers JSONB DEFAULT '{}',
    response_status INTEGER,
    response_size_bytes INTEGER,
    raw_response_hash VARCHAR(64),
    parsed_at TIMESTAMPTZ DEFAULT NOW(),
    parser_version VARCHAR(16) DEFAULT '1.0.0'
);

CREATE INDEX IF NOT EXISTS idx_provenance_run
    ON data_provenance(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_provenance_target
    ON data_provenance(target_table, target_record_id);
