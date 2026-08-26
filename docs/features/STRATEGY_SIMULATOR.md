# Strategy Simulator — Features #411 + #421

## Decision

**Sprint-2 Simulation Module — merged #421 Paper Trading into #411 Strategy Simulator.**

Legal name: **Strategy Simulator** / **Paper Portfolio**  
Forbidden: "EMS", "Execution", "Paper Trading" in legal naming

| Scope | Status |
|-------|--------|
| Paper account + PnL (#421) | ✅ |
| Order simulator + realistic fees (#421) | ✅ Fee DB (`fee_matrix`) |
| Realistic slippage options (#421) | ✅ #415 replay + venue profiles |
| No real execution | ✅ Every UI element + ToS |
| Signal application (Intelligence Ledger) | ✅ |
| Breakeven (#404) | ✅ |
| Risk Budget (#410) | ✅ |
| 30-day paper backtest | ✅ |

## API

```
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/status
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/paper-account
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/simulate-order
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/apply-signal
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/backtest-30d
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/reconciliation-tests
```

## Acceptance (#421)

- **No real execution** — blocked fail-closed; stated in SLA/ToS/UI
- **Realistic fees/slippage** — `fee_matrix` venue rates; slippage from #415 depth replay or documented profiles (never silent zero for unknown venue fees)

## Competitive Differentiator

Simulation shows **realistic** post-fee, post-slippage outcomes — not theoretical gross returns.
