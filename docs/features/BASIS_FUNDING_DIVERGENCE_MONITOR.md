# Basis Divergence Scanner — Feature #440

## Decision

**Sprint-2 — merged into #429 Unified Arbitrage Engine as "Derivatives Arbitrage" category.**

Renamed from "Derivatives & Futures Arbitrage" → **Basis Divergence Scanner**

Forbidden language: buy, sell, open positions, execute (شراء، بيع، فتح مراكز)

| Cancelled SLA | Replacement |
|---------------|-------------|
| Response ≤2s | Near real-time |
| Accuracy ≥95% | ±0.05% price deviation accuracy |
| Uptime 99% | Cancelled (Oracle API criteria) |
| Real-time update | Near-real-time analytics |

## Infrastructure (#146)

Invisible engineering layer — `bd_platform/intermediate_data_store.py`

- PostgreSQL: structured metadata
- InfluxDB: time-series prices/funding
- MongoDB: unstructured social/news
- Redis: hot cache
- Pipeline: collect → clean → store → query → serve

## Scanner row (required columns)

| Column | Field |
|--------|-------|
| Spot Price | `spot_price` |
| Perp Price | `perp_price` |
| Basis % (gross) | `basis_gross_pct` |
| Funding Rate (8h) | `funding_rate_8h_pct` |
| Net Basis | `net_basis_pct` |
| Feasibility | `feasibility` |

**Net Basis** = gross basis − funding accumulation (8h) − entry fees − exit fees − slippage.

Signal suppressed when `net_basis_pct ≤ 0`.

## Integrations

- **#429** — `scan_derivatives_divergence()` in unified feed with `buy_venue`/`sell_venue` legs
- **#417** — Net-Edge Truth via `enrich_opportunity()`
- **#415** — fill feasibility for proposed position size
- **#410** — risk alert when gross basis elevated
- **#427** — economics engine
- **Market Radar** — `Basis Monitor` widget (top-5)

## Routes

```
GET /api/platform/intelligence-ledger/unified-arbitrage/basis-funding/status
GET /api/platform/intelligence-ledger/unified-arbitrage/basis-funding
GET /api/platform/intelligence-ledger/unified-arbitrage/basis-funding/scan
GET /api/platform/intelligence-ledger/unified-arbitrage/basis-funding/reconciliation-tests
GET /api/platform/intelligence-ledger/market-radar/basis-monitor
```

## v1 Scope

- Monitoring only — no execution
- Display: "Gross basis X% | Net after costs Y% | Executable size: $Z"
