# Feature #74 — Market Microstructure Intelligence

Silent Decision Engine layer for order book toxicity, spoofing heuristics, and liquidity health.

## Scope

**NOT a standalone product** — feeds #48 Decision Engine, #56 Execution Optimizer, and complements #85 Order Flow.

## Features (rule-based v1)

| Metric | Description |
|--------|-------------|
| VPIN proxy | Volume-bucket informed trading probability |
| Order Book Imbalance (OBI) | Bid vs ask depth skew |
| Effective spread | Bid-ask in bps |
| Spoofing score | Off-touch large walls + cancellation between snapshots |
| Liquidity Health | 0-100 depth + spread composite |
| Market impact curve | Slippage at $1K / $10K / $50K / $100K |

## Toxicity regimes

- `normal` — healthy microstructure
- `caution` — elevated toxicity or thin liquidity
- `high_toxicity` — VPIN spike or stressed book
- `manipulation_detected` — spoofing heuristic ≥70

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/microstructure/analyze?asset=ETH` | Full analysis |
| `GET /api/platform/microstructure/status` | Module health |
| `decision_engine_inputs.market_microstructure` | Compact risk feed |

## Coverage

≥52 liquid USDT pairs on Binance spot (proxy for spot + futures majors).

## Disclaimer

Detectors are transparent rule-based heuristics — not trained ML models. L3 cancel streams = future upgrade path.
