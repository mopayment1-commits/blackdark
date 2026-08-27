# Data, Market Price & Valuation Merges — Features #581, #582, #583, #584, #585

## Summary

Five features merged into existing layers — no standalone modules.

| Feature | Legal Name | Merged Into |
|---------|------------|-------------|
| #581 | Price / Volume / Market Metrics | #564 Data Infrastructure Layer |
| #582 | Price-Move Event Correlator | #556 Flow-to-Price Event Correlation Layer |
| #583 | Market Anomaly Detection Module | Intelligence Layer (renamed from Pump & Dump) |
| #584 | Realized Cap & Realized Price Intelligence | #570 Protocol Valuation Layer |
| #585 | Realized Cap / Realized Value Intelligence | #570 Protocol Valuation Layer (merged with #584) |

---

## #581 — Price / Volume / Market Metrics (→ Data Infrastructure)

Foundation market layer: price, volume, market cap, returns with normalized feeds.

### Acceptance

- Source/freshness visible per metric
- Outlier flagged (not suppressed)
- Stale feed handling with visible stale flag

### Routes

```
GET /api/platform/intelligence-ledger/data-layer/infrastructure/price-volume-market-metrics?asset=BTC
```

---

## #582 — Price-Move Event Correlator (→ #556 epic)

Absorbed into unified **Price-Move Event Correlation Layer** with #519 and #556.

### Linguistic Framing

- "Candidate events in temporal window" — not "Top likely drivers"
- "Temporal correlation strength" / data completeness score — not causation confidence
- Evidence classification: 🟢 Fact | 🟡 Hypothesis | 🔴 Inference

### Routes

```
GET /api/platform/intelligence-ledger/intelligence-layer/price-move-correlation-layer?asset=BTC
GET /api/platform/intelligence-ledger/intelligence-layer/flow-to-price-correlator/reconciliation-tests
```

---

## #583 — Market Anomaly Detection Module

Renamed from Pump & Dump Detection. Statistical multi-signal flags only.

### Acceptance

- Minimum coverage gate (3+ signals)
- No label without multi-signal evidence
- "Multiple anomalies detected: [list]" — no accusation language

### Routes

```
GET /api/platform/intelligence-ledger/intelligence-layer/market-anomaly?asset=ALT
GET /api/platform/intelligence-ledger/intelligence-layer/market-anomaly/reconciliation-tests
```

---

## #584 / #585 — Realized Cap Intelligence (→ Protocol Valuation)

Chain-specific realized cap/price with entity-adjusted option and historical replay QA.

### Routes

```
GET /api/platform/intelligence-ledger/data-layer/protocol-valuation/realized-cap?asset_id=bitcoin
```

---

## Test Suite

```bash
.venv/bin/python -m pytest tests/test_data_market_price_merges_batch.py -q
```
