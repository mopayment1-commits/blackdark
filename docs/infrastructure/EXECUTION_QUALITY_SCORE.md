# Execution Quality Score — Feature #153

Institutional pattern: per exchange/asset **Execution Quality Score** — NOT a standalone marketing feature.

## Headline example

```
For $5,000 buy of ETH on Uniswap: expected slippage 2.3%.
Alternative: Binance (0.1% slippage).
```

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/infra/execution-quality/score` | Per-venue slippage comparison |
| `GET /api/platform/infra/execution-quality/status` | Module status |

## Integration

| Feature | Hook |
|---------|------|
| #119 Transfer Optimizer | `execution_quality` block on transfer response |
| #113 Net Profit | `enrich_net_profit_with_slippage()` |
| #5+#17 Slippage Intelligence | Reuses depth walk + AMM models |

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| API latency | ≤2s (`sla_met`) |
| Accuracy | ≥95% (depth walk + AMM proxy) |
| Mode | `infrastructure` — internal function |
