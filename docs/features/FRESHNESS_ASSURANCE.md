# Freshness Assurance Layer — #219 (Sprint 0)

Real-Time Data Freshness & Update Assurance. WebSocket (#222) = transport mechanism within this layer.

## Institutional Rules

| Rule | Implementation |
|------|----------------|
| Clock sync | NTP-synced across all nodes |
| Timestamp separation | `Source: 14:00:00 UTC \| Received: 14:00:00.250 UTC \| Latency: 250ms` |
| No stale→0 | Stale data = `null`, never `0` |
| Fail-closed | Exceed threshold → `"Data Stale"` not old number |
| Percentile evidence | `p50: 200ms \| p95: 800ms \| p99: 1.5s` |
| Historical retention | Freshness trend over time |
| Automated tests | Delayed/missing/out-of-order every 5 min |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/freshness/status` | Module status |
| `GET /api/platform/freshness/clock-sync` | NTP sync status |
| `GET /api/platform/freshness/dashboard` | Live freshness dashboard |
| `GET /api/platform/freshness/feeds/{id}` | Per-feed age/latency/stale |
| `GET /api/platform/freshness/feeds/{id}/percentiles` | p50/p95/p99 |
| `GET /api/platform/freshness/feeds/{id}/history` | Historical retention |
| `GET /api/platform/freshness/health-check` | Automated feed tests |
| `WS /ws/platform/stream` | WebSocket transport (#222) |

## Related

- `bd_platform/streaming_infrastructure.py` — #218 ingestion/distribution
- `stale_price_guard.py` — execution quote freshness
- `bd_platform/block_level_ingestion.py` — block stream freshness labels
