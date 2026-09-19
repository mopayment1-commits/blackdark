# Phase 7 / Batch B — Independent Verification Report

**Verification type:** independent engineering (read-only)  
**Implementation SHA:** `840a7b23`  
**Builder evidence SHA:** `6d442c58`  
**Product under test:** `840a7b23` (no later `launch57/` product changes)

## 1. Repository state

| Check | Result |
| --- | --- |
| Builder evidence implementation SHA | `840a7b23` — uniquely identified |
| Audited HEAD (pre-IV) | `6d442c58` (governance evidence only after implementation) |
| Later product changes invalidating IV | **None** (`git diff 840a7b23..6d442c58 -- launch57/ cap646/ tests/launch57/ api/routers/launch57_edge_ui.py` empty) |
| Canonical dispatch | `GET /api/launch57/command-home` → `launch57.edge_ui_batch2:six_heroes_command_home` |
| Entry gate | `PHASE7_BATCH_A_INDEPENDENT_VERDICT = PASS_ENGINEERING @ 292d876c` |

## 2. Capability verdict

| # | Verdict | Key control |
| --- | --- | --- |
| 1 | PASS_ENGINEERING | Readiness-filtered eligible IDs from SSOT; `include_parked` / metadata override → `UNSUPPORTED_READINESS_SCOPE_REJECTED`; Six Heroes primary; no duplicate capability directory |

## 3. Bypass controls

| # | Bypass simulation | Result |
| --- | --- | --- |
| 1 | `apply_command_home_guard` no-op with `include_parked` | Parked ID `99` appears in eligible list when bypassed; real guard blocks with empty eligible list |

## 4. Consumer-path probes

| Probe | Result |
| --- | --- |
| Grounded home | `COMMAND_HOME_GROUNDED`, `success=true`, heroes `derived_from=canonical_decision_truth` |
| `include_parked=true` | `UNSUPPORTED_READINESS_SCOPE_REJECTED`, eligible list empty, `scope_rejected=true` |
| `eligible_launch57_ids` injection | `UNSUPPORTED_READINESS_SCOPE_REJECTED`, injected ID `99` not surfaced |

## 5. Dependency-aware regression

Batch B appended command-home helpers to shared support; directly affected consumers regression-tested:

```text
python3 -m pytest tests/launch57/test_phase7_adaptive_batch_b.py tests/launch57/test_edge_ui_batch2.py tests/test_decision_truth_p5_product_experience.py tests/launch57/test_phase7_adaptive_batch_a.py tests/launch57/test_edge_ui_batch1.py tests/launch57/test_edge_ui_institutional_wire.py -q
# 53 passed, 0 failed
```

Phase 7 Batch A independent verdict remains valid: Batch A regression suite passes after Batch B shared-code append.

Unaffected prior capabilities not re-verified per scope.

## 6. Residual gaps (non-blocking)

- `launch57/trust_adaptive_common.py` contains duplicate identical derivatives helper definitions from Phase 5 Batch A; Python binds the later copy.
- Legacy `cap646.batch01_dedicated` / `batch10_dedicated` handlers exist but Launch-57 API routes command home via `launch57.edge_ui_batch2`; no parallel truth path observed on consumer path.
- #1 not wired through `cap646.institutional_official_production` — API route is canonical.

## 7. Final verdicts

```text
P7:#1 = PASS_ENGINEERING
PHASE7_BATCH_B_INDEPENDENT_VERDICT = PASS_ENGINEERING
PASS_LIVE_NOT_CLAIMED = true
```

Audit conclusion only. No SSOT/register promotion.
