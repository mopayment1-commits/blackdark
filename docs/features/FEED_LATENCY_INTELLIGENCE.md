# Feed Latency / Data Freshness — Feature #111

Informational Market Radar layer (Wave 2, **Pro tier**). Compares price freshness
between fast WebSocket feeds and slower REST-polled exchanges.

**Not execution advice** — no profit promises. Never labeled "استغلال" in product UI.

## Example output

> Price on Gate.io is 0.3% behind live data

> Binance updates ~every 100ms; MEXC REST ~every 5s

## APIs

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/market-radar/feed-latency` | Pro+ | Single-asset comparison |
| `GET /api/platform/market-radar/feed-latency/overview` | Pro+ | Multi-asset snapshot |
| `GET /api/market/feed-latency` | Public | Informational snapshot (no tier gate) |

Market Radar narrative (`/api/market/radar-narrative`) includes `feed_latency` block.

## Data flow

1. **Fast reference** — `live_book_hub` WebSocket (Binance, OKX, Bybit, Kraken)
2. **Slow venues** — REST poll (Coinbase, Gate.io, KuCoin, etc.)
3. **Fallback** — Binance REST → CoinGecko

## Acceptance criteria

| Criterion | Target |
|-----------|--------|
| API latency | ≤3s (`sla_met`) |
| Cache | Hot 60s / warm 1h / cold 24h |
| Rate limits | Per-domain throttle + graceful fetch_failed |
| Fallback | `live_book_hub` → `binance_rest` → `coingecko` |
| Mode | `informational_only` |

## Tier gating

`feed_latency: true` in `auth_service.TIER_FEATURES` for Pro, Elite, Whale, Quant, Institutional.
