# Batch04 Gate Zero + E2E Checklist — AWAITING_DEPLOY

**Status:** PREPARED ONLY — **NOT EXECUTED**  
**Date:** 2026-09-03  
**Branch:** `cursor/batch-04-151-200-e85e` · PR #363

هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 · لا جاهزية حية 100%.

---

## Preconditions (local — done)

| # | Check | Evidence | Status |
|---|-------|----------|--------|
| L1 | batch04 spine wired 151–200 | `cap646/runtime.py` | ✅ local |
| L2 | 49 dedicated handlers + #175 batch01 | `cap646/batch04_dedicated.py` | ✅ local |
| L3 | Pentagonal probe 50/50 domain_rules | `docs/BATCH04_RULE_COUNT_ASSERT_PROOF.txt` | ✅ local |
| L4 | Triple-match guard | `tests/cap646/test_batch04_pentagonal_triple_match.py` | ✅ local |
| L5 | Gateway entitlement proof | `docs/BATCH04_ENTITLEMENT_GATEWAY_PROOF.json` | ✅ local |
| L6 | PA registry (0 PA) | `docs/BATCH04_PA_CLOSURE_REGISTRY.json` | ✅ local |
| L7 | Blocker escalation documented | `docs/BATCH04_BLOCKER_ESCALATION_OWNER.md` | ✅ local |
| L8 | pytest batch04 + batch03 non-regression | CI / local runs | ✅ local |

---

## Gate Zero — Live (NOT EXECUTED)

| # | Check | Command / endpoint | Status |
|---|-------|-------------------|--------|
| G1 | Railway deploy batch04 branch | `cursor/batch-04-151-200-e85e` merged + deployed | ⏳ AWAITING_DEPLOY |
| G2 | Health endpoint 200 | `GET /health` on production URL | ⏳ NOT RUN |
| G3 | Sample cap646 execute 151 | `POST /api/cap646/151/execute` with auth | ⏳ NOT RUN |
| G4 | Sample cap646 execute 159 (elite) | entitlement + batch04 spine on live | ⏳ NOT RUN |
| G5 | #175 routes batch01 on live | `production_spine=batch01` | ⏳ NOT RUN |
| G6 | Sonar QG on PR #363 | GitHub Actions | ⏳ PENDING CI |

---

## E2E — Live (NOT EXECUTED)

| # | Scenario | Expected | Status |
|---|----------|----------|--------|
| E1 | Free user → #159 | `entitlement_denied` (canonical #103 elite) | ⏳ NOT RUN |
| E2 | Elite user → #159 | `success=true`, `production_spine=batch04`, `catalog_link.duplicate_of=103` | ⏳ NOT RUN |
| E3 | Pro user → #175 | `production_spine=batch01`, `surface=sentiment_ai` | ⏳ NOT RUN |
| E4 | Free user → #183 | `success=true`, whale_transaction payload | ⏳ NOT RUN |
| E5 | Latency sample 151 | <500ms direct_data on live | ⏳ NOT RUN |
| E6 | Latency sample 154 (AI) | <5000ms on live | ⏳ NOT RUN |

---

## Explicit Non-Claims

- **NOT** `LIVE_READY`
- **NOT** `LOCAL_GOVERNANCE_COMPLETE`
- **NOT** Batch05 authorized
- **NOT** any `PRODUCTION-ALIGNED` ID while `batch04_independent = 0`

---

## Execution Authorization

Gate Zero and E2E rows marked ⏳ require:

1. Owner deploy approval (Railway)
2. Resolution or ADR for BLOCKER-159-103 and BLOCKER-183-130
3. At least one documented PA closure before claiming governance progress
