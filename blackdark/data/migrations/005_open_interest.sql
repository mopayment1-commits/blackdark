CREATE TABLE IF NOT EXISTS open_interest (
    id BIGSERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(id),
    ingestion_run_id UUID REFERENCES ingestion_runs(id),
    symbol VARCHAR(32) NOT NULL,
    oi_time TIMESTAMPTZ NOT NULL,
    open_interest DECIMAL(36,18) NOT NULL,
    open_interest_value DECIMAL(36,18),
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id, symbol, oi_time)
);

CREATE INDEX IF NOT EXISTS idx_oi_symbol_time
    ON open_interest(symbol, oi_time DESC);
