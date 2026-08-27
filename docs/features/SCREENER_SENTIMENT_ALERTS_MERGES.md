# Screener, Sentiment, Alerts & Smart Money Merges — #587–#598

## Summary

| Feature | Legal Name | Merged Into |
|---------|------------|-------------|
| #587 | Screener | #533 Market Data Screener epic |
| #588 | Social Sentiment Layer | Epic (absorbs #595, #596, #600) |
| #589 | Smart Alerts | #532 Alert Layer |
| #590 | Accumulation/Distribution Detection | Smart Money Flow Intelligence (#408) |
| #593 | Historical Trend Analysis | Smart Money Flow Intelligence (#408) |
| #595/#596 | Entity-Tagged Sentiment Feed | #588 Social Sentiment Layer sub-module |
| #597 | Smart Money Token Screener | #533 Market Data Screener sub-filter |
| #598 | Smart Money Tracking | Smart Money Flow Intelligence (#408) |

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

### #595 / #596 — Entity-Tagged Sentiment Feed

Renamed from "Smart Money Sentiment Alignment Core". No alignment scoring here — alignment is computed in #524 Cross-Domain Context Layer.

### Acceptance (#595/#596)

- 15-minute refresh
- NLP accuracy ≥ 80%
- ≥ 5 sources (Twitter, Reddit, Telegram, news, Google Trends)
- Archive ≥ 1 year

### Routes

```
GET .../data-layer/social-sentiment?asset=BTC
GET .../data-layer/social-sentiment/entity-tagged-feed?asset=BTC
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

## #597 — Smart Money Token Screener (→ #533 Market Data Screener)

User-controlled filters only — no recommended tokens. Each match is explainable.

### Acceptance

- Backend filters
- Explain each match: `Matched: Inflow > $X | Wallets: Y | Timeframe: Z`
- Save + alert supported

### Routes

```
GET .../intelligence-layer/market-data-screener/smart-money?smart_money_inflow_min=5000000
GET .../intelligence-layer/market-data-screener/smart-money?saved_screener_id=smart_money_token_screener
```

---

## #590 / #593 / #598 — Smart Money Flow Intelligence

### #590 Output (renamed)

`Accumulation/Distribution State + Net-Flow Persistence Indicator` — not investment score.

### #593 Regimes

Statistical only: `high_activity_period` / `low_activity_period` — not bullish/bearish.

### #598 — Smart Money Tracking

Classified wallet feed. Event-based alerts (not advisory). Depends on #541 entity resolution.

### Acceptance (#598)

- Latency measured and visible
- Duplicate prevention
- Missed-event handling

### Routes

```
GET .../onchain-layer/smart-money-flow/accumulation-distribution?asset=BTC
GET .../onchain-layer/smart-money-flow/historical-trend?asset=BTC
GET .../onchain-layer/smart-money-flow/tracking?watchlist_id=default
```

---

## Test Suite

```bash
.venv/bin/python -m pytest tests/test_screener_sentiment_alerts_merges_batch.py -q
```
