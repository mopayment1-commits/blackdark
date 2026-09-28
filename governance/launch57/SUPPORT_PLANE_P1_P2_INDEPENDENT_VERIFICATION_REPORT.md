# Launch-57 Support Plane — Phase 1 + 2 Independent Verification Report

**IV session:** read-only — no product fixes  
**Verified at:** 2026-09-18T03:10:00+00:00  
**Implementation under test:** `1628e7e1`  
**Audited HEAD:** `a3c1170d` (docs-only delta after implementation; isolation + router code at `1628e7e1`)  
**Product baseline:** `f1700f7c` unchanged

## 1) Tests

| Command | Result |
| --- | --- |
| `python3 -m pytest tests/launch57/test_support_plane_phase1_isolation.py tests/launch57/test_router_selection_contract.py -q` | **14 passed, 0 failed** |
| `python3 -m pytest tests/test_trust_pulse.py -q` | **6 passed, 0 failed** |
| `python3 -m pytest tests/launch57/test_phase7_adaptive_batch_b.py -q` | **5 passed, 0 failed** (PARKED guard corroboration) |

## 2) Phase 1 — Isolation probes

| Probe | PASS | Evidence |
| --- | --- | --- |
| a) Default boot loads command-home | ✓ | `templates/dashboard.html:1702` `loadCommandHome(true)` in `boot()`; test `test_dashboard_boot_uses_launch57_command_home` |
| b) Landing pulse + Get Decision canonical | ✓ | `templates/landing.html:1145,1391,1588` → `/api/launch57/command-home`; test `test_landing_default_journey_uses_launch57` |
| c) Legacy paths NOT default data sources | ✓ | No `fetch('/api/intent/router')`, `fetch('/api/trust-pulse')`, or `fetch('/oracle/')` in dashboard/landing templates; delegates in `loadTrustPulse`/`askOracle` |
| d) `ISOLATION_GAP = false` | ✓ | Static + integration (`test_command_home_api_reachable`) + runtime anonymous HTTP 200 on `/api/launch57/command-home` |
| e) Legacy routes exist, not default | ✓ | `dashboard.py:1962,3046` still mount legacy; templates do not call them on boot |
| f) No PARKED / non-LAUNCH57 primary feed | ✓ | `test_phase7_adaptive_batch_b` parked/99 rejection; `test_command_home_eligible_ids_within_launch57` |

**Verdict:** `PHASE1_ISOLATION = PASS_ENGINEERING`

## 3) Phase 2 — §23 contract probes (Command Home)

**Governing (§23.5):** Intent → … → Eligibility → Dependence → Conflict → Budget → Stop → Abstain → Explain.

| Step | PASS | Symbol | Evidence |
| --- | --- | --- | --- |
| intent | ✓ | `build_intent_from_params` | `test_happy_path_selects_eligible_candidates` |
| candidates | ✓ | `gather_candidates` | `test_happy_path_selects_eligible_candidates` |
| eligibility | ✓ | `apply_eligibility` | `test_ineligible_parked_excluded` |
| dependence | ✓ | `apply_dependence_clustering` | `test_happy_path_selects_eligible_candidates` |
| conflict | ✓ | `apply_conflict_coverage` | `test_conflict_handling_abstains` |
| budget | ✓ | `apply_budget` | `test_budget_stop_limits_candidates` |
| stop | ✓ | `apply_stop` | `test_budget_stop_limits_candidates` |
| abstain | ✓ | `apply_abstain` | `test_abstain_on_stale_spine` |
| explain | ✓ | `build_explain` | `test_explain_step_present` |

**Adversarial**

| Probe | PASS | Evidence |
| --- | --- | --- |
| PARKED / ineligible excluded | ✓ | `test_ineligible_parked_excluded` |
| Conflict → abstain/explain | ✓ | `test_conflict_handling_abstains`; `edge_ui_batch2.py:112-152` |
| Budget/stop limits | ✓ | `test_budget_stop_limits_candidates` |
| Stale spine → abstain | ✓ | `test_abstain_on_stale_spine` |
| Command Home wire | ✓ | `edge_ui_batch2.py:104`; `test_command_home_wires_router` |

**Honesty**

- `FULL_CROSS_PATH_§23 = false` — router wired on Command Home composite only (`launch57/edge_ui_batch2.py`)
- G1 remains **partial** vs full-product §23 until other composite paths are wired
- G2, G3 (full), G4, G5 **not closed** in this IV

**Verdict:** `PHASE2_§23_COMMAND_HOME = PASS_ENGINEERING`

## 4) Output summary

| Item | Verdict | Evidence |
| --- | --- | --- |
| Phase 1 isolation | **PASS_ENGINEERING** | 6 isolation tests + template/static/runtime probes; `ISOLATION_GAP=false` |
| Phase 2 §23 on Command Home | **PASS_ENGINEERING** | 8 router tests + wire at `edge_ui_batch2.py:104` |
| `SUPPORT_PLANE_P1_P2_INDEPENDENT_VERDICT` | **PASS_ENGINEERING** | Both Phase 1 and Phase 2 PASS |

**Blockers:** none

## Flags

- `PASS_LIVE_NOT_CLAIMED = true`
- `G2_G3_G4_G5_STILL_OPEN = true`
- `NO_MASS_REVOKE = true`

STOP.
