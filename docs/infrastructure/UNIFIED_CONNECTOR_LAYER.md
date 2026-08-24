# Unified Connector Layer — Feature #194 (Sprint 0)

## Role

Foundation for #133 (price aggregation) and #127 (live refresh). Provides a **canonical schema** and **connector registry** for multi-exchange price data.

**Not user-facing** — feeds internal price engines only.

## Canonical Schema

`CanonicalPriceQuote` fields:

| Field | Description |
|-------|-------------|
| `connector_id` | Registry key (e.g. `binance`, `ws_binance`) |
| `exchange` | Venue name |
| `asset` | Base symbol (e.g. `BTC`) |
| `pair` | Trading pair |
| `price_usd` | Last/mid price |
| `bid` / `ask` | Top of book when available |
| `volume_24h_usd` | 24h quote volume for VWAP |
| `canonical_id` | Resolved via `blackdark.canonical.resolver` |
| `source` | Provenance string (e.g. `binance:api.binance.com`) |
| `latency_ms` | Fetch latency |
| `is_stale` | WS/Redis staleness flag |

## Registered Connectors (initial)

`binance`, `okx`, `bybit`, `kraken`, `coinbase`, `coingecko`, `gateio`, `kucoin`, `mexc`, `bitget`

Plus live WS path: `ws_binance`, `ws_okx`, `ws_bybit` via Redis.

**Expansion target:** 400+ exchanges via connector registry growth.

## API

`GET /api/platform/infra/connectors/status` — registry health and schema info.

## Design Principles

1. **Canonical schema** — one shape for all venues
2. **Parallel fetch** — `asyncio.gather` for SLA
3. **Source metadata** — every quote traceable to origin
4. **Extensible registry** — add connectors without changing aggregation logic
