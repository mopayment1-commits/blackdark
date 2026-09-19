# STEP ① Hygiene — FILE 01 ↔ SPECS_13 Ledger Consistency

**Date:** 2026-09-19  
**Scope:** Hygiene only — no feature work, no PASS_LIVE, no FILE 02–13 reopening.

## Before / After

| Field | Before | After |
|-------|--------|-------|
| SPEC_01 `closure_status` | `NOT_CLOSED` | `CLOSED_LOCAL` |
| SPEC_01 `PASS_ENGINEERING` | false | true |
| SPEC_01 `LOCAL_INSTITUTIONAL_CLOSURE` | false | true |
| SPEC_01 `LOCAL_WORK_REMAINING` | 1 | 0 |
| Ledger FILE 01 `closure_status` | `CLOSED_LOCAL` (owner override) | `CLOSED_LOCAL` |
| Ledger FILE 01 `artifact_closure_status` | `NOT_CLOSED` | `CLOSED_LOCAL` |
| Ledger FILE 01 `artifact_aligned_with_owner` | false (implicit) | true |
| SPECS_13 `all_files_closed_local` | true (decorative override) | true (artifact-backed) |
| SPECS_13 CLOSED_LOCAL count | 13/13 (FILE 01 mismatch) | 13/13 (aligned) |
| Tests run + result | phase8 ERROR (empty SSOT) + phase7 auth gap | **all green** (see below) |
| Real LOCAL gaps remaining | 0 (false TESTS gap from coupling) | **none** |
| PASS_LIVE false on all 13? | yes | **yes** |

## Root causes (honest)

1. **`BLACKDARK_CAPABILITY_CURRENT_STATE.json` truncated to 0 bytes** — caused `generate_phase8_launch_coherence()` JSON decode errors, cascading into phase8 E2E fixture failures that were coupled into SPEC_01 closure history.
2. **Stale SPEC_01 generator** — `generate_spec01_adaptive_decision_closure.py` called `build_final_status()` without passing `tests=tests`, so regenerated status could ignore the live test run.
3. **Phase7 test coupling** — `test_capability_49_history_only_rejects_behavioral_learning` called private history without authenticated `user_key`/`subject_id`; entitlement gate (FILE 03) correctly denied anonymous access, but test expected `personal_decision_history` body shape.

## Fixes applied (hygiene only)

| Change | File |
|--------|------|
| Restored SSOT from git (11MB) | `BLACKDARK_CAPABILITY_CURRENT_STATE.json` |
| Pass `tests=tests` into `build_final_status` | `governance/launch57/generate_spec01_adaptive_decision_closure.py` |
| Add auth params to history guard test | `tests/launch57/test_phase7_adaptive_batch_a.py` |
| Ledger: prefer artifact truth; override only when artifact still NOT_CLOSED | `launch57/temporal_evidence_intelligence_support_layer_spec_common.py` |
| Regenerated SPEC_01 artifacts | `governance/launch57/SPEC_01_ADAPTIVE_DECISION_EXPERIENCE/` |
| Refreshed master ledger | `governance/launch57/SPECS_13_LOCAL_CLOSURE_LEDGER.json` |

## Tests run (coupled phase8 ↔ SPEC_01 / support-plane)

```
python3 -m pytest \
  tests/launch57/test_support_plane_full_closure.py \
  tests/launch57/test_support_plane_phase1_isolation.py \
  tests/launch57/test_support_plane_phase3_composition_controls.py \
  tests/launch57/test_support_plane_progressive_disclosure.py \
  tests/launch57/test_support_plane_accessibility_baseline.py \
  tests/launch57/test_support_plane_human_validation_register.py \
  tests/launch57/test_router_selection_contract.py \
  tests/launch57/test_phase2_adaptive_batch_a.py \
  tests/launch57/test_phase2_adaptive_batch_b.py \
  tests/launch57/test_phase7_adaptive_batch_a.py \
  tests/launch57/test_phase7_adaptive_batch_b.py \
  tests/launch57/test_phase8_e2e_acceptance.py \
  tests/launch57/test_phase8_launch_coherence.py \
  -q --tb=no
```

**Result:** exit_code=0, all passed.

## Verdict

- **Honest state:** Path A — no real LOCAL gap for SPEC_01; coupling fixed; artifacts and ledger aligned.
- **STOP:** Await owner for Step ② Pre-Launch Gate.
- **PASS_LIVE:** remains false on all 13 files; `LIVE_VALIDATION_PENDING=true`.
