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
| Coinbase time alignment | 1-minute bucket alignment check |
| No causation without corroboration | Premium observed — causation not asserted |

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
- Coinbase: "Coinbase Premium measures US venue price differential vs reference. Premium does not imply causation without corroborating flow data. Not investment advice."

Both `disclaimer_hideable: false`.

## Related

- `fee_matrix.py` — Fee DB (#130)
- `bd_platform/market_radar_dashboard.py` — Market Radar integration
