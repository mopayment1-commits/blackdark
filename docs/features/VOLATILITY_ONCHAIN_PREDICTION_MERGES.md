# Volatility, On-Chain & Prediction Merges — Features #498, #578, #579, #580

## Summary

Four features merged into existing layers — no standalone modules.

| Feature | Legal Name | Merged Into |
|---------|------------|-------------|
| #498 | Volatility Analytics | Market Radar |
| #578 | On-Chain Usage Intelligence | #577 On-Chain Metrics Library |
| #579 | Non-Custodial Wallet Balance Tracker | Portfolio Intelligence Layer (#557/#569 epic) |
| #580 | Prediction Trend Analyzer | Data Layer / Sprint 1 |

---

## #498 — Volatility Analytics (→ Market Radar)

Realized volatility dashboard with mandatory rolling windows and transparent methodology.

### Rolling Windows

`7d`, `30d`, `90d` — all three mandatory with documented window + methodology version.

### Integrations

| Target | Behavior |
|--------|----------|
| #458 Volatility Compression | Vol drop computed as compression signal |
| #410 Capital Protection | High-vol regime adjusts position risk score context |

### Routes

```
GET /api/platform/intelligence-ledger/market-radar/volatility-analytics?asset=BTC
GET /api/platform/intelligence-ledger/market-radar/panel?exchange=binance&asset=BTC
GET /api/platform/intelligence-ledger/market-radar/reconciliation-tests
```

---

## #578 — On-Chain Usage Intelligence (→ #577 Metrics Library)

Adoption and usage metrics (DAA, txs, volumes) normalized by chain/app with spam/bot policies.

### Acceptance

- Spam/bot exclusion policy documented
- `missing ≠ zero`
- Metric definitions linked to canonical library

### Routes

```
GET /api/platform/intelligence-ledger/onchain-layer/metrics-library/usage?asset=BTC
```

---

## #579 — Non-Custodial Wallet Balance Tracker (→ Portfolio Intelligence Layer)

Renamed from `On_Chain_Balance_Monitor`. Holdings + changes + **data alerts only** — no risk output.

### Acceptance

- Chain reorg handling
- Spam-token filtering
- Price-source provenance per asset
- Address validation
- Statistical anomaly only (no "suspicious activity" language)

### Routes

```
GET /api/platform/intelligence-ledger/portfolio-layer/non-custodial-wallet-tracker?address=...&chain=ethereum
```

---

## #580 — Prediction Trend Analyzer (→ Data Layer)

Contextual signal from prediction-market probabilities — **not** BLACKDARK predictions.

### Acceptance

- Source attribution (`Polymarket probability: X%`)
- Liquidity threshold enforced
- Correlation ≠ causation
- No unsupported price forecast

### Routes

```
GET /api/platform/intelligence-ledger/data-layer/prediction-trends/status
GET /api/platform/intelligence-ledger/data-layer/prediction-trends
GET /api/platform/intelligence-ledger/data-layer/prediction-trends/reconciliation-tests
```

---

## Test Suite

```bash
.venv/bin/python -m pytest tests/test_volatility_onchain_prediction_merges_batch.py -q
```
