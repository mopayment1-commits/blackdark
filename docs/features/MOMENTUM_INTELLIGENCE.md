# Momentum Intelligence + Technical Ratings — #273 + #755 (Sprint 2)

Momentum decomposition merged into Technical Ratings — analysis layer, NOT buy/sell signal.

## #273 — Momentum Intelligence (merged into #755)

| Rule | Implementation |
|------|----------------|
| Formula documented | `Momentum = Price Trend (40%) + Acceleration (35%) + Volatility-Adjusted Return (25%) \| Version: 2.1` |
| No look-ahead | Only data up to day T; test: T+1 data never used |
| Historical validation | 2+ years: `Score > 7 → Forward 30D return +X% (with Y% volatility)` — not a promise |
| Multi-window | Short (7D) \| Medium (30D) \| Long (90D) decomposition |
| Components visible | Trend, Acceleration, Volatility-Adjusted Return each /10 |
| Not a signal | `Momentum Analysis: Strong Trend + Decelerating` — no Buy/Sell |
| Disclaimer | Non-hideable |

## #755 — Technical Ratings

Momentum score = 60% input to Technical Composite. Not standalone recommendation.

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/momentum/status` | Momentum module status |
| `GET /api/platform/market-radar/momentum` | Momentum analysis for asset |
| `GET /api/platform/market-radar/technical-ratings/status` | Technical Ratings status |
| `GET /api/platform/market-radar/technical-ratings` | Technical Composite (includes momentum) |

## Related

- `bd_platform/momentum_intelligence.py` — #273 core
- `bd_platform/technical_ratings.py` — #755 composite
- `data/momentum_intelligence_seed.json` — price series + validation
