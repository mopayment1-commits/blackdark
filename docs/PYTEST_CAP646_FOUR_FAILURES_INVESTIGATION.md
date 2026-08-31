# Investigation: 4 cap646 pytest failures (institutional gate)

**Branch audited:** `cursor/reused-link-batch05-e85e` @ `17c43e0`  
**Command:** `pytest -m "not slow" -q --tb=line --maxfail=10`  
**Investigated:** 2026-08-30

## 1) Raw pytest output (current branch, final run)

**Result:** `1978 passed, 2 skipped, 4 deselected, 0 failed` — `EXIT=0`

Full raw `-q` output saved at: `docs/artifacts/pytest_batch05_final_raw.log` (repo-relative copy below).

The `-q` flag suppresses the passed-count line; count verified with:
`pytest -m "not slow" --tb=no` → **1978 passed, 2 skipped, 4 deselected**.

Compared to last confirmed batch-04 closure (**1776 passed**): +202 tests (batch 05 hero + defi yield suites).

## 2) The four reported failures — per-test analysis

| # | Test | Green at 1776 baseline? | Last git touch | Specific failure reason |
|---|------|-------------------------|----------------|-------------------------|
| 1 | `tests/cap646/test_institutional_gate.py::test_external_registry_integrity` | **Yes** on batch-04 @ `4bf90f2` (with `85dca36`) | `tests/…/test_institutional_gate.py` → `6a886d5` (2026-08-30 17:11 UTC); logic → `cap978/institutional_gate.py` → `85dca36` (2026-08-30 17:11 UTC) | `missing=[644]` when `85dca36` registry restore absent; live registry expected 33 slots incl. ID644 |
| 2 | `tests/cap646/test_institutional_gate.py::test_committed_artifacts_match_baseline` | **Yes** on batch-04 @ `4bf90f2` | same as above | Committed `EVIDENCE_ROOM_SNAPSHOT.json` / `EXTERNAL_VENDOR_REGISTRY.json` drift vs live `external_registry_report()` when 644 slot missing |
| 3 | `tests/cap646/test_institutional_gate.py::test_commercial_launch_checklist` | **Yes** on batch-04 @ `4bf90f2` | same as above | `total_external_items` mismatch (32 vs 33) when registry incomplete |
| 4 | `tests/cap646/test_soft_launch_closure.py::test_soft_launch_closure_code_complete` | **Yes** on batch-04 @ `4bf90f2` (when runtime data present) | `tests/…/test_soft_launch_closure.py` → `314d8075` (2026-08-27); logic → `cap978/soft_launch_closure.py` → `bdfb6b15` (2026-08-27) | `verdict='NOT READY'` when `data/signal_registry.jsonl` et al. missing **or** external registry count wrong (expected 31 caps) |

### Reproduction matrix

| Environment | 4 cap646 tests | Full `pytest -m "not slow"` |
|---|---|---|
| **batch-05 branch** (`17c43e0`, `/workspace`) | **5/5 PASS** (3 runs) | **1978 passed, 0 failed** |
| **batch-04** (`4bf90f2`, `PYTHONPATH` set) | **5/5 PASS** | **1775 passed, 1 failed** (`test_batch_test_mapping` only) |
| **origin/main** (`e4bcfd5`, `PYTHONPATH` set) | **1/5 PASS, 4 FAIL** | Not in 1776 scope |
| **batch-04** without `PYTHONPATH` / stale data | **4 FAIL** (transient) | 4 cap646 + mapping fail |

## 3) Scope: batch 05 content vs institutional path

**No substantive overlap with capabilities 401–500.**

| Area | Files touched by batch 05 / REUSED-LINK | cap646 gate files |
|---|---|---|
| Batch 05 impl | `bd_platform/defi_yield_intelligence_layer.py`, batch 05 tests/manifest | — |
| REUSED-LINK retro | `scripts/retrospective_deep_audit.py`, evidence JSONL, checklist xlsx | — |
| cap646 institutional | — | `cap978/institutional_gate.py`, `cap978/external_registry.py`, committed snapshots |

The four failures exercise **CAP-978 external vendor registry invariants** and **soft-launch data-store presence** — not defi/yield capability logic.

**Verdict:** Batch 05 content (401–500) and REUSED-LINK reclassification are **separable** from institutional gate health. The intermediate 4-failure report was **not a regression** from those changes; it matched **pre-existing main-branch gap** (`e4bcfd5` lacks `85dca36`) or **transient environment state** (missing runtime `data/*.jsonl`, PYTHONPATH cross-contamination).

## 4) Root-cause commit (pre-existing on main, fixed on feature branches)

**Fix commit (on batch-03/04/05 branches, NOT on `origin/main`):**

```
85dca36f9f24f2af25636e23feb0ebe97904e5a3
2026-08-30 17:11:52 +0000
fix: production-only CAP-644 gate + restore external vendor registry
```

**Main branch without fix:**

```
e4bcfd5 — fix(ci): institutional hardening for CAP978, security, and Sonar gates (#263)
```

## 5) Action

- **No fix required** on `cursor/reused-link-batch05-e85e` — institutional gate green (0 failures).
- **No regression** from REUSED-LINK or batch 05 capability code.
- Batch 06 remains blocked per user gate until this report is accepted.
