# Price Aggregation Engine — Features #133 + #127 (Sprint 0)

## Role

**Invisible infrastructure** — users expect prices to update automatically. This is not a user-facing marketing feature.

| Feature | Role |
|---------|------|
| **#133** | Collect, outlier-filter, volume-weight, attach source metadata |
| **#127** | Live refresh via WS/Redis → REST fallback |
| **#194** | Unified Connector Layer — canonical schema across venues |

## Pipeline

1. **Collect** — parallel fetch from 10+ connectors (#194)
2. **Outlier filter** — >2.5% from median flagged as likely API error
3. **Volume-weight** — VWAP when volume available, equal-weight fallback
4. **Source metadata** — provenance per connector (where did this price come from?)
5. **Live refresh** — prefer WS/Redis top-of-book (#127 + #128 sub-second path)
6. **Persist** — snapshots to `data/price_aggregation_snapshots.jsonl` + Redis cache (5s TTL)

## API (ops / internal)

| Endpoint | Auth | Description |
|----------|------|-------------|
| `GET /api/platform/infra/prices/aggregate?asset=BTC` | Public | Aggregated price with outlier filtering |
| `GET /api/platform/infra/prices/live?asset=BTC` | Public | Invisible live refresh result |
| `GET /api/platform/infra/prices/status` | Public | Pipeline health |
| `GET /api/platform/infra/connectors/status` | Public | Connector registry (#194) |

All responses include `sla_met` (≤2s target) and `user_facing: false`.

## Acceptance

- Response latency ≤ 2 seconds
- Accuracy estimate ≥ 95% (outlier removal)
- Source metadata on every quote
- Live path when WS/Redis available
- 2-second in-process cache for repeat reads

## Integration

- **#118 ETL** — optional downstream persistence via `local_data_etl`
- **#128 sub-second** — WS tick ingress via `price_stream_engine` + `redis_price_cache`
- **Canonical schema** — `CanonicalPriceQuote` in `unified_connector_layer.py`
