# HA Architecture — RTO/RPO (Feature #65, silent infrastructure)

Internal engineering reference — not a user-facing product surface.

## Targets

| Metric | Target | Evidence |
|--------|--------|----------|
| RPO | ≤60 minutes | `backup_drills.jsonl` |
| RTO | ≤120 minutes | `backup_drills.jsonl` |
| Uptime SLA | 99.99% | `uptime_monitor.uptime_stats()` |
| Multi-instance | ≥2 web replicas × workers | `viral_capacity.effective_parallelism()` |

## No single point of failure

| Component | Redundancy |
|-----------|------------|
| Web tier | `docker-compose.ha.yml` — 2+ replicas behind nginx |
| Redis | Shared cache, rate limits, in-flight ceiling (local fallback) |
| Postgres | Primary + connection pool |
| Price feeds | Binance → Kraken failover, Redis OHLC cache |
| Health routing | `/health/live`, `/health/ready`, `/health/viral` |

## Graceful degradation

When Redis or parallelism is insufficient, `viral_health_payload()` returns `degraded` with `degraded_reasons[]`. Load shedding returns 503 with `Retry-After`.

## Failover testing

- Record: `POST /api/institutional/ha/failover-drill`
- Self-test: `uptime_monitor.run_failover_self_test()`
- Evidence: `data/institutional_assurance/failover_drills.jsonl`

## Runtime posture API (internal)

```python
from uptime_monitor import ha_runtime_posture, ha_architecture_status
```

Surfaced via:
- `GET /api/due-diligence/uptime`
- `scale_readiness.scale_readiness_report()`

## Load / chaos evidence

Deposit signed load proof in `docs/LOAD_TEST_RUN_LOG.md` or set `SIGNED_LOAD_EVIDENCE_JSON`.
