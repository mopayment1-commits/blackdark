# Unified Arbitrage Opportunity Engine — Features #429 + #428

Sprint-2 Intelligence Ledger Core. Unifies all arbitrage types under one canonical schema and shared economics engine (#427).

## #429 — Unified Engine

| Route | Description |
|-------|-------------|
| `GET /api/platform/intelligence-ledger/unified-arbitrage/status` | Feature status |
| `GET /api/platform/intelligence-ledger/unified-arbitrage` | Unified opportunity feed |
| `GET /api/platform/intelligence-ledger/unified-arbitrage/triangular` | #428 triangular scanner |
| `GET /api/platform/intelligence-ledger/unified-arbitrage/market-radar` | Market Radar integration |

### Canonical opportunity schema
`opportunity_type | gross_spread_bps | trading_fees | slippage | transfer_cost | net_edge | confidence | feasibility | risk_reasons`

### Acceptance
- Same economics engine (#427) for every arbitrage type
- Deduplication of equivalent opportunities (best net edge kept)
- Ranked by executable net edge only
- Deterministic net calculations (regression tested)
- **No real-money auto-execution** (SLA + Terms + every UI element)

## #428 — Triangular Price Divergence Scanner (merged)

Rule-based v1 only — no ML:
- 3-pair loop detection on single venue
- Stablecoin depeg monitor (USDT/USDC/DAI)

### Cancelled from v1
- ML training / 100+ features / walk-forward
- Sharpe ≥1.5, Max Drawdown ≤15%, Win Rate ≥55%
- FX local currency merge
- 4+ asset circular loops

## Integrations
- #417 Net-Edge Score
- #415 Fill Feasibility
- #422 Arbitrage Probability Signal (early detection filter)
- #433 Fill Risk Assessment
- #410 Capital Protection (SLA)
- #434 Opportunity Worth Studying Alerts
- #438 DeFi Opportunity Scanner
- #456 Exchange Health
- #460 Diligence Risk
- Market Radar

## #434 — Opportunity Worth Studying Alert Engine (merged)

Alerts fire only when:
- Net-Edge Truth score > threshold
- Feasibility = fillable
- Fill Risk % < user limit

Push/email via existing alert infrastructure. No "execution" language.

## #438 — DeFi Opportunity Scanner (merged)

Rule-based v1 monitoring only:
- Price divergence + implied yield + gas cost + net edge after fees
- LST peg deviation, liquidation discount % (monitoring only)
- Cancelled: flash loans, bridge execution, liquidation buying, ML SLAs
