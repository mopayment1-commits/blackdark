# Price Feed Layer — #283 (Sprint 0 Infrastructure)

**Rejected as standalone feature** — exists as Sprint 0 foundation.

NOT a product. NOT a separate dashboard. UI: Landing Page + Market Radar.

## Institutional Decision

| Aspect | Decision |
|--------|----------|
| Standalone #283 | ❌ Archived |
| Build as | Sprint 0 Price Feed Layer |
| Live charts | Frontend requirement (deferred) |
| Serves | All platform surfaces |

## Acceptance Criteria

| Criterion | Implementation |
|-----------|----------------|
| Latency visible | On every quote output |
| Freshness visible | `snapshot_age_ms`, stale flag |
| No standalone dashboard | `archived_standalone_ticket` |

## APIs

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/price-feed/status` | Infrastructure status |
| `GET /api/platform/price-feed/live` | Live prices with freshness |

## Integration

- `live_book_hub.py` — WebSocket top-of-book
- `bd_platform/free_market_data.py` — REST fallback
- Landing Page + Market Radar (UI deferred)
