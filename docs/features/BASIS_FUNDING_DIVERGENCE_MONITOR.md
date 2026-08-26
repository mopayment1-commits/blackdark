# Basis/Funding Divergence Monitor — Feature #440

## Decision

**Sprint-2 — merged into #429 Unified Arbitrage Engine as "Derivatives Arbitrage" category.**

Renamed from "Derivatives & Futures Arbitrage" → **Basis/Funding Divergence Monitor**

Forbidden language: buy, sell, open positions, execute (شراء، بيع، فتح مراكز)

| Cancelled SLA | Reason |
|---------------|--------|
| Response ≤2s | Oracle API criteria |
| Accuracy ≥95% | Not applicable to monitoring |
| Uptime 99% | Cancelled |
| Real-time update | Near-real-time analytics sufficient |

## Outputs (monitoring only)

| Metric | Description |
|--------|-------------|
| `spot_perp_basis_pct` | Spot vs perpetual premium/discount |
| `funding_rate_apy` | Annualized funding rate |
| `calendar_spread_pct` | Term structure deviation (e.g. Mar vs Jun) |
| `implied_holding_cost_pct` | Fees + borrow + slippage + basis risk |
| `funding_vs_holding_cost` | 7d cumulative funding vs holding cost (no position sim v1) |
| `index_derivative_basis_pct` | Index vs derivative price divergence |

## v1 Scope

- **No position simulation** — show cumulative funding vs estimated holding cost only
- **No position recommendations** on calendar spreads
- Integrated into unified opportunity feed with `opportunity_type: derivatives_basis_funding`

## Routes

```
GET /api/platform/intelligence-ledger/unified-arbitrage/basis-funding/status
GET /api/platform/intelligence-ledger/unified-arbitrage/basis-funding
GET /api/platform/intelligence-ledger/unified-arbitrage/basis-funding/scan
GET /api/platform/intelligence-ledger/unified-arbitrage/basis-funding/reconciliation-tests
```

## Integrations

- **#429** — `scan_derivatives_divergence()` in unified feed
- **#427** — economics engine for net spread estimates
