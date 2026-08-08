# Viral Launch Capacity — Ops Playbook

**Goal:** Absorb a sudden spike of concurrent users after a viral launch without process collapse.

## Hard rule

| Mode | Viral OK? |
|------|-----------|
| Soft Launch + SQLite + 1 worker | **NO** |
| Postgres + Redis + ≥2 parallelism + `VIRAL_MODE=true` | **YES (codepath)** |
| Signed load row in `LOAD_TEST_RUN_LOG.md` | Required before marketing HA numbers |

**Parallelism** = `WEB_CONCURRENCY` × `WEB_REPLICAS` (uvicorn workers × deploy replicas).

## Required environment

```bash
ENV=production
# SOFT_LAUNCH must be UNSET
DATABASE_URL=postgresql://…
REDIS_URL=redis://…
SERVICE_BUS_LOCAL=false
WEB_CONCURRENCY=4          # honored by run_service.py → uvicorn --workers
WEB_REPLICAS=2             # match k8s/Railway replicas
PG_POOL_MIN=4
PG_POOL_MAX=40
VIRAL_MODE=true
VIRAL_MAX_INFLIGHT=200
VIRAL_ORACLE_CONCURRENCY=32
VIRAL_ORACLE_RL_PER_MIN=60
VIRAL_AUTH_RL_PER_MIN=30
VIRAL_API_RL_PER_MIN=120
VIRAL_QUICK_CACHE_TTL_SEC=2
PRODUCTION_GUARD_FAIL_CLOSED=true
SESSION_TOKEN_PEPPER=…   # long random
SECRETS_MASTER_KEY=…     # not a known-dev default
```

Compose viral rehearsal:

```bash
docker compose up -d --scale web=2
curl -s localhost:8080/api/viral/readiness | jq .
curl -s localhost:8080/health/viral | jq .
```

## Protections shipped

1. **Load shedding** — cluster-wide Redis inflight (memory fallback) → `503` + `Retry-After`
2. **Class rate limits** — Oracle / auth / API bursts (Redis-shared when available)
3. **Oracle semaphore** — caps concurrent heavy compute per process
4. **Oracle `/quick` micro-cache** — Redis-shared stampede collapse (~2s TTL)
5. **Postgres pool** — larger min/max under `VIRAL_MODE`
6. **Real multi-worker** — `run_service.py` passes `--workers` from `WEB_CONCURRENCY`
7. **Fail-closed boot** — strict prod + `VIRAL_MODE` requires Redis + multi-instance in `production_guard`
8. **Probes** — `/health/viral` + Redis gate on `/health/ready` in viral prod
9. **k8s** — web HPA min 2 + Service (`deploy/k8s/*`)

## Verify before campaign

```bash
curl -s "$BASE/api/viral/readiness" | jq .
curl -s "$BASE/health/viral" | jq .
curl -s "$BASE/api/production/guard" | jq .
python scripts/load_test_concurrent.py --base "$BASE" --workers 40 --requests 200 --require-viral-approved
# Append signed Postgres+Redis multi-worker results to docs/LOAD_TEST_RUN_LOG.md
```

`viral_production_approved=true` means codepath + env prerequisites look good — **not** infinite capacity.

## What still fails closed / honestly

- Soft Launch is demo-only
- Without Redis, rate limits / inflight / cache are per-process (weaker under multi-replica) — viral approval requires live Redis
- CDN in front of `/` and `/static` is recommended (edge) for pure page views
- Do not promise “zero problems under any traffic” — promise **controlled degradation** (429/503) instead of collapse
