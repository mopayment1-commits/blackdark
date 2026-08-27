# Screener, Sentiment, Alerts & Smart Money Merges — #587, #588, #589, #590, #593

## Summary

| Feature | Legal Name | Merged Into |
|---------|------------|-------------|
| #587 | Screener | #533 Market Data Screener epic |
| #588 | Social Sentiment Layer | Epic (absorbs #595, #596, #600) |
| #589 | Smart Alerts | #532 Alert Layer |
| #590 | Accumulation/Distribution Detection | Smart Money Flow Intelligence (#408) |
| #593 | Historical Trend Analysis | Smart Money Flow Intelligence (#408) |

---

## #587 — Screener (→ #533 Market Data Screener)

User-controlled filtering — no default platform ranking.

### Acceptance

- Backend enforcement
- Deterministic sort (user-specified only)
- Missing values explicit
- Pagination

### Routes

```
GET .../intelligence-layer/market-data-screener?sort_by=risk_score&page=1&page_size=50
GET .../intelligence-layer/market-data-screener/reconciliation-tests
```

---

## #588 — Social Sentiment Layer

Absorbs #595, #596, #600 duplicates. ToS-compliant. No unsupported causality.

### Routes

```
GET .../data-layer/social-sentiment?asset=BTC
GET .../data-layer/social-sentiment/reconciliation-tests
```

---

## #589 — Smart Alerts (→ #532 Alert Layer)

Metric threshold alerts with cooldown, dedupe, delivery logs.

### Routes

```
GET .../infrastructure/custom-alerts
GET .../infrastructure/custom-alerts/reconciliation-tests
```

---

## #590 / #593 — Smart Money Flow Intelligence

### #590 Output (renamed)

`Accumulation/Distribution State + Net-Flow Persistence Indicator` — not investment score.

### #593 Regimes

Statistical only: `high_activity_period` / `low_activity_period` — not bullish/bearish.

### Routes

```
GET .../onchain-layer/smart-money-flow/accumulation-distribution?asset=BTC
GET .../onchain-layer/smart-money-flow/historical-trend?asset=BTC
```

---

## Test Suite

```bash
.venv/bin/python -m pytest tests/test_screener_sentiment_alerts_merges_batch.py -q
```
