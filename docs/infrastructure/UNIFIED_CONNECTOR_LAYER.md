# Unified Connector Layer — Feature #194 (merged with #175)

## Role

Foundation for #133 (price aggregation), #127 (live refresh), and #137 (data ingestion).
**Merged with #175 Flexible Connector Microservice** — single unified connector stack.

**Not user-facing** — feeds internal price engines and ingestion layer only.

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
| `source` | Provenance string |
| `latency_ms` | Fetch latency |
| `is_stale` | WS/Redis staleness flag |

## Symbol Normalization

`BTCUSDT` (Binance) = `BTC-USD` (Coinbase) = `BTC_USDT` (internal schema)

All timestamps normalized to **UTC**.

## Connector Types

| Type | Connectors | Role |
|------|-----------|------|
| Primary | binance, okx, bybit, kraken, coinbase, gateio, kucoin, mexc, bitget | First-class exchange APIs |
| Aggregator (#138) | coingecko | Backup + cross-reference only |

## Policies

1. **No venue-specific leakage** — users see "Source temporarily unavailable", not "Binance API error"
2. **Health heartbeat** — every 60 seconds
3. **Retries** — 3 attempts with backoff (#175)
4. **Version tracking** — connector version in status

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/infra/connectors/status` | Registry (#194) |
| `GET /api/platform/infra/connectors/registry` | User-visible health (#175) |
| `GET /api/platform/infra/ingestion/status` | Ingestion layer (#137) |

## Design Principles

1. Canonical schema — one shape for all venues
2. Parallel fetch — `asyncio.gather` for SLA
3. Source metadata — every quote traceable
4. Aggregator cross-reference — never sole data source (#138)
