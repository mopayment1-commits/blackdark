# Confidence Engine — Feature #149 (Sprint 2, Phased)

## Phase Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| **1** | Active | Rule-based scoring — 13 criteria, 0-100 |
| **2** | Planned (3-6 mo) | ML models on accumulated data |
| **3** | Planned (12 mo) | Full engine + 2-year backtest |

## Phase 1 Label

```
Confidence: Experimental — 78/100 (moderate)
```

**No Sharpe ≥1.5 promise on day one.** Performance disclosure is honest and verifiable.

## Criteria (13 weighted)

Multi-source agreement, source diversity, outlier cleanliness, data validation (#147), accuracy estimate, latency, liquidity, price stability, clean quote ratio, connector success, VWAP, live path, asset tier.

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/confidence/score?asset=BTC` | Rule-based confidence |
| `GET /api/platform/confidence/status` | Roadmap + disclosure |

## Oracle Integration (#125)

`confidence_engine` block attached to single-sentence oracle responses.

## Acceptance (Phase 1)

- Score 0-100 with transparent criteria
- Latency ≤ 2 seconds
- No fabricated ML metrics
- Roadmap visible to users
