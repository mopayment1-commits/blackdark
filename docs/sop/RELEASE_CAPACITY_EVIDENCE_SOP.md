# SOP #30 — Capacity / Load Evidence (Every Release)

**Type:** Engineering practice — NOT a user-facing feature.  
**Goal:** Prove system capacity with numbers and repeatable tests — never extrapolate user counts without evidence.

## When to run

- Before every production/staging release
- After infrastructure changes (DB pool, Redis, worker count, rate limits)
- When claiming HA or scale readiness

## Preconditions

| Requirement | Notes |
|-------------|-------|
| Representative workload | Same endpoints, concurrency, and payload sizes as production profile |
| Honest environment | Document Postgres, Redis, worker/replica counts |
| No extrapolation | Do NOT claim "supports N users" without measured evidence |

## Procedure

### 1. Record environment profile

Capture in the evidence artifact:

- `WEB_CONCURRENCY`, `WEB_REPLICAS` (or equivalent)
- `DATABASE_URL` present (yes/no — never log credentials)
- `REDIS_URL` present (yes/no)
- CPU/memory limits if containerized
- Git commit SHA

### 2. Run repeatable workload

```bash
# Local/staging — concurrent harness (controlled 429/503 = OK unless --strict-2xx)
python scripts/load_test_concurrent.py --base https://YOUR-STAGING --workers 40 --requests 200

# Release evidence gate (records SLO pass/fail + trend)
python scripts/release_capacity_evidence.py --base https://YOUR-STAGING

# Optional: k6 data-engine smoke
MODE=smoke k6 run scripts/k6_wave_01_data.js
```

### 3. Measure and record

Required metrics per endpoint/workload:

| Metric | Required |
|--------|----------|
| p50 / p95 / p99 latency (ms) | Yes |
| Error rate | Yes |
| Controlled degradation (429/503) | Yes — scored separately from hard failures |
| Saturation point | Yes — workers/requests where SLO breaks |
| Recovery time | Yes — after burst, time to return to SLO |
| Resource limits | Yes — pool size, in-flight caps, memory |

### 4. Pass/fail SLOs

Default release SLOs (override via env if documented):

| SLO | Threshold |
|-----|-----------|
| Health/readiness p95 | ≤ 2000 ms |
| Core API p95 | ≤ 3000 ms |
| Hard error rate | ≤ 5% (excludes controlled 429/503) |
| Capacity ok rate | ≥ 95% (2xx + controlled degradation) |

### 5. Append regression trend

`scripts/release_capacity_evidence.py` appends to:

- `data/release_engineering/capacity_trend.jsonl`

For signed HA claims, also append a row to `docs/LOAD_TEST_RUN_LOG.md` with Postgres+Redis multi-worker evidence.

## Acceptance criteria

- [ ] Repeatable workload profile documented
- [ ] No user-count extrapolation without measured evidence
- [ ] Pass/fail SLOs recorded per endpoint
- [ ] Resource limits captured
- [ ] Regression trend retained (JSONL append)
- [ ] Operator + timestamp on every run

## Fail-closed rule

If capacity evidence is missing or SLOs fail → **do not claim scale readiness**. `scale_readiness_report()` remains honest (`proven_signed_load_test: false`).
