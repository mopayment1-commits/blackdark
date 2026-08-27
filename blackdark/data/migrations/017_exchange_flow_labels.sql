-- D-09: Exchange flow wallet labels (expandable via admin)
CREATE TABLE IF NOT EXISTS exchange_flow_labels (
    address TEXT PRIMARY KEY,
    exchange TEXT NOT NULL,
    label_type TEXT NOT NULL DEFAULT 'hot',
    confidence REAL DEFAULT 0.9,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_exchange_flow_labels_exchange ON exchange_flow_labels (exchange);
