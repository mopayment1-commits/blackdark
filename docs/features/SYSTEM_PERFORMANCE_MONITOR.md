# System Performance Monitor — Feature #414

Sprint-0 Infrastructure observability layer (renamed from Execution_Latency_Monitor). Internal admin tool only — not a user-facing product feature.

## Endpoints (admin only)

| Route | Description |
|-------|-------------|
| `GET /api/platform/internal/system-performance/status` | Feature status |
| `GET /api/platform/internal/system-performance` | Latency dashboard + SLO breaches |
| `GET /api/platform/internal/system-performance/reconciliation-tests` | Acceptance tests |

## Principles

- Clock sync required
- Trace IDs on all spans
- p50/p95/p99 reported separately (no averaged-away tail latency)
- Stage attribution + bottleneck detection
- Load evidence from stress tests

## Systems monitored

Oracle API, Data Engine, Intelligence Ledger
