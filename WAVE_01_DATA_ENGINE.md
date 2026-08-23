# Wave 01 — Sprint 1: Data Engine

**Branch:** `wave-01-data-engine`  
**Status:** IMPLEMENTED (pending production deploy + curl/k6 proofs)  
**Version:** `1.0.0`

## Objective

Foundational data collection and provenance layer. Every data point is sourced, timestamped, versioned, attributable, and queryable.

## Deliverables

| Item | Status |
|------|--------|
| 9 DB migrations (`blackdark/data/migrations/001-009`) | ✅ |
| 7 API endpoints (`/api/v1/data/*`) | ✅ |
| Admin seed (`POST /api/v1/admin/seed-sources`) | ✅ |
| 3 background jobs (Binance OHLCV 1m/1h, funding, CoinGecko) | ✅ APScheduler |
| Backfill CLI (`python -m blackdark.data backfill ...`) | ✅ |
| Provenance endpoint | ✅ |
| k6 script (`scripts/k6_wave_01_data.js`) | ✅ |
| Unit tests | ✅ 3/3 |

## PostgreSQL required

Set `DATABASE_URL=postgresql://...` on Railway. SQLite returns HTTP 503 on data endpoints.

## Post-deploy curl proofs

```bash
# Seed sources (admin)
curl -sS -X POST https://blackdark-production.up.railway.app/api/v1/admin/seed-sources \
  -H "Content-Type: application/json" -H "X-Admin-Key: $ADMIN_KEY" -d '{}'

# Trigger ingestion
curl -sS -X POST https://blackdark-production.up.railway.app/api/v1/data/ingest \
  -H "Content-Type: application/json" -H "X-Admin-Key: $ADMIN_KEY" \
  -d '{"source":"binance","symbols":["BTCUSDT"],"intervals":["1h"],"backfill_days":1}'

curl -sS "https://blackdark-production.up.railway.app/api/v1/data/ohlcv?symbol=BTCUSDT&interval=1h&limit=5"
curl -sS "https://blackdark-production.up.railway.app/api/v1/data/funding?symbol=BTCUSDT&limit=5"
curl -sS "https://blackdark-production.up.railway.app/api/v1/data/open-interest?symbol=BTCUSDT&limit=5"
curl -sS https://blackdark-production.up.railway.app/api/v1/data/status
curl -sS "https://blackdark-production.up.railway.app/api/v1/data/events?limit=5"
```

## k6

```bash
k6 run -e BASE=https://blackdark-production.up.railway.app scripts/k6_wave_01_data.js
```

## Backfill

```bash
python -m blackdark.data backfill --source binance --symbol BTCUSDT --interval 1h --days 30 --batch-size 1000
```
