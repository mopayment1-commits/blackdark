# Cross-Exchange Funding & Derivatives Expansion — #317 #325 #328 #329

## #317 Cross-Exchange Funding Rate Analytics — 🟡 Wave 2

Renamed from **Cross-Exchange Funding Arbitrage Scanner**.

| Rule | Implementation |
|------|----------------|
| No "arbitrage" / "scanner" / "opportunities" | Funding rate comparison table only |
| Output format | APR with fee model; Net = gross minus fees; Capacity = OI-based estimate |
| Stale data | Funding rate > 1 hour = flagged |
| Unknown venue | Excluded |
| Asset-class integrity | Perp vs spot verified |
| Disclaimer | No recommendation; execution risk = user responsibility |

API: `/api/platform/intelligence-ledger/cross-exchange-funding/*`

## #325 Derivatives Data — 🔴 Rejected standalone

Merged into **Instrument Master (#268)** as **Derivatives Asset Class Expansion**.

- Futures/perp contract → unified instrument ID
- Expiry normalized; funding interval documented; index reference source tagged
- No separate pipeline — additional `asset_class` tag in Sprint 1 Data Engine schema

API: `/api/v1/data/instrument-master/derivatives-contracts`

## #328 Derivatives Regime Engine — 🔴 Rejected standalone

Merged into **Derivatives Market State Module (#327)** as **Regime Classification Sub-component**.

- Rule-based crowded/flush/normal classification
- Formula versioned; backtest gate required

## #329 Estimated Leverage Ratio — 🔴 Rejected standalone

Merged into **Derivatives Market State Module (#327)** as **Estimated Leverage Ratio contributor metric**.

| Rule | Implementation |
|------|----------------|
| Formula | ELR = OI / Exchange Reserve (versioned) |
| Variants | OI_deribit/Reserve_deribit; OI_total/Reserve_total |
| Zero/missing | Reserve = 0 or missing → ELR = N/A |
| Percentile | 90-day rolling window; recomputed daily |
