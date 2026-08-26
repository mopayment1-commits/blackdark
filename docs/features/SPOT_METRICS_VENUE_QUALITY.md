# Spot Metrics & Venue Quality Layer — #295 + #294 (Sprint 1 Data Engine)

**#294 rejected as standalone** — merged as spot overview sub-task.

| Ticket | Role |
|--------|------|
| #295 | Spot Market Metrics Suite (primary) |
| #294 | Spot overview (absorbed sub-task) |

Data Engine expansion — **no separate pipeline**. Spot metrics = aggregations + filtering on existing OHLCV/trades.

Dashboard deferred to **Sprint 2**.

## Scope Lock

| Rule | Value |
|------|-------|
| Max venues | Top 50 |
| New venue | 7-day warmup |
| Delisted venue | Archived |
| Pipeline | Sprint 1 Data Engine only |

## Venue Normalization

| Criterion | Implementation |
|-----------|----------------|
| Venue quality score | Documented per venue |
| Outlier detection | Z-score > 3 = excluded |
| Timestamp alignment | UTC |
| Source provenance | Every metric tagged |

## APIs (Data Engine)

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/data/spot-metrics/status` | Layer status |
| `GET /api/v1/data/spot-metrics` | Spot metrics panel per symbol |
| `GET /api/v1/data/venue-quality/rankings` | Venue quality rankings |

## Acceptance

- Venue normalization
- Outlier filtering (Z > 3)
- Timestamp alignment (UTC)
- Source provenance on every metric
- Outlier/stale venues filtered
