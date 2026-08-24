CREATE TABLE IF NOT EXISTS ohlcv_data (
    id BIGSERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(id),
    ingestion_run_id UUID REFERENCES ingestion_runs(id),
    symbol VARCHAR(32) NOT NULL,
    quote_asset VARCHAR(16) NOT NULL,
    interval VARCHAR(8) NOT NULL,
    open_time TIMESTAMPTZ NOT NULL,
    close_time TIMESTAMPTZ NOT NULL,
    open_price DECIMAL(36,18) NOT NULL,
    high_price DECIMAL(36,18) NOT NULL,
    low_price DECIMAL(36,18) NOT NULL,
    close_price DECIMAL(36,18) NOT NULL,
    volume DECIMAL(36,18) NOT NULL,
    quote_volume DECIMAL(36,18),
    trades_count INTEGER,
    taker_buy_base_volume DECIMAL(36,18),
    taker_buy_quote_volume DECIMAL(36,18),
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    provenance_hash VARCHAR(64),
    UNIQUE(source_id, symbol, interval, open_time)
);

CREATE INDEX IF NOT EXISTS idx_ohlcv_symbol_interval_time
    ON ohlcv_data(symbol, interval, open_time DESC);
CREATE INDEX IF NOT EXISTS idx_ohlcv_ingestion_run
    ON ohlcv_data(ingestion_run_id);
