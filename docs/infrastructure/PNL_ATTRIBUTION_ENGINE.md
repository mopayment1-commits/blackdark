# PnL Attribution & Drift Analysis Engine — Feature #199

**Wave 2 — True Cost Engine.** Integrates with #113 (Net Profit) and #130 (Fee Database).

## Waterfall Example

```
Gross Profit: +$500
  → Trading Fees: -$15
  → Slippage: -$8
  → Gas: -$5
  → Net Profit: $472

Drift: expected $490 → actual $472 → $18 gap
  → 60% slippage_drift (Uniswap execution quality)
```

## API

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/analytics/pnl-attribution/status` | Public | Engine status |
| `GET /api/platform/analytics/pnl-attribution/methodology` | Public | Versioned methodology (v1.0) |
| `POST /api/platform/analytics/pnl-attribution/trade` | User | Single trade attribution |
| `POST /api/platform/analytics/pnl-attribution/portfolio` | User | Portfolio attribution + Sharpe/Sortino |

## Attribution Factors

| Factor | Description |
|--------|-------------|
| market_drift | General market movement (beta) |
| fee_drift | Unexpected/hidden fees |
| slippage_drift | Execution quality vs expected |
| timing_drift | Entry/exit delay impact |
| decision_drift | Suboptimal venue/network choice |
| residual | Remainder (must be ≤ 0.5%) |

## Acceptance Criteria

| Criterion | Target |
|-----------|--------|
| Attribution accuracy | ≥ 95% |
| Trade report SLA | ≤ 3 seconds |
| Portfolio report SLA | ≤ 10 seconds |
| Unexplained drift | ≤ 0.5% |
| Sharpe/Sortino | On Net PnL, not Gross |
| Methodology | Versioned (v1.0) |
