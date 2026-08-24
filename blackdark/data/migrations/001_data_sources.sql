CREATE TABLE IF NOT EXISTS data_sources (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(32) UNIQUE NOT NULL,
    name VARCHAR(64) NOT NULL,
    source_type VARCHAR(32) NOT NULL,
    base_url VARCHAR(255) NOT NULL,
    rate_limit_rps DECIMAL(4,2) DEFAULT 1.0,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
