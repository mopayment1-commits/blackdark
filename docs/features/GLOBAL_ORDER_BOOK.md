# Global Order Book Metrics — #249 (Sprint 2 Intelligence)

Aggregates order book depth across venues with documented weights, sequence gap
handling, and imbalance as context. **Replaces #227** opportunistic framing.

Integrated into **Market Radar** as **Global Order Book tab** — NOT standalone.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Sequence gaps | Detected, interpolated (dashed), coverage disclosed |
| Venue weights | 30D volume-weighted, versioned — no equal-weight |
| Global depth | Descriptive bid/ask depth + imbalance label |
| Imbalance | Context only — "Not: Bullish signal" |
| Per-venue breakdown | Each venue + global total |
| Update frequency | Enterprise 1s / Pro 5s / Free 30s — no "instant" |
| Disclaimer | Non-hideable |
| No opportunity language | Technical context only |
| Fee DB (#130) | Only if arbitrage — module stays technical |
| Market Radar tab | `global_order_book` block in dashboard |
| Methodology v1.3 | Volume-weighted, gap interpolation + alert |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/market-radar/order-book` | Global Order Book tab |
| `GET /api/platform/market-radar/order-book/status` | Module status |
| `GET /api/platform/market-radar/dashboard` | Includes `global_order_book` block |

## Related

- `bd_platform/market_radar_dashboard.py` — Market Radar integration
- `bd_platform/cvd_intelligence.py` — related order flow context (#232)
