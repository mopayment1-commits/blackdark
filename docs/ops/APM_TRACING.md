# APM & Distributed Tracing (#1061)

**Merged into:** Sprint-0 Infrastructure — NOT standalone.

## Metrics (8+ dimensions)

latency p50/p95/p99 · throughput · error rate · CPU · memory · DB connections · cache hit rate

## Rule-based alerts (Sprint 2 — no ML)

1. latency p95 >2× baseline
2. error rate >1%
3. memory >85%
4. DB connections >80% pool

Baselines calibrated from #1020 Load Testing — recalculated monthly.

## API

```
GET /api/platform/internal/infrastructure/apm/status
GET /api/platform/internal/infrastructure/apm/dashboard
GET /api/platform/internal/infrastructure/apm/e2e
```

## Integrations

#1059 Uptime · #1060 Logging · #1051 Circuit Breakers · #1017 Incident Response · #955 Decision Trace
