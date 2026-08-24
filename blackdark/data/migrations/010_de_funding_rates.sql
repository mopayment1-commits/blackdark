CREATE TABLE IF NOT EXISTS de_funding_rates (
    id BIGSERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(id),
    ingestion_run_id UUID REFERENCES ingestion_runs(id),
    symbol VARCHAR(32) NOT NULL,
    funding_time TIMESTAMPTZ NOT NULL,
    funding_rate DECIMAL(24,12) NOT NULL,
    mark_price DECIMAL(36,18),
    index_price DECIMAL(36,18),
    realized_rate DECIMAL(24,12),
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id, symbol, funding_time)
);

CREATE INDEX IF NOT EXISTS idx_de_funding_symbol_time
    ON de_funding_rates(symbol, funding_time DESC);
