# Live Breakeven Tracker — Feature #404

## Decision

**Sprint 2 Portfolio AI Enhancement — High priority, NOT standalone.**

Legal name: **Live Breakeven Tracker** / **Dynamic Cost Basis**  
Forbidden name: "Auto-Calculation" (implies system decides).

| Scope | Status |
|-------|--------|
| Dynamic breakeven (not static entry price) | ✅ |
| Fee Transparency — every cent visible | ✅ |
| Breakeven Scenario Simulator | ✅ |
| Intelligence Ledger distance-to-breakeven | ✅ |
| Capital Protection (#410) proximity alerts | ✅ |
| Client-side instant + server 30s refresh | ✅ |
| Standalone module/API | ❌ Cancelled |
| ≤2s API / 99% uptime criteria | ❌ Modified/cancelled |

## Cost Factors in Breakeven

1. Average entry + DCA entries
2. Partial exits (average-cost method on remaining)
3. Exchange fees (maker/taker)
4. Network fees
5. Funding rate accumulation
6. Slippage

## API

```
GET /api/platform/intelligence-ledger/portfolio-ai/live-breakeven/status
GET /api/platform/intelligence-ledger/portfolio-ai/live-breakeven?position_id=pos_btc_001
GET /api/platform/intelligence-ledger/portfolio-ai/live-breakeven/simulate?hypothetical_dca_qty=0.1&hypothetical_dca_price=62000
GET /api/platform/intelligence-ledger/portfolio-ai/live-breakeven/reconciliation-tests
GET /api/platform/intelligence-ledger/portfolio-ai/capital-protection/breakeven-alerts
GET /api/platform/intelligence-ledger/intelligence-layer/live-breakeven/signal-context?symbol=BTC
```

## UI

`/portfolio-ai/live-breakeven` — interactive panel with scenario simulator.

Client-side instant calculation via `static/js/live_breakeven_tracker.js`; server refresh every 30 seconds.

## Accuracy

Target: **±0.01%** from actual breakeven after all costs deducted.

## Integrations

| System | Behavior |
|--------|----------|
| Intelligence Ledger | Signals attach `distance_to_breakeven` when user owns asset |
| Capital Protection (#410) | Alerts when price within proximity threshold of breakeven |

## Competitive Differentiator

Fee Transparency shows every cent added to breakeven — not offered by CoinTracker, Delta, or Koinly.
