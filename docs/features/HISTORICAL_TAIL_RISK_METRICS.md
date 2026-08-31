# Historical Tail Risk Metrics — #503 + #504

## Decision: 🟡 Rename & Merge

Features #503 (CVaR) and #504 (VaR) merged into a single ticket:

**Historical Tail Risk Estimates (VaR/CVaR)**

Part of the **Risk Metrics Layer** alongside Cross-Asset Volatility Regime Analyzer (#501).

| Original | Decision |
|----------|----------|
| #503 Conditional Value at Risk (CVaR) | Merged — tail average beyond VaR threshold |
| #504 Value at Risk (VaR) | Merged — historical percentile estimate |

## Mandatory Terminology Rules

| Rule | Implementation |
|------|----------------|
| Rename | "Value at Risk" / "Conditional Value at Risk" → **Historical Tail Risk Estimates (VaR/CVaR)** |
| No financial claims | NOT "maximum potential loss" — use "Estimated historical loss percentile based on past returns distribution" |
| Legal disclaimer | Every output: "Statistical estimate only \| Not a prediction \| Past distribution does not indicate future tail events \| No guarantee" |
| Descriptive framing | "In the worst 5% of historical days, the average was [X]" — not advisory |
| VaR + CVaR coupled | Implemented together — no standalone VaR or CVaR product |

## Formula (Historical Simulation — No ML)

```
historical_var = percentile(returns, 1 - confidence)
historical_cvar = mean(returns where return <= historical_var)
```

| Input | Description |
|-------|-------------|
| `historical_daily_returns` | Past daily return series |
| `confidence_level` | Tail percentile (default 95%) |
| `notional_usd` | Scale factor for USD display (descriptive only) |
| `lookback_days` | Historical window (default 252) |

## Sprint 1 — Data Layer

| Criterion | Target |
|-----------|--------|
| Response time | ≤ 2 seconds |
| Accuracy | ≥ 95% (backtest documented) |
| Uptime | 99% |
| Refresh | Real-time from seed/market data |

## API

| Endpoint | Scope |
|----------|-------|
| `/api/platform/intelligence-ledger/data-layer/tail-risk-metrics/status` | Feature status |
| `/api/platform/intelligence-ledger/data-layer/tail-risk-metrics?asset=BTC` | Asset tail risk |
| `/api/platform/intelligence-ledger/data-layer/tail-risk-metrics?portfolio_id=demo_balanced` | Portfolio tail risk (#504) |

## Risk Metrics Layer

```
Risk Metrics Layer
├── #501 Cross-Asset Volatility Regime Analyzer
└── #503+#504 Historical Tail Risk Estimates (VaR/CVaR)
```
