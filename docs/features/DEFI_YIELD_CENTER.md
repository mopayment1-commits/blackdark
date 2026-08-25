# DeFi Yield Center — #709 + #710 + #711 + #198 (Sprint 2)

Unified DeFi Hub — **NOT** separate screeners. Single surface integrating:

| Feature | Surface | Tier |
|---------|---------|------|
| #711 | Yields Screener | All |
| #709 | Yield History / Sustainability | All |
| #710 | Yield Arbitrage Engine | Pro / Institutional |
| #198 | Yield Optimization | All |

## #711 — Yields Screener

| Rule | Implementation |
|------|----------------|
| APY methodology | `APY = (fees_24h * 365 / TVL) * 100 + incentive_APY` |
| Stale pools excluded | No interaction in 7+ days → hidden from screener |
| Display | `Pool X: APY 12% \| TVL $50M \| Risk: 🟡 Medium \| Stale: ❌ No` |
| No guaranteed yield | Disclaimer on every response |

## #710 — Yield Arbitrage Engine

| Rule | Implementation |
|------|----------------|
| Costs included | gas + bridge + lockup + slippage = net yield |
| Break-even horizon | `To recover switching cost: 3 days` |
| Historical simulation | `6-month backtest → 78% success rate` |
| No auto-execute | Simulation only; Execute requires MFA |
| No guaranteed yield | Legal protection disclaimer |

## #198 — Yield Optimization

Risk-adjusted pool allocation suggestion based on screener results. Simulation only.

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/defi/yield-center/status` | Module status |
| `GET /api/platform/defi/yield-center/dashboard` | Unified dashboard (all surfaces) |
| `GET /api/platform/defi/yield-center/screener` | #711 pool screener |
| `GET /api/platform/defi/yield-center/arbitrage` | #710 arbitrage opportunities |
| `GET /api/platform/defi/yield-center/arbitrage/{id}` | Arbitrage detail |
| `POST /api/platform/defi/yield-center/arbitrage/{id}/simulate` | Historical simulation |
| `GET /api/platform/defi/yield-center/optimize` | #198 allocation suggestion |

## Related

- `bd_platform/yield_sustainability_score.py` — #709 Yield History
- `bd_platform/defi_tvl_engine.py` — #702 DeFi TVL (Market Radar layer)
- `bd_platform/incentive_tracker.py` — #203 incentive programs
