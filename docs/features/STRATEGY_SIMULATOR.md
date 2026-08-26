# Strategy Simulator — Feature #411

## Decision

**Sprint 2 Simulation Module — High priority, NOT standalone EMS.**

Legal name: **Strategy Simulator** / **Paper Portfolio**  
Forbidden: "EMS", "Execution", "Order Routing"

| Scope | Status |
|-------|--------|
| Paper portfolio only | ✅ |
| Real money blocked | ✅ Fail-closed |
| Signal application on paper | ✅ |
| Breakeven integration (#404) | ✅ |
| Risk Budget on paper (#410) | ✅ |
| 30-day paper backtest | ✅ |
| Standalone EMS | ❌ Cancelled |

## API

```
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/status
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/apply-signal?signal_id=sig_btc_momentum
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/backtest-30d
GET /api/platform/intelligence-ledger/portfolio-ai/strategy-simulator/reconciliation-tests
```

## SLA

> SIMULATION — Paper Portfolio only. Real money order placement is isolated and blocked.

## Competitive Differentiator

Paper trading on real market data with signal application, breakeven tracking, and risk budget testing — insight platforms rarely offer integrated virtual portfolio testing.
