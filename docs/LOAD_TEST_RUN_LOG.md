# Load Test Run Log

Use this log after running harnesses against a **Postgres + Redis** staging/production-like stack.

## Commands

```bash
# Buyer DD probes (app core; sidecar optional)
python scripts/load_test.py --base http://127.0.0.1:8080 --requests 100

# Concurrent diligence harness (health, trust-os, viral, oracle quick, arb, compliance)
python scripts/load_test_concurrent.py --base http://127.0.0.1:8080 --workers 40 --requests 200

# Scale + viral readiness JSON (codepath honesty — not a signed capacity proof)
curl -s http://127.0.0.1:8080/api/scale/readiness | jq .
curl -s http://127.0.0.1:8080/api/viral/readiness | jq .

# 60-second grasp machine probe
python scripts/acceptance_60s.py --base http://127.0.0.1:8080

# Heavier simulation (if available)
python scripts/load_test_1m_simulation.py
```

## Required environment for an honest HA claim

- `ENV=production` or Soft Launch documented explicitly  
- `DATABASE_URL=postgresql://…`  
- `REDIS_URL=redis://…`  
- At least 2 web workers / replicas if claiming multi-worker safety  

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
- [ ] First signed HA run on Postgres+Redis multi-worker recorded above  
- [ ] Results attached to acquirer evidence pack discussion  

Until a Postgres+Redis multi-worker row is filled, do **not** claim proven 1k–10k concurrent production capacity.
