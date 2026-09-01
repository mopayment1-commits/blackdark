# CLOSURE-REJECT-04 Report (Items 1–34)

**Date:** 2026-09-01  
**Branch:** `cursor/closure-reject-04-e85e`  
**Status:** `PENDING_CLOSURE` — institutional closure **prohibited**

| Artifact | [Status on Branch] | [Status on main] |
|----------|-------------------|------------------|
| `closure_status` | PENDING_CLOSURE | PENDING_CLOSURE (invalid PR #349 merge msg) |
| Progress | **104/826** | **114/826** (incorrect — pre-REJECT-04) |
| Batch03 leak (#103) | **Removed + corrected** | **Present** in entitlement proofs |
| gate-full PR job | Added `gate-full` in `ci.yml` | Not present |
| Sonar Grade A | **Not achieved** | Grade E (5.0/5.0) |

---

## Corrections applied in REJECT-04

1. **Type-3:** lizard `-C 8` executed — `clone_count: 0` in `docs/CLOSURE_REJECT_04_AUDIT.json`
2. **ADR-001:** Rule of Three mis-citation corrected; `Extract Function` in `_batch_route.py`
3. **jscpd:** executed via `npx jscpd@4.0.5` — results in `CLOSURE_REJECT_04_AUDIT.json`
4. **R0801:** post-refactor pylint on handlers = **10.00/10** (no duplicate-code hits)
5. **SSOT:** `docs/SSOT_MATRIX_1_100.json` created
6. **Split-brain 56:** full rows + 20-sample live contracts in `CLOSURE_REJECT_04_AUDIT.json`
7. **#103 removed** from entitlement scripts + proofs; batch02 denial via **#85 free→teaser**
8. **Entitlement counts:** 10 test cases each batch; batch01=9 unique IDs, batch02=9 unique IDs
9. **Progress 114→104:** removed extension/hero IDs without batch01/02 proof
10. **#214/#245:** excluded from numerator (Hero Batch OPEN_RISK)
11. **Pre-batch 338/500/507/534:** retained with documented pre-batch status
12. **Coverage formula:** weighted by statement count (not arithmetic mean)
13. **#57 mislabel attribution:** prior CLOSURE-REJECT-01 agent report (pre-batch02), not R2
14. **HMAC guard:** `cap646/closure_guard.py` + `scripts/prove_hmac_closure_guard_failure.py`
15. **CI:** `cap-dedup-gate` + `gate-full` jobs on PR
16. **checklist:** OVERLAP/LINK columns added to `capabilities_checklist.xlsx`

## Remaining blockers (items 15–20, 27, 33)

- Sonar `new_reliability_rating` / `new_security_rating` still **5.0** (no SONAR_TOKEN in agent env)
- Spine coverage **50.7%** weighted (target ≥80%)
- Owner written HMAC approval not issued
- `main` corrective commit for PR #349 revocation pending merge

## Link-eligible decision (item 32)

**DEFERRED_DOCUMENTED** — live execution of #106/#107/#110/#125 requires batch03 scope (prohibited). Canonical targets #63/#64/#69/#85 in 1–100 remain PRODUCTION-ALIGNED.
