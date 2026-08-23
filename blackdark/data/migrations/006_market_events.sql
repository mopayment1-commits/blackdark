CREATE TABLE IF NOT EXISTS market_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    severity VARCHAR(16) NOT NULL,
    symbol VARCHAR(32),
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    description TEXT,
    price_change_pct DECIMAL(12,6),
    volume_spike_multiplier DECIMAL(8,2),
    source_links JSONB DEFAULT '[]',
    detected_by VARCHAR(64) DEFAULT 'manual',
    confirmed BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_market_events_type_time
    ON market_events(event_type, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_market_events_severity
    ON market_events(severity);
