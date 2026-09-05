# Local Organized Data ETL — Feature #118 (Sprint 0)

## Role

Infrastructure foundation — **not** a user-facing marketing feature. Every market, on-chain, and user analytics surface depends on this pipeline.

## Stack

| Store | Purpose |
|-------|---------|
| **PostgreSQL** | Structured cleaned records (`etl_records`, `etl_job_runs`) |
| **InfluxDB** | Time-series metrics (prices, funding, liquidity) — 730-day retention |
| **Redis** | Hot query cache (≤1s SLA) |

## Pipeline

1. **Extract** — market (Binance public), on-chain (DexScreener), user events
2. **Transform** — normalize, checksum, quality score (target 99.99% accuracy)
3. **Load** — PostgreSQL + InfluxDB (JSONL fallback when Influx unavailable)
4. **Query** — cached reads via `/api/platform/infra/etl/query`
5. **Export** — admin export to `data/etl/reports/`

## API (ops)

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/infra/etl/status` | Public | Health + store connectivity |
| `POST /api/platform/infra/etl/run` | Admin | Run one ETL cycle |
| `GET /api/platform/infra/etl/query` | Public | Query cleaned records |
| `GET /api/platform/infra/etl/export` | Admin | Export dataset |

## Environment

```bash
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0
INFLUXDB_URL=http://localhost:8086
INFLUXDB_TOKEN=blackdark-dev-token
INFLUXDB_ORG=blackdark
INFLUXDB_BUCKET=blackdark
ETL_RETENTION_DAYS=730
```

## Docker

`docker compose up -d postgres redis influxdb` — Influx initialized with 730-day retention.

## Acceptance

- Validation accuracy ≥ 99.99% (rolling)
- Query latency ≤ 1 second (cached)
- Retention ≥ 2 years
- Near-real-time ingest on admin trigger or scheduled job
