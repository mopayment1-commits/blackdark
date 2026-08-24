# Wave 01 — Sprint 1: Data Engine

**Branch:** `cursor/wave-01-data-engine-e85e` (merged PR #92)  
**Bootstrap fix:** `cursor/wave-01-bootstrap-e85e`  
**Version:** `1.0.0`  
**Institutional audit:** [`WAVE_01_INSTITUTIONAL_AUDIT.md`](WAVE_01_INSTITUTIONAL_AUDIT.md)  
**Proof runner:** `bash scripts/wave_01_institutional_proof.sh`

## Objective

Foundational data collection and provenance layer. Every data point is sourced, timestamped, versioned, attributable, and queryable.

## Deliverables

| Item | Status |
|------|--------|
| 10 DB migrations (`blackdark/data/migrations/001-010`) | ✅ |
| 7 API endpoints (`/api/v1/data/*`) | ✅ |
| Admin seed (`POST /api/v1/admin/seed-sources`) | ✅ |
| Startup bootstrap (`ensure_data_engine_ready` + `DATA_ENGINE_BOOTSTRAP_INGEST`) | ✅ |
| 4 background jobs (Binance OHLCV 1m/1h, funding, CoinGecko) | ✅ APScheduler |
| Backfill CLI (`python -m blackdark.data backfill ...`) | ✅ |
| Provenance endpoint | ✅ |
| k6 script (`scripts/k6_wave_01_data.js`) | ✅ |
| Unit tests | ✅ |

## Control mapping (partial — NOT VERIFIED for institutional PASS)

| Control | Scope | Evidence | Status |
|---------|-------|----------|--------|
| DAT-001 | Data sourcing & lineage | `data_sources`, `ingestion_runs`, `/api/v1/data/provenance/{id}` | NOT VERIFIED |
| DAT-003 | Freshness / staleness gates | `data_engine_status`, job schedules | NOT VERIFIED |
| GOV-003 | No mock as sole production proof | Live Binance/CoinGecko ingest only | PASS WITH RISK (bootstrap may be empty if external APIs fail) |
| QA-004 | Reproducible evidence | This doc + curl/k6 below | NOT VERIFIED until production proofs pasted |
| REL-002 | Background job reliability | APScheduler + ingestion_errors table | NOT VERIFIED |

## PostgreSQL required

Set `DATABASE_URL=postgresql://...` on Railway. SQLite returns HTTP 503 on data endpoints.

### Bootstrap env

| Variable | Default | Purpose |
|----------|---------|---------|
| `DATA_ENGINE_ENABLED` | `true` | Master switch |
| `DATA_ENGINE_BOOTSTRAP_INGEST` | `true` | Seed sources + one-shot ingest when `ohlcv_data` is empty |

**Note:** Binance API is geo-restricted on some hosts (including Railway US). Bootstrap falls back to CoinGecko OHLC when Binance returns zero rows. Binance scheduled jobs may remain empty until ingest runs from an allowed region or via proxy — label **EXTERNAL EVIDENCE** per `BLACKDARK_CONTEXT.md` D-09.

## Post-deploy curl proofs (5.1 → 5.8)

```bash
PROD=https://blackdark-production.up.railway.app

# 5.1 Seed sources (admin)
curl -sS -X POST "$PROD/api/v1/admin/seed-sources" \
  -H "Content-Type: application/json" -H "X-Admin-Key: $ADMIN_KEY" -d '{}'

# 5.2 Trigger ingestion (admin)
curl -sS -X POST "$PROD/api/v1/data/ingest" \
  -H "Content-Type: application/json" -H "X-Admin-Key: $ADMIN_KEY" \
  -d '{"source":"binance","symbols":["BTCUSDT"],"intervals":["1h"],"backfill_days":1}'

# 5.3 OHLCV (30m from CoinGecko bootstrap when Binance geo-blocked; else 1h)
curl -sS "$PROD/api/v1/data/ohlcv?symbol=BTCUSDT&interval=30m&limit=5"
curl -sS "$PROD/api/v1/data/ohlcv?symbol=BTCUSDT&interval=1h&limit=5"

# 5.4 Funding
curl -sS "$PROD/api/v1/data/funding?symbol=BTCUSDT&limit=5"

# 5.5 Open interest
curl -sS "$PROD/api/v1/data/open-interest?symbol=BTCUSDT&limit=5"

# 5.6 Status
curl -sS "$PROD/api/v1/data/status"

# 5.7 Events
curl -sS "$PROD/api/v1/data/events?limit=5"

# 5.8 Provenance (replace UUID from ohlcv response)
curl -sS "$PROD/api/v1/data/provenance/<record-uuid>"
```

## k6

```bash
k6 run -e BASE=https://blackdark-production.up.railway.app scripts/k6_wave_01_data.js
```

## Backfill

```bash
python -m blackdark.data backfill --source binance --symbol BTCUSDT --interval 1h --days 30 --batch-size 1000
```

## Production proof log

Verified **2026-08-24** after bootstrap + Kraken fallback deploy (`c25079a`).

| Check | Result | Notes |
|-------|--------|-------|
| `/api/v1/data/status` sources populated | **PASS** | binance/coingecko failed (geo); kraken `completed`, 721 records |
| `/api/v1/data/ohlcv?interval=1h` count > 0 | **PASS** | Kraken-sourced BTCUSDT 1h candles with provenance_id |
| k6 Wave 01 | see below | |

```json
// /api/v1/data/status (excerpt)
{"sources":[{"slug":"kraken","last_run_status":"completed","records_24h":721}],"total_records":721}

// /api/v1/data/ohlcv?symbol=BTCUSDT&interval=1h&limit=3
{"count":3,"data":[{"source":"kraken","provenance_id":"b2172713-..."}]}
```

**Institutional note:** Binance blocked on Railway US (EXTERNAL EVIDENCE). CoinGecko also failed from host; Kraken public API used as failover. Verdict remains **NOT READY** per `BLACKDARK_CONTEXT.md`.
