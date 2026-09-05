# Exchange Health & Certification Engine — Feature #53

## Overview

Institutional trust layer — **"Moody's of Crypto"**. Evaluates exchange health, assigns certification badges, and explains score changes with AI-style narratives.

## Pipeline

1. Gather & clean data (CoinGecko, universe rollout, fee matrix, reference registry)
2. Extract 100+ exchange-specific features (not trading features)
3. Composite risk scoring with transparent dimension weights
4. Collapse-prediction validation against reference blacklisted venues
5. Publish rankings + alerts (6h cache, ≤1h emergency alert SLA)

## Outputs

| Output | Description |
|--------|-------------|
| Health Score | 0–100 per exchange |
| Risk Badge | Certified / Caution / High Risk / Blacklisted |
| AI Explanation | Score change drivers (PoR, withdrawals, regulatory, etc.) |
| Historical Timeline | Snapshot trail in `data/exchange_health_snapshots.jsonl` |
| Comparative Ranking | Full universe scan with badge distribution |

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/exchange-health/ranking` | Full scan + ranking (≥50 venues) |
| `GET /api/platform/exchange-health/assess?exchange_id=` | Single exchange assessment |
| `GET /api/platform/exchange-health/overview?exchange_id=` | Detail + universe rank |

## UI

`/exchange-health` — dark-theme hub with exchange selector, dimension breakdown, ranking table, and acceptance metrics.

## Data Sources

- **CoinGecko** — trust score, 24h volume (3 pages × 250)
- **Reference registry** — PoR status, regulatory tier, hack history (`data/exchange_health_reference.json`)
- **universe_rollout** — operational feed health
- **fee_matrix** — withdrawal fee coverage proxy
- **exchange_ingress_guard** — ban/rate-limit status

## Acceptance Criteria

| Criterion | Target | Implementation |
|-----------|--------|----------------|
| Collapse recall | ≥80% | `collapse_validation_metrics()` vs reference blacklisted |
| False positive rate | ≤10% | Safe-tier exchanges incorrectly flagged |
| Refresh cadence | 6–12h | 6h in-memory cache (`_CACHE_TTL`) |
| Coverage | ≥50 exchanges | CoinGecko 3-page fetch |
| Alert latency | ≤1h | `sla_met` on scan latency |

## Tests

```bash
pytest tests/test_exchange_health.py -v
```

## CAP Bindings

- **CAP-916** (extension): `bd_platform.exchange_health_engine.assess_all_exchanges`
- Keyword: `exchange health`, `certification engine`, `counterparty risk`

## Limitations

- PoR and regulatory data are reference-registry priors (not live on-chain attestation feeds)
- Wash-trading proxy uses volume/trust-score heuristic (not CoinMetrics order-book analysis)
- Sentiment panic uses static proxy (not live social feed)
- ML model training deferred to Sprint 4; feature vector is ML-ready
