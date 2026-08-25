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
- `bd_platform/b2b_sla_monitoring.py` — #231 B2B Query Latency SLA (merged tab)
- `stale_price_guard.py` — execution quote freshness
- `bd_platform/block_level_ingestion.py` — block stream freshness labels

## #231 B2B SLA Monitoring Tab (merged)

| Rule | Implementation |
|------|----------------|
| API p95 ≤ 3s | `Latency: p50=200ms \| p95=1.8s \| p99=2.5s \| SLO: 3s` |
| Uptime 99% | Per endpoint per month with SLA credit tracking |
| Rate limit handling | Graceful degradation — Normal/Throttled/Blocked with explanation |
| Tier cache 1-24H | Free: 1H \| Pro: 4H \| Enterprise: 24H + bypass |
| Fallback | Primary Oracle API v2.1 \| Backup Feed v1.9 \| auto-switch |
| Enterprise only | Internal admin, enterprise portal, SLA reports |
| No instant claims | `Update Frequency: Real-time (p95 < 500ms) \| Cached: No` |
| #162 middleware | Latency monitoring built over Oracle API endpoints |

### B2B SLA APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/freshness/b2b-sla/status` | #231 module status |
| `GET /api/platform/freshness/b2b-sla/dashboard` | Enterprise SLA dashboard tab |
| `GET /api/platform/freshness/b2b-sla/endpoints/{path}` | Per-endpoint latency + uptime |
| `GET /api/platform/freshness/b2b-sla/rate-limit` | Rate limit status |
| `GET /api/platform/freshness/b2b-sla/fallback` | Primary/fallback status |
| `GET /api/platform/freshness/b2b-sla/cache-policy` | Tier-based cache policy |
