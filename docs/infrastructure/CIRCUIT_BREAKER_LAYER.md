# Circuit Breaker Layer (#1051)

**Sprint 0/1 · Infrastructure · NOT standalone**

Resilience layer preventing cascading failure when a service degrades.

## Defense sequence

```
Rate Limit (#1046) → Circuit Breaker (#1051) → DDoS (#1047)
```

## Triggers (rule-based)

| Trigger | Threshold |
|---------|-----------|
| Error rate | >50% in 60 seconds |
| Latency | >2× baseline in 60 seconds |
| Resource | CPU/memory >90% |

## Recovery

Exponential backoff: 30s → 1min → 5min → half-open probe → close if healthy.

## User impact

Circuit open = **"Service Degraded"** badge (#1030) + cached/stale fallback — no blank error page.

## API

| Endpoint | Description |
|----------|-------------|
| `GET /api/platform/circuit-breaker/{status,gate,e2e}` | Policy + service states |

## Audit

`data/circuit_breaker_audit.jsonl` — trip/close/half-open events (#1038).

## Integrations

- #1025 Automatic Failover — trip triggers secondary
- #1017 Incident Response — >3 trips/hour = alert
- #945 Provenance — cached data flagged stale
