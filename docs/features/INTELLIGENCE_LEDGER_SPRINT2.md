# Intelligence Ledger — Sprint 2

Sprint 2 hub for execution intelligence. **1inch is a data source inside this ledger**, not a standalone product surface.

| # | Feature | Module | API | UI Tab |
|---|---------|--------|-----|--------|
| 5 | Slippage Intelligence Module (#5+#17) | `bd_platform/slippage_tolerance_optimizer.py` | `GET /api/platform/intelligence-ledger/slippage-optimize` | Slippage Intelligence (#5+#17) |
| 6 | 1inch Network (embedded) | `bd_platform/oneinch_connector.py` | via `GET /api/platform/intelligence-ledger/execution` | Execution Intelligence |

## Self-optimization logic (Feature #5)

Transparent formula:

```
optimal_bps = clamp(base + vol_adj + depth_adj + gas_adj, 10, 300)
```

| Input | Source | Effect |
|-------|--------|--------|
| Volatility | Binance 24h % change (DexScreener fallback) | Higher vol → wider tolerance |
| Liquidity depth | Binance quote volume proxy or DexScreener pool USD | Thin pool vs trade size → wider |
| Gas costs | `gas_oracle.gas_cost_bps` | Higher gas % of notional → slightly wider |

## 1inch integration (Feature #6)

- Live `api.1inch.dev` quote when `ONEINCH_API_KEY` is set
- DexScreener 1inch pool fallback (always available)
- TTL cache: default 1h (`ONEINCH_CACHE_TTL_SEC`, max 24h)
- Rate-limit backoff on HTTP 429
- Normalized into `build_execution_intelligence()` alongside AMM + CEX routes

## Execution ranking

Routes ranked by `effective_cost_bps` = price deviation penalty + slippage + gas.

## Acceptance criteria

| Criterion | Target | Implementation |
|-----------|--------|----------------|
| Slippage API latency | ≤2s | `sla_met` on optimizer response |
| Execution API latency | ≤3s | `sla_met` on ledger response |
| 1inch cache | 1–24h | `ONEINCH_CACHE_TTL_SEC` |
| Fallback | Required | DexScreener when API/key unavailable |
| Uptime | 99% | Multi-source fallbacks + cache |

## UI

`/intelligence-ledger` — Sprint 2 dashboard with Execution Intelligence and Slippage tabs.
