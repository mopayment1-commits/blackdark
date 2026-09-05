# Rollback Plan — Batch 01 + Batch 02 (IDs 1–100)

**Tag:** `batch01-02-pending-closure-v1` (see git tag on merge commit)  
**Baseline commit:** `9798ab86c6a94287fbee88fdb147f5988ce6cfbe`  
**Status:** PENDING_CLOSURE — rollback documented, not exercised in production

---

## Scope

Reverts official batch01 (1–50) and batch02 (51–100) production spine if live regression detected.

## Pre-requisites

- Confirm regression via `docs/BATCH01_HTTP_PROOF_1_50.json` or `docs/BATCH02_HTTP_PROOF_51_100.json` failure
- Notify owner before production rollback

## Rollback steps

```bash
# 1. Checkout pre-batch spine tag (or parent commit before batch merge)
git fetch origin tag batch01-02-pending-closure-v1
git checkout batch01-02-pending-closure-v1

# 2. Verify critical gate locally
python -m pytest -m "not slow" -q --tb=line 2>&1 | tail -5

# 3. Deploy reverted artifact (Railway / Docker)
docker build -t blackdark-rollback:batch01-02 .
# railway up --image blackdark-rollback:batch01-02  # per ops runbook

# 4. Post-rollback verification
python scripts/verify_batch01_http_all50.py
python scripts/verify_official_batch02_production.py
```

## Files introduced by batch closure (revert targets)

| Path | Purpose |
|------|---------|
| `cap646/batch01_production.py` | Batch01 spine |
| `cap646/batch01_dedicated.py` | Batch01 dedicated handlers |
| `cap646/batch02_production.py` | Batch02 spine |
| `cap646/batch02_dedicated.py` | Batch02 dedicated handlers |
| `cap646/batch03_production.py` | Mis-scoped prep (101–150) |
| `docs/BATCH01_*` / `docs/BATCH02_*` | Evidence artifacts |

## Rollback test record

| Date | Action | Result |
|------|--------|--------|
| 2026-09-01 | Documented only | Not executed — no live production deployment confirmed |

## SRE PRR gap

This plan satisfies rollback *documentation* only. Full Google SRE PRR (monitoring, load test, p95 SLO) remains **unverified** per CLOSURE-REJECT-02 item 24.
