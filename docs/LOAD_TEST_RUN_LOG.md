# Load Test Run Log

Use this log after running harnesses against a **Postgres + Redis** staging/production-like stack.

## Commands

```bash
# Basic buyer DD probes
python scripts/load_test.py --base http://127.0.0.1:8080 --requests 100

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

## Status

- [ ] First signed HA run recorded above  
- [ ] Results attached to acquirer evidence pack discussion  

Until a row is filled, do **not** claim proven 1k–10k concurrent production capacity.

## Local dry-run note (dev VM)

| Field | Value |
|-------|--------|
| Date (UTC) | 2026-08-08 |
| Environment | local / not prod-like |
| Workers / replicas | 1 |
| Postgres | no (unless env set) |
| Redis | no (unless env set) |
| Script | `scripts/load_test.py` (buyer DD probes) |
| Notes | Scaffold only — **not** an HA capacity claim. Re-run against Postgres+Redis staging and fill the template above. |
| Operator | cloud-agent quality polish |

This dry-run row exists so operators know the log format; it does **not** unlock production concurrency claims.
