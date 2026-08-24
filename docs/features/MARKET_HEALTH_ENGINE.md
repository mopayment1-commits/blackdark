# Market Health Dashboard — Feature #151 (Sprint 2)

## Role

Integrated **Market Health Dashboard** — not a single indicator.

## Four Pillars

| Pillar | Metrics |
|--------|---------|
| **On-Chain Health** | Daily transactions, hash rate, DeFi TVL (network value) |
| **Liquidity Health** | Multi-source price quality, outliers, TVL depth |
| **Sentiment Health** | Fear & Greed Index |
| **Macro Health** | DXY/S&P regime via Macro Context Engine (#141) |

## Classification

| Status | Emoji | Score |
|--------|-------|-------|
| Healthy | 🟢 | ≥70 |
| Cautious | 🟡 | 45–69 |
| Unhealthy | 🔴 | <45 |

One **classification reason** from the weakest pillar.

Example:
> 🟢 Healthy — Liquidity healthy — 7 sources, price verified

## #109 Integration

`portfolio_risk_109` block with recommended action:
- `maintain` (healthy)
- `review_positions` (cautious)
- `reduce_exposure` (unhealthy)

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-health/dashboard?asset=BTC` | Full dashboard |
| `GET /api/platform/market-health/status` | Engine health |

## Acceptance

- Response ≤ 2 seconds
- Accuracy ≥ 95%
- Real data sources (blockchain.com, DeFiLlama, Alternative.me, price aggregation)
- No placeholders
