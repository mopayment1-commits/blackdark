# Launch-57 Support Plane — Phase 1 + 2 Report

**Prerequisite:** Phase 0 @ `da116cf8`  
**Generated:** 2026-09-18  
**Status:** `SUPPORT_PLANE_P1_P2_STATUS = PENDING_VERIFICATION`

## A) HEAD before/after

| | SHA |
| --- | --- |
| Before (Phase 0) | `da116cf8` |
| After (Phase 1+2) | _(see commit)_ |

Product baseline `f1700f7c` handler cores unchanged; support-plane + UI journey isolation added.

## B) Files changed

### Phase 1 — Journey isolation (UI)

| File | Change |
| --- | --- |
| `templates/dashboard.html` | Default boot → `loadCommandHome()` → `/api/launch57/command-home`; legacy `/api/intent/router`, `/api/trust-pulse`, `/oracle/{sym}` removed from default fetch path |
| `templates/landing.html` | Landing pulse + `consultOracle` → `/api/launch57/command-home` |
| `anonymous_route_foundation.py` | Add `/api/launch57/` to anonymous public API allowlist (v1 default journey reachable) |

### Phase 2 — §23 Router Selection Sufficiency Contract

| File | Change |
| --- | --- |
| `launch57/router_selection_contract.py` | **NEW** — §23.5 pipeline owner (`PENDING_VERIFICATION`) |
| `launch57/edge_ui_batch2.py` | Thin wire: `six_heroes_command_home` invokes router before guard; abstain/explain on sufficiency failure |

### Tests

| File | Coverage |
| --- | --- |
| `tests/launch57/test_support_plane_phase1_isolation.py` | Default journey isolation |
| `tests/launch57/test_router_selection_contract.py` | §23 pipeline steps |
| `tests/test_trust_pulse.py` | Updated wiring assertion for Launch-57 command home |

## C) Phase 1 — Default journey

| Field | Before | After |
| --- | --- | --- |
| `DASHBOARD_REACHABLE_PARALLEL_PATH` | true | true (shell still at `/dashboard`) |
| `CANONICAL_LAUNCH57_ENTRY` | `/api/launch57/command-home` | `/api/launch57/command-home` |
| `ISOLATION_GAP` | **true** | **false** |

### Before (default boot)

- `loadIntentRouter()` → `GET /api/intent/router`
- `loadTrustPulse()` → `GET /api/trust-pulse`
- `askOracle()` → `GET /oracle/{sym}`
- Landing: trust-pulse + oracle parallel paths

### After (default boot)

- `loadCommandHome()` → `GET /api/launch57/command-home`
- `loadTrustPulse` / `askOracle` / `loadIntentRouter` delegate to command home
- `startTrustPulseStream` polls command home (no trust-pulse SSE on default path)
- Landing pulse + Get Decision use command home

Legacy servers/routes remain in repo; not default launch journey.

## D) Phase 2 — §23 step → symbol → test map

**Governing quote (Adaptive Spec §23.5):**  
> Selection logic: Intent → Mandatory controls → Eligibility → Dependence clustering → Conflict coverage → Marginal value → Budget → Stop → Abstain → Explain. No Router behavior may select or infer a PARKED capability.

| §23.5 step | Code symbol | Test |
| --- | --- | --- |
| Intent | `build_intent_from_params` | `test_happy_path_selects_eligible_candidates` |
| Candidates | `gather_candidates` | `test_happy_path_selects_eligible_candidates` |
| Eligibility | `apply_eligibility` | `test_ineligible_parked_excluded` |
| Dependence | `apply_dependence_clustering` | `test_happy_path_selects_eligible_candidates` |
| Conflict | `apply_conflict_coverage` | `test_conflict_handling_abstains` |
| Budget | `apply_budget` | `test_budget_stop_limits_candidates` |
| Stop | `apply_stop` | `test_budget_stop_limits_candidates` |
| Abstain | `apply_abstain` | `test_abstain_on_stale_spine` |
| Explain | `build_explain` | `test_explain_step_present` |
| Composite wire | `run_router_selection_contract` in `six_heroes_command_home` | `test_command_home_wires_router` |

## E) Status

`SUPPORT_PLANE_P1_P2_STATUS = PENDING_VERIFICATION`

- No `SUPPORT_PLANE_PASS` claimed
- No `PASS_LIVE` claimed
- No mass `PASS_ENGINEERING` revocation
- Router module `builder_status = PENDING_VERIFICATION` only

## F) Remaining open gaps

| Gap | Status |
| --- | --- |
| G1 §23 Router contract | **Partially addressed** — `router_selection_contract.py` on Command Home composite path; full cross-composition IV pending |
| G2 §28 L2–L5 | **OPEN** (later phase) |
| G3 §32 full instrumentation | **OPEN** — minimal budget defaults only in router |
| G4 Accessibility | **OPEN** (later phase) |
| G5 Human validation | **OPEN** (later phase) |

## G) Composite paths needing re-IV

1. **Command Home composite** (`launch57.edge_ui_batch2:six_heroes_command_home`) — router + guard + L1 disclosure chain
2. **Anonymous allowlist expansion** (`/api/launch57/*`) — security/route foundation re-IV
3. **Dashboard + landing default journey** — UI isolation evidence vs Phase 8 engineering E2E

STOP. Await IV command for Phase 1–2.
