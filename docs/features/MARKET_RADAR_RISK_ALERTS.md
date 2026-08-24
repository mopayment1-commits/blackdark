# Market Radar & Risk Alerts — Features #121, #122, #114, #123

## #121 — Large Liquidity Event Alert

**Not** "buy now" — data + qualitative analysis only.

Example:
> Detected $2M sell on Binance. Price dropped 8%. Sell type: Stop-loss cascade. Analysis: may be a buy opportunity, but risks are elevated.

- API: `GET /api/platform/market-radar/large-liquidity-events`
- `mode`: `alert_only`
- `no_buy_language`: true

## #114 + #122 — Listing Intelligence Engine

Unified timeline:

**Deposit Opened (#122) → Listing Announced (#114) → First Trade**

- API: `GET /api/platform/market-radar/listing-intelligence`
- `mode`: `event_only` — not buy recommendations

## #123 — Withdrawal Closure Alert (highest priority)

Per-asset withdrawal suspension with classification:

| Classification | Meaning |
|----------------|---------|
| `likely_maintenance` | Short duration, moderate health |
| `elevated_risk` | Poor health — not typical maintenance |
| `dangerous_closure` | FTX-class insolvency pattern |
| `uncertain` | Insufficient data |

Integrated with:
- **#109** Portfolio Risk — `portfolio_risk` hook in alerts
- **#110** Exchange Health — `exchange_health_110` context
- **#134** Platform Status — `platform_status_134` block

APIs:
- `GET /api/platform/risk/withdrawal-closures`
- `POST /api/platform/risk/withdrawal-closures/record` (admin)
- `GET /api/platform/exchange-health/status`

## Acceptance (all)

- Response ≤ 2 seconds (`sla_met`)
- Accuracy estimate ≥ 95%
- Informational / risk-signal modes only
