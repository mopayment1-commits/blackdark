# BLACKDARK Institutional SLA (Template)

| Metric | Target |
|--------|--------|
| Monthly availability | 99.5% |
| API p95 | ≤ 800ms |
| Oracle p95 | ≤ 2500ms |
| P0 support response | 1h |
| P1 support response | 4h |

Capacity claims require a verified signed capacity row (`POST /api/institutional/capacity`) with Postgres + Redis + workers ≥ 2.
