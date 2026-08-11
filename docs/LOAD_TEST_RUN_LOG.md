# Load Test Run Log

Use this log after running harnesses against a **Postgres + Redis** staging/production-like stack.

## Commands

```bash
# Buyer DD probes (app core; sidecar optional)
python scripts/load_test.py --base http://127.0.0.1:8080 --requests 100

# Concurrent diligence harness (health, trust-os, viral, oracle quick, arb, compliance)
# 429/503 = controlled degradation (OK) unless --strict-2xx
python scripts/load_test_concurrent.py --base http://127.0.0.1:8080 --workers 40 --requests 200 --require-viral-approved

# Scale + viral readiness JSON (codepath honesty — not a signed capacity proof)
curl -s http://127.0.0.1:8080/api/scale/readiness | jq .
curl -s http://127.0.0.1:8080/api/viral/readiness | jq .
curl -s http://127.0.0.1:8080/health/viral | jq .

# 60-second grasp machine probe
python scripts/acceptance_60s.py --base http://127.0.0.1:8080

# Heavier simulation (if available)
python scripts/load_test_1m_simulation.py
```

## Required environment for an honest HA claim

- `ENV=production` or Soft Launch documented explicitly  
- `DATABASE_URL=postgresql://…`  
- `REDIS_URL=redis://…`  
- `WEB_CONCURRENCY` × `WEB_REPLICAS` ≥ 2 (uvicorn workers × deploy replicas)  
- `VIRAL_MODE=true` and Soft Launch unset for viral approval  


## Run template (fill after each run)

| Field | Value |
|-------|--------|
| Date (UTC) | |
| Environment | staging / prod-like |
| Workers / replicas | |
| Postgres | yes / no |
| Redis | yes / no |
| Script | `load_test.py` / other |
| Requests | |
| p50 / p95 / p99 (ms) | |
| Error rate | |
| Notes | |
| Operator | |

## Recorded runs

### 2026-08-11T21:39:09Z — local Soft Launch + Postgres/Redis (NOT signed HA multi-worker proof)

| Field | Value |
|-------|--------|
| Date (UTC) | 2026-08-11T21:39:09Z |
| Commit intent | _(parent fills)_ |
| Environment | local Soft Launch (`SOFT_LAUNCH=true`, `ENV=development`, single uvicorn worker via `run_service.py web`) |
| Workers / replicas | 1 × 1 (`WEB_CONCURRENCY=1`, parallelism=1) |
| Postgres | yes (`postgresql://…@127.0.0.1:5432/blackdark`, pool active) |
| Redis | yes (`redis://127.0.0.1:6379/0`; viral readiness `rate_limit_backend=redis`, `inflight_backend=redis`) |
| Infra limits | Single process; Soft Launch; `viral_production_approved=false`; `ha_ready_codepath=false`; not multi-worker / not multi-replica |
| Script | `scripts/load_test.py` (50 req/endpoint) + `scripts/load_test_concurrent.py` (10 workers × 50 req/endpoint, no `--require-viral-approved`) |
| Requests | 50 sequential/core; 50 concurrent/endpoint |
| Results (sequential) | app_live p50/p95=1/2ms · ready 1/2ms · trust_os 2/2ms · strategy_correction 2/2ms · ledger_page 2/3ms (errors 31/50) · sidecar_live 0/0ms · core harness PASS |
| Results (concurrent) | live ok_rate=1.0 p50/p95=12.5/13.1ms · ready 1.0 11.5/12.4ms · oracle_quick 1.0 28.7/664.8ms · compliance_html 1.0 16.8/33.9ms · viral_health/trust_os/scale_readiness/viral_readiness/arb_scan capacity_ok_rate=1.0 via controlled 429 (ok_rate=0.0) |
| Error / degradation | Controlled 429 under concurrent API burst (expected Soft Launch / rate-limit protection). Not collapse. |
| Notes | **NOT signed HA multi-worker proof.** Redis was live and used for shared rate-limit/inflight backends, but workers/replicas=1 and Soft Launch remains on — does **not** unlock proven 1k–10k concurrent production capacity or DEC-0407. Re-run with Postgres+Redis, `SOFT_LAUNCH` unset, `WEB_CONCURRENCY`×`WEB_REPLICAS`≥2, and `viral_production_approved=true` before any HA claim. |
| Operator | cloud-agent load-evidence probe (no commit) |

### 2026-08-08 — local Soft Launch (NOT an HA capacity claim)

| Field | Value |
|-------|--------|
| Date (UTC) | 2026-08-08 |
| Environment | local Soft Launch (`SOFT_LAUNCH=1`, single uvicorn worker) |
| Workers / replicas | 1 |
| Postgres | no |
| Redis | no |
| Script | `scripts/load_test.py` |
| Requests | 40 per endpoint |
| Results | app_live p50/p95 ≈ 1ms · ready ≈ 1ms · trust_os ≈ 1ms · strategy_correction ≈ 1ms · ledger_page ≈ 1ms · errors 0/40 on core |
| Sidecar | not running (optional; recorded as ALL FAILED) |
| Acceptance 60s | `machine_pass=true` (8/9 probes; oracle `/quick` restored after `get_top_of_book` fix) |
| Notes | **Does not unlock** proven 1k–10k concurrent production capacity. Re-run on Postgres+Redis multi-worker staging before any HA claim. |
| Operator | cloud-agent expert-execution-closure |

## Status

- [x] Local Soft Launch buyer-DD probe recorded (honest, non-HA)  
- [x] Local Soft Launch with Postgres+Redis single-worker probe recorded (honest, **still non-HA**)  
- [ ] First signed HA run on Postgres+Redis multi-worker recorded above  
- [ ] Results attached to acquirer evidence pack discussion  

Until a Postgres+Redis multi-worker row is filled, do **not** claim proven 1k–10k concurrent production capacity.
