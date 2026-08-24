# Feature #94 — AI Trade Simulator (Paper Trading Engine)

Paper trading integrated with #48 Decision Engine — safe virtual capital testing.

## Modes

### Forward (Live Paper)
- Tracks real-time `#48` Decision Engine signals
- Executes virtual trades when confidence ≥ 70%
- Manual override supported
- API: `POST /api/platform/paper-trading/forward-tick`

### Historical Backtest
- Walk-forward on purged OHLCV (no future leakage)
- Realistic execution: slippage + fees + spread
- Performance report: Sharpe, Max DD, Win Rate, Profit Factor
- API: `GET /api/platform/paper-trading/backtest`

## Execution model

```
executed_price = signal_price ± (spread/2 + slippage_bps)
total_cost = executed_price × quantity + exchange_fee
```

Slippage scales with order size (log-based proxy).

## Virtual portfolio

- Default capital: $10,000 (configurable)
- Position sizing: 2% risk per trade
- ≥50 supported assets
- Reset anytime

## APIs

| Endpoint | Purpose |
|----------|---------|
| `POST /api/platform/paper-trading/forward-tick` | Live paper tick |
| `GET /api/platform/paper-trading/backtest` | Historical backtest |
| `GET /api/platform/paper-trading/portfolio` | Virtual dashboard |
| `POST /api/platform/paper-trading/reset` | Reset portfolio |
| `GET /api/platform/paper-trading/status` | Module health |

## Acceptance

| Criterion | Implementation |
|-----------|----------------|
| P&L accuracy ≥99% | Deterministic fee/slippage formulas |
| Signal latency ≤10s | Async single-tick forward mode |
| Backtest ≥2 years | Archive + extended kline history |
| ≥50 assets | `_SUPPORTED_ASSETS` (50) |
| No future leakage | `point_in_time_decision_signal` only in backtest |
| #48 integration | `gather_decision_inputs` in forward mode |

## Distinction from #99 Trading Journal

- **#94**: Automated paper execution from AI signals
- **#99**: Manual trade logging + psychology coach
