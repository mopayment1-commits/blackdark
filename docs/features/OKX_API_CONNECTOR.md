# Feature #80 — OKX API (Silent Data Layer)

OKX spot + perpetual swap market data integrated silently into analysis.

## Scope

**NOT a branded OKX product** — users see *"OKX futures data included in analysis"*.

## Connector

- Module: `blackdark/ingestion/okx_connector.py`
- Optional `OKX_API_KEY` (public endpoints work without auth)
- Cache: `OKX_CACHE_TTL_SEC` (default 300s, max 24h)
- Circuit breakers: `okx_spot`, `okx_swap`
- Fallback: stale cache → Binance spot/futures

## Acceptance

| Criterion | Implementation |
|-----------|----------------|
| API ≤3s | `sla_met` on every response |
| Rate limits | `IngestionCache` 429 backoff |
| Cache 1–24h | `OKX_CACHE_TTL_SEC` env |
| Fallback | Binance connector chain |

## APIs

| Endpoint | Purpose |
|----------|---------|
| `GET /api/platform/okx/ticker?asset=BTC` | Spot + swap context |
| `GET /api/platform/okx/status` | Connector health |
| `decision_engine_inputs.okx_market` | Funding risk delta |

## Wired consumers

- `ingestion_fetchers.py` — `okx_spot`, `okx_swap`
- `decision_engine_inputs.py`
- `GET /api/platform/ingestion/data-layer/status`
