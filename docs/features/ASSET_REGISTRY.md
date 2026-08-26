# Asset Registry — Feature #402

## Decision

**Sprint 1 Data Engine completion — Medium priority, NOT standalone.**

| Scope | Status |
|-------|--------|
| Seed 105 coins (#101–#205) in Data Engine `assets` table | ✅ Implemented |
| Asset Metadata enrichment (sector, chain, tier, risk, volatility) | ✅ Implemented |
| Asset Scoring Layer (risk, liquidity, on-chain health 0–100) | ✅ Implemented |
| Market Radar + Portfolio AI + Intelligence Ledger integration | ✅ Mandatory |
| Account/wallet data | ❌ Cancelled (non-custodial) |
| Duplicate Oracle cache/rate-limits/fallback | ❌ Delegated to Oracle API (#274) |
| Standalone ≤3s / 99% uptime criteria | ❌ Cancelled (Oracle API owns) |

Extends **#516 Asset Intelligence Profiles** — does not replace it.

## API

```
GET /api/platform/intelligence-ledger/data-layer/asset-registry/status
GET /api/platform/intelligence-ledger/data-layer/asset-registry?symbol=BTC
GET /api/platform/intelligence-ledger/data-layer/asset-registry/universe
GET /api/platform/intelligence-ledger/data-layer/asset-registry/reconciliation-tests
GET /api/platform/intelligence-ledger/market-radar/asset-registry
GET /api/platform/intelligence-ledger/portfolio-ai/asset-registry?symbol=ETH
GET /api/platform/intelligence-ledger/intelligence-layer/asset-registry
```

## Universe

105 assets ranked #101–#205: BTC through GAL.

Alias resolution:
- `MATIC` → `asset_pol` (Polygon POL)
- `SKY` → `asset_mkr` (Maker/Sky rebrand)
- `MANA` (Decentraland) distinct from `MANTA` (Manta Network)

## Scoring Layer

Analytics indices (0–100), not investment advice:

| Index | Description |
|-------|-------------|
| `risk_score` | Volatility + classification composite |
| `liquidity_score` | Market cap tier + depth proxy |
| `onchain_health_score` | Chain activity proxy |

## Data Engine Hook

`market_data_engine_status()` includes `asset_registry` block via `build_data_engine_asset_registry_block()`.

## Evidence

Seed data labeled `BACKTESTED`. Live market prices via Oracle API — not duplicated here.
