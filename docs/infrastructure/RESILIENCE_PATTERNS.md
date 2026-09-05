# Resilience Patterns — Circuit Breakers (#32)

**Type:** Engineering practice — NOT a product feature.  
**Pattern:** Hystrix/Resilience4j-style per-source circuit breaking on **every external API call**.

## Implementation

| Layer | Module | Behavior |
|-------|--------|----------|
| Canonical breaker | `blackdark/data/circuit_breaker.py` | 3 failures → OPEN, 300s half-open reset |
| Ingestion HTTP | `blackdark/ingestion/connector_cache.py` | `http_get` / `http_get_json` with `source_slug` |
| Legacy fetchers | `ingestion_fetchers.py` | `fetch_single_source` checks `is_open(source_id)` |
| Data engine | `blackdark/data/ingestors/*.py` | Records success/failure per source slug |
| Exchange ingress | `exchange_ingress_guard.py` | Per-exchange ban on rate-limit strikes |

## Fail-closed semantics (crypto-critical)

When circuit is **OPEN**:

1. **No live upstream call** — blocked before HTTP
2. **Stale cache allowed** — disclosed via `stale_fallback: true`, `circuit_open: true`
3. **No stale cache** → `ok: false`, `fail_closed: true` — **never invent data**

## Source slugs (ingestion layer)

| Slug | Connector |
|------|-----------|
| `binance_spot` | Binance spot ticker |
| `binance_futures` | Binance futures funding |
| `theblock` | The Block RSS |
| `investing_com` | Investing.com RSS |
| `defillama_yields` | Lending markets (#25+#26) |

## Observability

```bash
curl -s /api/platform/ingestion/data-layer/status | jq .circuit_breakers
```

Wave 01 institutional status also exposes breakers via `blackdark/data/institutional.py`.

## Adding a new connector

```python
resp = await cache.http_get_json(
    url,
    cache_key=key,
    ttl=ttl,
    source_slug="my_source",  # required for external calls
)
```

Never call external APIs without `source_slug` on shared cache helpers.
