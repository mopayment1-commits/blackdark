# Premium Intelligence Module — #255 Korea + #233 Coinbase (Sprint 2)

Regional premium analytics merged into one dashboard — educational + analytical, NOT arbitrage opportunity framing.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Reliable FX timestamps | `KRW/USD: 1,350.20 \| Source: ECB \| Timestamp: ... \| Update Frequency: Hourly` |
| FX stale fail-closed | Age > 2h → `FX Stale \| Premium: N/A` |
| Venue normalization | Volume-weighted: Upbit 40% \| Bithumb 35% \| Coinone 25% |
| Weights versioned | `Weights v1.3 \| Last Rebalanced: 2026-08-01` |
| Outage handling | Auto-recalculate weights, alert `Coverage reduced` |
| Global reference explicit | `Reference: Binance BTC/USDT \| FX-adjusted: Yes \| Methodology: VWAP 1H` |
| Regime detection | `Regime: Premium (Kimchi) \| Level: +3.2% \| Historical Context: 75th percentile` |
| No arbitrage framing | `Note: Arbitrage requires local banking + regulatory compliance` |
| Fee DB (#130) | Mandatory fee context when profit context shown |
| Coinbase time alignment | Identical timestamp: `Coinbase: ... UTC \| Reference: Binance BTC/USDT ... UTC \| FX: N/A` |
| Coinbase outage handling | `Coinbase API degraded \| Premium: N/A \| Last valid: ... \| Fallback: Kraken USD pair` |
| Rolling z-score documented | `Z-Score: 1.8 \| Window: 30D \| Mean: +0.5% \| StdDev: 1.2% \| Interpretation: ...` |
| Persistence analysis | `Premium Duration: 5 days \| Historical median: 2 days \| Regime: Persistent` |
| Divergence alerts | `Premium ↑ + BTC Price ↓ = Bearish Divergence` — not sell signal |
| US Demand Gauge | `US Demand Gauge: Elevated` — not "Buy BTC" |
| No causation without corroboration | `Correlation (90D): +0.65 \| Note: Correlation ≠ Causation` |

## Unified Dashboard

`Regional Premiums: US (Coinbase) | Korea | Japan | Europe`

Each region = one card. Japan/Europe planned for future sprints.

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/premiums/status` | Module status |
| `GET /api/platform/market-radar/premiums/dashboard` | Unified regional dashboard |
| `GET /api/platform/market-radar/premiums/korea` | Korea Premium Index (#255) |
| `GET /api/platform/market-radar/premiums/coinbase` | Coinbase Premium Index (#233) |

## Integration

- `bd_platform/market_radar_dashboard.py` — `regional_premiums` block in unified Market Radar
- `bd_platform/premium_intelligence.py` — core module

## Disclaimers

- Korea: "Korea Premium measures price differential after FX adjustment. Regulatory restrictions may prevent arbitrage. Not investment advice."
- Coinbase: "Coinbase Premium measures price differential between Coinbase and reference markets. It reflects US demand conditions but does not predict future prices. Not investment advice."

Both `disclaimer_hideable: false`.

## Related

- `fee_matrix.py` — Fee DB (#130)
- `bd_platform/market_radar_dashboard.py` — Market Radar integration
