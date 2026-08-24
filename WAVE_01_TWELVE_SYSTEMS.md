# Wave 01 — Twelve Systems Sprint

**Branch:** `cursor/wave-01-twelve-systems-e85e`  
**Governing:** [`BLACKDARK_CONTEXT.md`](BLACKDARK_CONTEXT.md) — platform verdict **NOT READY**

## Systems map

| # | System | Migration | API | Status |
|---|--------|-----------|-----|--------|
| 1 | Live Shadow Collection | — | `/api/v1/data/status` + APScheduler | ✅ Kraken 1h + Binance/CoinGecko jobs |
| 2 | Historical Backfill | — | CLI `python -m blackdark.data backfill` | ✅ Kraken pagination fallback |
| 3 | Data Provenance | `007_data_provenance` | `/api/v1/data/provenance/{id}` | ✅ SHA-256 |
| 4 | Ingestion Run Versioning | `002_ingestion_runs` | `/api/v1/data/ingestion-runs` | ✅ |
| 5 | Market Event Library | `006_market_events` | `GET/POST /api/v1/data/events` | ✅ |
| 6 | Failure Registry | `008_ingestion_errors` | `/api/v1/data/ingestion-errors` | ✅ |
| 7 | Signal Registry | `011_de_signal_registry` | `/api/v1/data/signals` | ✅ |
| 8 | Prediction Ledger | `012_de_prediction_ledger` | `/api/v1/data/predictions` | ✅ sealed hash |
| 9 | Decision Ledger | `013_de_decision_ledger` | `/api/v1/data/decisions` | ✅ act/wait |
| 10 | Outcome Evaluator | `014_de_outcome_evaluations` | `/api/v1/data/outcomes` | ✅ hit/miss/pending |
| 11 | Evidence Store | `015_de_evidence_store` | `/api/v1/data/evidence` | ✅ append-only |
| 12 | Failure Misses | `016_de_failure_misses` | `/api/v1/data/failures/misses` | ✅ |

## Backfill fix

Binance returns `records_fetched: 0` on geo-blocked hosts. CLI now auto-falls back to **Kraken `since` pagination**:

```bash
python -m blackdark.data backfill --source binance --symbol BTCUSDT --interval 1h --days 30
# → tries Binance, then Kraken with records_fetched > 0
```

## Proof

```bash
pytest tests/test_wave_01_systems.py -v
PROD=https://blackdark-production.up.railway.app bash scripts/wave_01_twelve_systems_proof.sh
curl -sS $PROD/api/v1/data/systems | python3 -m json.tool
```
