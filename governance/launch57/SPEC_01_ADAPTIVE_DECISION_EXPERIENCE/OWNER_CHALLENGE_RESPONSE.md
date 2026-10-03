# SPEC_01 Owner Challenge Response

**SHA under test:** `fa6edea1` / `cd07e554`  
**Challenge date:** 2026-09-18  
**Mode:** honesty audit — no new features

---

## 1) `full_cross_path_23`

### Spec quote (authority)

> §23.5 Router Selection Sufficiency Contract — Selection logic, **where applicable**  
> §3 — Every **material decision path** must pass applicable controls (scope, freshness, evidence class, …).  
> Router is a **support structure**, not a capability.

§23 applies to **capability composition / candidate selection**, not to raw data-spine reads or hard fail-closed gates that occur **before** any composition.

### Paths that MUST run §23 (SPEC_01 material composition scope)

| # | Surface / entry | Caller → control | Router mechanism |
|---|-----------------|------------------|------------------|
| 1 | `six_heroes_command_home` (happy + abstain) | `edge_ui_batch2.six_heroes_command_home` → `run_router_selection_contract` | Direct call before hero build |
| 2 | `single_sentence_oracle` | `trust_batch1.single_sentence_oracle` → `attach_adaptive_disclosure` → `finalize_launch57_consumer_response` → `attach_router_if_material` → `run_router_selection_contract` | Envelope |
| 3 | `decision_certificate_institutional_dd_export` | `trust_batch1.decision_certificate_export` → same envelope chain | Envelope |
| 4 | `public_accuracy_ledger` | `trust_batch1.public_accuracy_ledger` → `finalize_b5_ledger_surface` → `attach_adaptive_disclosure` → envelope | Envelope |
| 5 | `net_edge_truth_score` | `trust_batch1.net_edge_truth_score` → envelope | Envelope |
| 7–12, 37 | decision_batch* surfaces | `decision_batch*.py` handlers → `attach_adaptive_disclosure` → envelope | Envelope |
| 13–20, 53–57 | smart_money_batch* | same pattern | Envelope |
| 25–33 | derivatives_batch* | same pattern | Envelope |
| 34–36, 51 | explanation_ai_batch1 | same pattern | Envelope |
| 38, 43, 49, 50, 52 | edge_ui_batch1 | same pattern | Envelope |
| 44–48 | trust_batch2 | same pattern | Envelope |

**Proof pattern (runtime, not JSON):** `attach_adaptive_disclosure(body, level1)` on material `launch_item_id` returns `router_selection_contract` with `pipeline_steps` (see `test_trust_batch_consumer_gets_l2_l5_and_router`).

### Explicit OUT_OF_SCOPE (not LOCAL gaps)

| Class | Launch IDs | Spec basis | Router |
|-------|------------|------------|--------|
| Data spine (no composition) | 21–24, 39–42 | §23 *where applicable* — raw metric/connector reads, not multi-cap composition | **Skipped** by `material_composition_applies()` in `support_plane_envelope.py` |
| Pre-composition fail-closed | #1 stale gate; #2/#3 timing error returns | §23.4 abstain semantics — blocked before candidate set exists | **No router** — `stale_gate_body` / `apply_b4_trust_envelope` only |

### Previously `FULL_CROSS_PATH_§23 = false`

| When | Evidence | Scope |
|------|----------|-------|
| Phase 3 (`7e835261`) | `SUPPORT_PLANE_PHASE3_REPORT.md` §F: "G1 remains **Command-Home-scoped** — FULL_CROSS_PATH_§23 = false" | Router only on Command Home |
| P1/P2 IV | `SUPPORT_PLANE_P1_P2_INDEPENDENT_VERIFICATION.json`: `FULL_CROSS_PATH_§23: false` | Same |

### What code made it true (NOT `fa6edea1`)

| Commit | Change |
|--------|--------|
| **`313c8ccf`** | **Created** `launch57/support_plane_envelope.py`; wired `attach_adaptive_disclosure` default → `finalize_launch57_consumer_response` → `attach_router_if_material` → `run_router_selection_contract` on all material composition consumers |
| `fa6edea1` | **Documentation only** — flipped `SUPPORT_PLANE_P3_STATUS.full_cross_path_23` to `true`; **zero router code changes** |

### Honest verdict

| Field | Value | Meaning |
|-------|-------|---------|
| `full_cross_path_23` | **`true`** | All **material composition consumer paths** (attach_adaptive default + Command Home happy/abstain) run §23 |
| `full_cross_path_23_literal_all_surfaces` | **`false`** | Stale gate + hard error returns + data spine do not run router (by design) |
| `fa6edea1_introduced_router` | **`false`** | Doc alignment only; engineering from `313c8ccf` |

---

## 2) Three historically weak YES rows — runtime proof

### A) REQ-S01-012 — Progressive disclosure L2–L5

- **Caller → control:** `trust_batch1.net_edge_truth_score` → `attach_adaptive_disclosure` → `finalize_launch57_consumer_response` → `build_level2_why_disclosure` … `build_level5_expert_disclosure` (`support_plane_envelope.py`)
- **Test:** `tests/launch57/test_support_plane_full_closure.py::test_trust_batch_consumer_gets_l2_l5_and_router`
- **Fails if removed:** monkeypatch `build_level2_why_disclosure` → `{}` ⇒ `level_2` missing ⇒ **exit 1**

### B) REQ-S01-014 — Accessibility §31

- **Caller → control:** `finalize_launch57_consumer_response` → `attach_launch57_accessibility` (`accessibility_common.build_launch57_accessibility_envelope`)
- **Test:** `tests/launch57/test_support_plane_accessibility_baseline.py::test_command_home_api_includes_launch57_accessibility` (HTTP `/api/launch57/command-home`)
- **Fails if removed:** monkeypatch `attach_launch57_accessibility` to identity ⇒ `launch57_accessibility` missing ⇒ **exit 1**

### C) REQ-S01-015 — Human validation proxy §31.1

- **Caller → control:** `templates/dashboard.html` `boot()` → `loadCommandHome` → `/api/launch57/command-home` (task_success proxy); dimensions backed by `SUPPORT_PLANE_HUMAN_VALIDATION_EVIDENCE.json` **and** pytest harness
- **Test:** `tests/launch57/test_support_plane_full_closure.py::test_human_validation_engineering_harness` + `test_support_plane_phase1_isolation.py::test_dashboard_boot_uses_launch57_command_home`
- **Fails if removed:** delete evidence file or remove `loadCommandHome` from dashboard boot ⇒ tests fail (not JSON-only PASS)

---

## 3) `LOCAL_WORK_REMAINING` after honesty fix

| Item | Counted as LOCAL gap? | Reason |
|------|----------------------|--------|
| Data spine without router | **No** | OUT_OF_SCOPE — §23 where applicable |
| Command Home stale gate without router | **No** | PRE_COMPOSITION_FAIL_CLOSED — §23.4 abstain equivalent |
| trust_batch1 error-only `apply_b4_trust_envelope` | **No** | PRE_COMPOSITION_FAIL_CLOSED |
| `fa6edea1` doc-only full_cross flip | **No** | Documentation correction applied here; engineering already in `313c8ccf` |

**`LOCAL_WORK_REMAINING = 0`** — holds under scoped §23 definition above.

**STOP.** No FILE 02.
