# On-Chain Metrics Library — Epic #577

## Decision

**Sprint 0 (Foundation Layer) — highest priority.**

Epic with sub-module tasks (not standalone tickets):

| Task | Name | Role |
|------|------|------|
| #577 | On-Chain Metrics Library | Canonical definitions + versioning + QA |
| #574 | Network Data Pro Metrics | Institutional API delivery (sub-task) |
| #737 | HODL Waves | Absorbed via `onchain_metrics_suite` |
| #741 | MVRV Z-Score | Absorbed via `onchain_metrics_suite` |

**#574 is NOT a standalone ticket** — it is the API delivery layer for metrics defined in #577.

## Live Indexer (Rule 6 — Real Data)

Priority order per metric:

1. **Live indexer** (`onchain_live_indexer.py`) — free public APIs
2. **Seed fallback** (`onchain_metrics_library_seed.json`) — labeled BACKTESTED
3. **Unavailable** — `غير متوفر` (never zero)

| Metric | BTC Live Source | ETH Live Source |
|--------|-----------------|-----------------|
| Hash rate | mempool.space / Blockchair | N/A (unavailable) |
| Active addresses | blockchain.info | unavailable (free tier) |
| Transaction count | Blockchair | Blockscout / Blockchair |
| Exchange netflow | exchange_intelligence_layer (derived) | same |

## API

```
GET /api/platform/intelligence-ledger/onchain-layer/metrics-library/status
GET /api/platform/intelligence-ledger/onchain-layer/metrics-library?asset=BTC
GET /api/platform/intelligence-ledger/onchain-layer/metrics-library/network-api?asset=BTC
GET /api/platform/intelligence-ledger/onchain-layer/metrics-library/live?asset=BTC
GET /api/platform/intelligence-ledger/onchain-layer/metrics-library/historical-qa
```

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Formula/source/version | Per-metric in seed + `build_metric_definitions()` |
| Historical QA | `run_historical_qa_tests()` |
| missing ≠ zero | `_sanitize_metric_value()` |
| Canonical definitions | Single seed source of truth |
| Live indexer | `fetch_live_onchain_metrics()` with seed fallback |
