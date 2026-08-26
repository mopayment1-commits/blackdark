# Asset Screener & Filter Engine — #1008

## 🟢 Sprint 2 — Product feature

Builds on **#742 Smart Screener** (Sprint 1 Market Radar) with full backend filter engine.

## Mandatory rules

1. **Backend enforcement** — All filters server-side; no client-side only; pagination mandatory; max 1000 results per query
2. **Deterministic sorting** — Same query = same order; tie-breaker = market cap desc
3. **Missing data** — Excluded by default; option `include_missing=true` shows "N/A"; no fabricated zeros
4. **Presets versioned** — Built-in presets versioned; user presets saved; export CSV/JSON

## Metric categories

| Category | Fields |
|----------|--------|
| Market | market_cap_usd, volume_24h_usd, price_change_24h_pct |
| On-chain | onchain_signal, bot_activity_score, mvrv_z |
| Derivatives | funding_rate, open_interest_usd |
| Fundamental | yield_pct, tvl_usd |

## API

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/platform/intelligence-ledger/asset-screener/status` | GET | Status + acceptance criteria |
| `/api/platform/intelligence-ledger/asset-screener/presets` | GET | Built-in + user presets |
| `/api/platform/intelligence-ledger/asset-screener` | GET | Run with preset / pagination |
| `/api/platform/intelligence-ledger/asset-screener` | POST | Run with filter body (server-side) |
| `/api/platform/intelligence-ledger/asset-screener/export` | GET | Export CSV or JSON |

## Acceptance criteria

- Filters enforced backend ✅
- Pagination mandatory ✅
- Deterministic sorting ✅
- Missing data handling ✅
- Presets versioned ✅
- Export CSV/JSON ✅
