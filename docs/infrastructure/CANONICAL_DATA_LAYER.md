# Canonical Data Layer + Asset Metadata

Core infrastructure (#16 + #29). **Not a user-facing feature.**

## Purpose

- **Stable mapping:** any vendor input (symbol, alias, pair, CoinGecko id, contract) → `bd:{SYMBOL}`
- **Reference data:** labels, sectors, external IDs, chain contracts
- **Canonical pipeline:** collect → normalize → store → query

## Modules

| Module | Role |
|--------|------|
| `blackdark/canonical/schema.py` | `CanonicalAsset`, `ResolveResult` |
| `blackdark/canonical/registry.py` | Load `universe_registry.json` + `canonical_enrichment.json` |
| `blackdark/canonical/resolver.py` | `resolve_asset()`, `resolve_symbol()`, `contract_address()` |
| `blackdark/canonical/store.py` | SQLite `canonical_assets` + `canonical_records` |
| `blackdark/canonical/layer.py` | `CanonicalDataLayer` ingest/query/bootstrap |

## Stable ID format

```
bd:BTC   bd:ETH   bd:POL
```

Aliases resolve consistently: `MATIC` → `bd:POL`, `XBT` → `bd:BTC`, `BTCUSDT` → `bd:BTC`.

## Infrastructure APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/canonical/resolve?input=` | Resolve any input |
| `GET /api/platform/canonical/assets` | Reference asset list |
| `GET /api/platform/canonical/layer/status` | Layer health + bootstrap |
| `POST /api/platform/canonical/ingest` | Normalize + persist payload |

## Integration points

- `platform_universe.resolve_asset_symbol()` → canonical resolver
- `market_context.normalize_oracle_symbol()` → canonical resolver
- `data_lake.store_snapshot()` → attaches `canonical_id` on ingest
- `cap646/data_spine.normalization_report()` → canonical layer query

## Acceptance

| Criterion | Implementation |
|-----------|----------------|
| Stable mapping | Deterministic resolver + versioned registry |
| Query ≤1s | In-memory index + SQLite materialization |
| Retention ≥2y | `canonical_records` table policy (730 days) |
| Accuracy | Universe registry + explicit vendor ID maps |

## Downstream consumers

Features #5 (slippage), #10, #13 and all symbol-aware modules should call `resolve_asset()` or `resolve_symbol()` instead of local dicts.
