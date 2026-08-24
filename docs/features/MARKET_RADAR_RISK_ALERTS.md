# Market Radar & Risk Alerts — Features #121, #122, #114, #123, #129, #131

## #121 — Large Liquidity Event Alert

**Not** "buy now" — data + qualitative analysis only.

Example:
> Detected $2M sell on Binance. Price dropped 8%. Sell type: Stop-loss cascade. Analysis: may be a buy opportunity, but risks are elevated.

- API: `GET /api/platform/market-radar/large-liquidity-events`
- `mode`: `alert_only`
- `no_buy_language`: true

## #114 + #122 + #129 — Listing Intelligence Engine

Unified timeline:

**Deposit Opened (#122) → Listing Announced (#114) → First Trade → Opportunity Analysis (#129)**

- API: `GET /api/platform/market-radar/listing-intelligence`
- API: `GET /api/platform/market-radar/listing-opportunity?symbol=NEW&liquidity_usd=50000&opening_price_usd=0.01`
- `mode`: `event_only` + `opportunity_analysis` — not buy recommendations, no profit promises

Example (#129):
> Listed. Opening price: $0.01. Liquidity: $50K. Analysis: low liquidity — high slippage risk. Recommendation: wait 24 hours for stabilization.

## #131 — Unusual Liquidity Alert Engine

On-chain + CEX depth alerts with severity:

| Severity | Meaning |
|----------|---------|
| 🟡 `warning` | Unusual liquidity movement |
| 🔴 `critical` | 70%+ liquidity withdrawn — rug-pull warning |

- API: `GET /api/platform/market-radar/unusual-liquidity`
- Sources: AMM TVL (DexScreener), CEX order-book depth proxy
- Integrates with #193 Smart Contract Scanner when available

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

## #132 + #134 — Exchange Trust Layer

Unified interface combining quality score and platform status:

| Feature | Role |
|---------|------|
| **#132** | Exchange Quality Score — A+ to D badges, transparent methodology |
| **#134** | Platform Status — API/withdrawal/deposit/trading + 6-month history |

Badge examples:
- 🟢 A+ — Reserves Verified
- 🔴 D — Withdrawals Suspended 3x

APIs:
- `GET /api/platform/exchange-trust/dashboard` — unified #132 + #134
- `GET /api/platform/exchange-trust/quality` — quality scores only
- `GET /api/platform/exchange-health/status` — #110 + #134 platform status

## #135 — Order Flow Analytics

Translates order-book volume to plain language (not raw numbers):

- Buy Wall at $30K (500 BTC) — strong support
- Fake Sell Wall (spoofing detected) — cancels within seconds

API: `GET /api/platform/market-radar/order-flow?asset=BTC`

## Acceptance (all)

- Response ≤ 2 seconds (`sla_met`)
- Accuracy estimate ≥ 95%
- Informational / risk-signal modes only
