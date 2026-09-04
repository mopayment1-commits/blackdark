# Batch05 Gate Zero + E2E Checklist — AWAITING_DEPLOY

**Status:** PREPARED ONLY — **NOT EXECUTED**  
**Date:** 2026-09-04  
**Branch:** `cursor/batch05-201-250-e85e` · **PR #366** · **Commit:** `40b654d+`  
**Sequence item:** 5

هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%.

---

## Preconditions (local — done)

| # | Check | Evidence | Status |
|---|-------|----------|--------|
| L1 | Strangler spine 43/43 | `cap646/batch05_strangler_spine.py` | ✅ local |
| L2 | REUSED-LINK facades (#214/#232/#245/#206/#228/#226) | `cap646/batch05_dedicated.py` | ✅ local |
| L3 | Pentagonal probe 47/50 domain_rules (3 REUSED-LINK partial tolerated) | `docs/BATCH05_PENTAGONAL_TEMPLATE_201_250.json` | ✅ local |
| L4 | PA sweep 43/43 stranglers | `docs/BATCH05_PA_CLOSURE_SWEEP_43.json` | ✅ local |
| L5 | REUSED-LINK partial disposition | `docs/BATCH05_REUSED_LINK_PARTIAL_DISPOSITION.json` | ✅ local |
| L6 | Entitlement gateway proof (43 stranglers) | `docs/BATCH05_ENTITLEMENT_GATEWAY_PROOF.json` | ✅ local |
| L7 | Six Heroes final freeze | `docs/BATCH05_HERO_SIX_FINAL_FREEZE.json` | ✅ local |
| L8 | Gateway contract tests | `tests/cap646/test_batch05_gateway_canonical_entitlement_contract.py` | ✅ local |
| L9 | Strangler spine tests | `tests/cap646/test_batch05_strangler_spine.py` | ✅ local |

---

## Gate Zero — Live (NOT EXECUTED)

| # | Check | Command / endpoint | Status |
|---|-------|-------------------|--------|
| G1 | Railway deploy batch05 branch | `cursor/batch05-201-250-e85e` merged + deployed | ⏳ AWAITING_DEPLOY |
| G2 | Health endpoint 200 | `GET /health` on production URL | ⏳ NOT RUN |
| G3 | Sample strangler execute 201 | `POST /api/cap646/201/execute` with auth | ⏳ NOT RUN |
| G4 | Sample strangler execute 242 (Wave 5) | `POST /api/cap646/242/execute` with auth | ⏳ NOT RUN |
| G5 | REUSED-LINK #214 runtime batch01 | `production_spine=batch01` on live GET | ⏳ NOT RUN |
| G6 | REUSED-LINK #232 facade batch05 | `catalog_link.canonical_capability_id=205` on live | ⏳ NOT RUN |
| G7 | Sonar QG on PR #366 | GitHub Actions | ⏳ PENDING CI |

---

## E2E — Live (NOT EXECUTED)

| # | Scenario | Expected | Status |
|---|----------|----------|--------|
| E1 | Pro user → #201 strangler | `success=true`, `production_spine=batch05`, `miswire_remediation=STRANGLER_IMPLEMENTED` | ⏳ NOT RUN |
| E2 | Pro user → #247 public API | `success=true`, surface matches acceptance | ⏳ NOT RUN |
| E3 | Free user → #226 (canonical #69 pro-gated) | `entitlement_denied` or teaser | ⏳ NOT RUN |
| E4 | Pro user → #214 watchlists | `production_spine=batch01`, watchlists payload | ⏳ NOT RUN |
| E5 | Pro user → #232 OI REUSED-LINK | `open_interest_intelligence.feature_ref=205` | ⏳ NOT RUN |
| E6 | Latency sample 201 | <500ms direct_data on live | ⏳ NOT RUN |
| E7 | Latency sample 224 (AI) | <5000ms on live | ⏳ NOT RUN |

---

## Explicit Non-Claims

- **NOT** `LIVE_READY`
- **NOT** `LOCAL_GOVERNANCE_COMPLETE`
- **NOT** Batch05 complete
- **NOT** any `PRODUCTION-ALIGNED` ID while `batch05_independent = 0`
- **NOT** `pa_elevated` without per-ID clearance of all blockers

---

## Execution Authorization

Gate Zero and E2E rows marked ⏳ require:

1. Owner deploy approval (Railway)
2. REUSED-LINK tolerate ceiling review (#214/#245 by 2026-12-31)
3. Per-ID PA closure after live probe + col10 + 12207 Transition sign-off

هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%.
