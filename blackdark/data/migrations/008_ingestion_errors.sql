CREATE TABLE IF NOT EXISTS ingestion_errors (
    id BIGSERIAL PRIMARY KEY,
    ingestion_run_id UUID REFERENCES ingestion_runs(id),
    source_id INTEGER REFERENCES data_sources(id),
    error_type VARCHAR(64) NOT NULL,
    error_message TEXT NOT NULL,
    endpoint VARCHAR(255),
    retry_count INTEGER DEFAULT 0,
    resolved BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_errors_run
    ON ingestion_errors(ingestion_run_id);
CREATE INDEX IF NOT EXISTS idx_errors_unresolved
    ON ingestion_errors(resolved) WHERE resolved = false;
