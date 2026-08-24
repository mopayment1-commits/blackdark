# Slippage Intelligence Module — Features #5 + #17

Unified module (NOT separate features):

| # | Capability | Function | API |
|---|------------|----------|-----|
| 5 | Slippage Tolerance Self-Optimization | `optimize_slippage_tolerance()` | `GET /api/platform/intelligence-ledger/slippage-optimize` |
| 17 | Asymmetric Slippage Cost (embedded) | `compute_asymmetric_slippage_cost()` | via slippage-optimize response (`asymmetric_slippage` field) |

## #5 Self-optimization formula

```
optimal_bps = clamp(base + vol_adj + depth_adj + gas_adj + asymmetric_adj, 10, 300)
```

## #17 Asymmetric slippage cost

Directional decomposition from CEX order-book walk (`walk_asks` / `walk_bids`) + AMM pool asymmetry:

| Output | Description |
|--------|-------------|
| `buy_slippage_bps` | Cost to buy (walk asks) |
| `sell_slippage_bps` | Cost to sell (walk bids) |
| `asymmetry_spread_bps` | \|buy − sell\| |
| `directional_bias` | `buy_heavy` / `sell_heavy` / `balanced` |
| `side_tolerance_adjustment_bps` | Fed into #5 optimal tolerance |

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| API latency | ≤2s (`sla_met`) |
| Accuracy | CEX depth walk + AMM proxy |
| Uptime | Multi-source fallbacks |

## UI

`/intelligence-ledger` → **Slippage Intelligence (#5+#17)** tab
