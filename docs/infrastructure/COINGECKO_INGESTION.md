# CoinGecko — Primary Data Ingestion Source (#34)

**Not a user-facing feature.** CoinGecko is the **#1 priority source** in the Data Ingestion Layer, integrated with the Canonical Data Layer (#16/#29).

## Connector

`blackdark/ingestion/coingecko_connector.py`

| Capability | Implementation |
|------------|----------------|
| Auth | `COINGECKO_API_KEY` → `x-cg-demo-api-key` header |
| Cache | `COINGECKO_CACHE_TTL_SEC` (default 3600s, max 86400s) |
| Rate limits | HTTP 429 → 60s backoff + stale cache |
| Normalization | `canonical_id` on every price/market row |
| Fallback | stale cache → Kraken public ticker |

## Fallback chain

```
CoinGecko API → stale cache (≤24h) → Kraken public
```

## Bootstrap order

`ingest_all_categories()` runs `run_coingecko_primary_ingest()` **before** all other sources.

Writes to data lake:
- `coingecko_primary` — markets + trending + global
- `coingecko_prices` — top-10 normalized price rows

## Infrastructure APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/ingestion/coingecko/status` | Connector health |
| `GET /api/platform/ingestion/coingecko/price?asset=` | Normalized price |
| `GET /api/platform/ingestion/coingecko/markets` | Top markets |
| `POST /api/platform/ingestion/coingecko/sync` | Trigger primary ingest |

## Wired consumers

- `ingestion_fetchers.py` — coingecko handlers delegate to connector
- `market_context._fetch_coingecko_ticker()` — uses connector
- `coingecko_cex_fetcher` — `coingecko_id_for_asset()` via canonical
- `cap646/data_spine` — `primary_source: coingecko`

## Acceptance

| Criterion | Target |
|-----------|--------|
| API latency | ≤3s (`sla_met` on responses) |
| Cache | 1–24 hours |
| Rate limit | 429 backoff + stale serve |
| Fallback | Kraken when API unavailable |
| Uptime | Multi-layer fallback chain |
