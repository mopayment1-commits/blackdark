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

### 2026-08-12T00:07:00Z — Soft Launch tip concurrent burst @ `73818e2` (NOT signed HA)

| Field | Value |
|-------|--------|
| Date (UTC) | 2026-08-12T00:07:00Z |
| Commit | `73818e24635d2b6be8483127dcb2d37e0aadef6c` |
| Environment | local Soft Launch / single uvicorn worker |
| Workers / replicas | 1 × 1 |
| Postgres | yes |
| Redis | yes |
| Script | `load_test_concurrent.py --workers 40 --requests 80` |
| Results | live p50/p95=51.8/57.6ms ok=1.0 · ready 46.6/55.1 · trust_os 69.1/76.9 · oracle_quick 446/1448 ok=0.75 · controlled 429 elsewhere |
| Error rate | hard errors=0 |
| Notes | **NEEDS_EXTERNAL_VERIFICATION for DEC-0407** |
| Operator | cloud-agent |


### 2026-08-11T23:48:40Z — Soft Launch tip concurrent burst @ `31a492e` (NOT signed HA)

| Field | Value |
|-------|--------|
| Date (UTC) | 2026-08-11T23:48:40Z |
| Commit | `31a492e105d37c3c391a990a1789670804580914` (`cursor/institutional-hardening-120d`) |
| Environment | local Soft Launch / single uvicorn worker on `127.0.0.1:8080` |
| Workers / replicas | 1 × 1 (`parallelism=1`; viral approved=False) |
| Postgres | yes (accepting on `127.0.0.1:5432`) |
| Redis | yes (`used_memory` 1.09M → 1.12M during burst) |
| Script | `scripts/load_test_concurrent.py --workers 40 --requests 120` |
| HTTP concurrency | 40 workers |
| Results | live p50/p95=53.6/56.4ms ok_rate=1.0 · ready 52.3/53.4 · trust_os 74.8/139.8 · compliance 68.3/70.8 · oracle_quick 142.3/1401.6 ok_rate=0.5 · viral/scale/arb capacity_ok via controlled 429 |
| Error rate | hard errors=0; controlled 429 on capacity-gated routes |
| Process | uvicorn RSS≈160MB, ~0.1% CPU at idle after burst |
| Notes | **NEEDS_EXTERNAL_VERIFICATION for DEC-0407 signed HA.** Not multi-worker / multi-replica. |
| Operator | cloud-agent one-shot closure |


### 2026-08-11T23:00:29Z — Soft Launch Postgres+Redis concurrent burst (NOT signed HA)

| Field | Value |
|-------|--------|
| Date (UTC) | 2026-08-11T23:00:29Z |
| Commit intent | tip before closure commit on `cursor/institutional-hardening-120d` (post-Ruff cherry-pick `518b018`) |
| Environment | local Soft Launch (`SOFT_LAUNCH=true`, `ENV=development`, single uvicorn worker) |
| Workers / replicas | 1 × 1 |
| Postgres | yes (`postgresql://blackdark@127.0.0.1:5432/blackdark`) |
| Redis | yes (`redis://127.0.0.1:6379/0`, used_memory≈1.1M) |
| Infra limits | Single process; Soft Launch rate-limits; **not** multi-worker / multi-replica HA |
| Script | `scripts/load_test.py` (50) + `scripts/load_test_concurrent.py` (20 workers × 100 req/endpoint) |
| Results (sequential) | app_live p50/p95=2/2ms · ready 1/2 · trust_os 2/2 · strategy_correction 2/2 · ledger_page 2/3 (errors 30/50) · sidecar_live 0/0 · harness PASS |
| Results (concurrent) | live ok_rate=1.0 p50/p95=28.4/32.9ms · ready 1.0 26.1/181.1ms · compliance_html 1.0 34.6/40.0ms · oracle_quick ok_rate=0.6 p95=769.4ms · viral/trust_os/scale/arb capacity_ok_rate=1.0 via controlled 429 |
| Error / degradation | Controlled 429 under burst (Soft Launch / viral protection). No process collapse. |
| Notes | **NEEDS_EXTERNAL_VERIFICATION for DEC-0407 signed HA.** Re-run with `WEB_CONCURRENCY`×`WEB_REPLICAS`≥2, Soft Launch unset, viral production approved. |
| Operator | cloud-agent one-shot closure |


### 2026-08-11T21:39:09Z — local Soft Launch + Postgres/Redis (NOT signed HA multi-worker proof)

| Field | Value |
|-------|--------|
| Date (UTC) | 2026-08-11T21:39:09Z |
| Commit intent | tip `b8698ea0d5031f9f44d48f41d806b5d720da8d8a` / evidence `f1a4815c7f87db6526619c8fcd3406ea1d2c2403` |
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

### 2026-08-12T06:33:53Z — signed HA multi-worker (Postgres+Redis, Soft Launch off)

| Field | Value |
|-------|--------|
| Date (UTC) | 2026-08-12T06:33:53Z |
| Commit / tip | `0839637a95dbc2ded5428f40c25777b17384a796` (HA code tip `9bae7c48c630d60654a5d8f09e1f9535b60a8c00`) |
| Environment | local HA rehearsal: `ENV=production`, `VIRAL_MODE=true`, Soft Launch **unset**, ephemeral local secrets for production-guard gates (not live Stripe) |
| Workers / replicas | **2 × 1** (`WEB_CONCURRENCY=2`, `WEB_REPLICAS=1`, parallelism=2 via uvicorn `--workers 2`) |
| Postgres | yes (`postgresql://blackdark:***@127.0.0.1:5432/blackdark_clean`, pool active min=4 max=20) |
| Redis | yes (`redis://127.0.0.1:6379/0`; `rate_limit_backend=redis`, `inflight_backend=redis`, used_memory≈1.1M) |
| HA / viral gates | `ha_ready_codepath=true`, `viral_production_approved=true`, `viral_codepath_ready=true`, Soft Launch false |
| Script | `scripts/load_test.py` (50) + `scripts/load_test_concurrent.py` (40 workers × 200 req/endpoint, `--require-viral-approved`) |
| Concurrency | 40 client threads; 200 requests/endpoint; server workers=2 |
| Throughput (live) | 200/200 ok in concurrent wave; capacity_ok_rate=1.0 on all scored endpoints |
| Latency | sequential live p50/p95=2/2ms; concurrent live p50/p95=28.4/31.2ms; post-cool-down live burst p50/p95/p99=1.5/1.8/2.1ms; ready p50/p95/p99=1.5/2.1/2.4ms; oracle_quick concurrent p50/p95=41.3/807.7ms |
| Errors | **0 hard errors** on concurrent scored endpoints; controlled 429 on trust_os/scale/viral_readiness/oracle_quick/arb_scan (capacity protection) |
| CPU / memory | host mem ~1.6→1.7 GB used of 16 GB; workers remained up (parent uvicorn `--workers 2`) |
| DB pool | postgres_pool active size=4 (min=4 max=20) before and after |
| Redis | shared RL + inflight backends stable; memory ~1.09→1.14M |
| Worker stability | no worker crash / no process collapse under concurrent load |
| Notes | **Signed multi-worker HA row for DEC-0407.** Does **not** claim 1k–10k concurrent global production capacity without multi-replica staging (`WEB_REPLICAS≥2`) + real PSP credentials. |
| Operator | cloud-agent pre-merge blocker closure |

## Status

- [x] Local Soft Launch buyer-DD probe recorded (honest, non-HA)  
- [x] Local Soft Launch with Postgres+Redis single-worker probe recorded (honest, **still non-HA**)  
- [x] First signed HA run on Postgres+Redis multi-worker recorded above  
- [ ] Results attached to acquirer evidence pack discussion  

Multi-worker Postgres+Redis HA row is filled. Still do **not** claim proven 1k–10k concurrent *global* production capacity without multi-replica staging.
