# Market Cap & Valuation — #266 (Sprint 1 Core Data)

Institutional valuation module: Market Cap, FDV, Dominance, historical series + QA.
**Replaces #267** (archived). Merged into **#705 Asset Metadata** + **#217 OHLCV** — NOT standalone.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Supply source/version | Every supply figure has source + version + last verified |
| Missing supply | N/A with reason — no fabricated numbers |
| Historical QA | Verified against 3 sources, variance threshold |
| FDV ≠ Market Cap | Circulating, FDV, Max Supply Market Cap shown separately |
| Dominance | Descriptive only — no buy signals |
| Historical series | 1Y trends for market cap, FDV, dominance |
| #705 integration | `market_cap_valuation` field on every asset profile |
| Replaces #267 | All #267 resources migrated to #266 |
| Disclaimer | Non-hideable |
| Methodology v2.0 | Market Cap + FDV + Dominance + Historical QA |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/valuation/status` | Module status |
| `GET /api/platform/valuation/{symbol}` | Full valuation profile |
| `GET /api/platform/connectors/assets/{stable_id}` | Includes `market_cap_valuation` via #705 |

## Related

- `bd_platform/market_cap_supply.py` — core engine (#266, replaces #267)
- `bd_platform/canonical_asset_registry.py` — #705 integration
- `bd_platform/ohlcv_core_feed.py` — #217 candle enrichment
- `data/supply_provenance_seed.json` — supply, dominance, historical data
