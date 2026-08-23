CREATE TABLE IF NOT EXISTS market_snapshots (
    id BIGSERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES data_sources(id),
    ingestion_run_id UUID REFERENCES ingestion_runs(id),
    coin_id VARCHAR(64) NOT NULL,
    symbol VARCHAR(16) NOT NULL,
    name VARCHAR(128),
    current_price DECIMAL(36,18),
    market_cap DECIMAL(36,2),
    total_volume DECIMAL(36,2),
    price_change_24h DECIMAL(12,6),
    price_change_pct_24h DECIMAL(12,6),
    circulating_supply DECIMAL(36,18),
    total_supply DECIMAL(36,18),
    max_supply DECIMAL(36,18),
    ath DECIMAL(36,18),
    ath_change_pct DECIMAL(12,6),
    ath_date TIMESTAMPTZ,
    atl DECIMAL(36,18),
    atl_change_pct DECIMAL(12,6),
    atl_date TIMESTAMPTZ,
    last_updated TIMESTAMPTZ,
    fetched_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(source_id, coin_id, fetched_at)
);

CREATE INDEX IF NOT EXISTS idx_market_snapshots_coin_fetched
    ON market_snapshots(coin_id, fetched_at DESC);
