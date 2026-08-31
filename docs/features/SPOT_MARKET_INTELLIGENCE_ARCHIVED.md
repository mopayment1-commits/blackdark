# Spot Market Intelligence — #294 ARCHIVED

**Decision:** 🔴 Reject as standalone — merge into #295 Spot Market Metrics Suite.

## Rationale

#294 (Spot Market Intelligence) duplicates #295 (Spot Market Metrics Suite). #295 is more detailed and covers price, volume, returns, volatility, and market structure with venue normalization.

## Implementation

- No standalone module
- Absorbed as `spot_overview` sub-task in `blackdark/data/spot_metrics_venue_quality.py`
- Outlier/stale venue filtering handled by #295 venue quality layer

## Related

- **#295** — Spot Metrics & Venue Quality Layer (Wave 01 Data Engine, Sprint 1)
- Dashboard deferred to Sprint 2
