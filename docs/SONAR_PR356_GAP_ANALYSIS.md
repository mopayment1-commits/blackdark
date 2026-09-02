# Sonar PR #356 — Gap Analysis (spine 80% vs New Code 26.09%)

**Generated:** 2026-09-02 UTC  
**PR:** #356 (`cursor/closure-mandate-verify-e85e`)  
**Sonar baseline:** `sonar.projectVersion = 2026.08.12` @ main `9798ab86`

## Executive summary

| Metric | Definition | Value | Source |
|---|---|---:|---|
| **Spine coverage** | Weighted statement coverage on **8 hand-picked modules** via `SPINE_PYTEST` | **80.00%** (1940/2425) | `docs/SPINE_COVERAGE_SNAPSHOT.json` |
| **Sonar New Code coverage** | Line coverage on **253 new/changed executable lines** since baseline | **26.09%** (66/253) | SonarCloud API PR #356 |
| **Sonar overall coverage** | Entire repo in CI `coverage.xml` | **~25.6%** | CI run `33578562159` |

The gap is **not a math error** — it is a **scope + suite + denominator** mismatch.

---

## 1) Spine-suite scope (local 80%)

### Files (8 modules, 2425 statements)

| Module | Stmts | Miss | Coverage |
|---|---:|---:|---:|
| `cap646/runtime.py` | 124 | 16 | 87.1% |
| `cap646/batch_spine.py` | 12 | 0 | 100% |
| `cap646/batch01_production.py` | 72 | 5 | 93.1% |
| `cap646/batch01_dedicated.py` | 458 | 40 | 91.3% |
| `cap646/batch02_production.py` | 36 | 6 | 83.3% |
| `cap646/batch02_dedicated.py` | 255 | 0 | 100% |
| `cap646/dedicated_common.py` | 49 | 0 | 100% |
| `database.py` | 1419 | 418 | 70.5% |
| **Σ** | **2425** | **485** | **80.00%** |

### Pytest files (`SPINE_PYTEST` in `scripts/run_closure_mandate_last.py`)

- `tests/cap646/test_batch01_dedicated.py`
- `tests/cap646/test_batch01_production.py`
- `tests/cap646/test_batch02_dedicated.py`
- `tests/cap646/test_dedicated_common.py`
- `tests/cap646/test_batch_spine.py`
- `tests/cap646/test_cap69_dual_path.py`
- `tests/cap646/test_runtime_spine_coverage.py`
- `tests/cap646/test_closure_reject_04.py`
- `tests/test_spine_database.py`
- `tests/test_spine_database_auth.py`
- `tests/test_bigquery_export_mock.py`

**Not in Sonar CI workflow before this fix** — spine tests were excluded from `coverage.xml` generation.

---

## 2) Sonar New Code scope (PR #356)

**Definition:** executable lines added/changed since engineering baseline `2026.08.12` (Previous version).

| Aggregate | Value |
|---|---:|
| `new_lines_to_cover` | 253 |
| `new_uncovered_lines` | 187 |
| `new_coverage` | 26.09% |

### All New Code files with measurable lines (Sonar API)

| File | New lines | Uncovered | New coverage | In spine-suite? |
|---|---:|---:|---:|---|
| `cap646/dedicated_common.py` | 70 | 47 | 32.9% | **Yes** (but new-line slice under-covered in Sonar suite) |
| `cap646/parallel_invoke.py` | 33 | 33 | **0%** | **No** |
| `cap646/closure_guard.py` | 26 | 26 | **0%** | **No** (partial HMAC tests only) |
| `cap646/handlers/*` | 30 | 15 | ~50% | **No** |
| `cap978/institutional_gate.py` | 14 | 14 | **0%** | **No** |
| `cap646/batch_spine.py` | 12 | 7 | 41.7% | **Yes** |
| `cap646/batch01_dedicated.py` | 11 | 10 | 9.1% | **Yes** (whole-file 91% ≠ new-line 9%) |
| `cap646/batch03_dedicated.py` | 10 | 4 | 60% | **No** |
| `cap646/batch02_dedicated.py` | 9 | 3 | 66.7% | **Yes** |
| `cap646/runtime.py` | 8 | 6 | 25% | **Yes** |
| `macro_correlations.py` | 9 | 9 | **0%** | **No** |
| `bigquery_export.py` | 5 | 5 | **0%** | **No** (test existed but not in Sonar job) |
| `cap978/gate_verdict.py` | 4 | 4 | **0%** | **No** |
| `database.py` | 4 | 0 | 100% | **Yes** |
| `cap978/closure.py` | 2 | 2 | **0%** | **No** |
| `cap646/institutional_controls.py` | 1 | 1 | **0%** | **No** |
| `net_edge_truth.py` | 1 | 0 | 100% | **No** |
| `cap646/batch01_production.py` | 0 | 0 | n/a | **Yes** |
| `cap646/batch02_production.py` | 0 | 0 | n/a | **Yes** |

`scripts/**` excluded from `sonar.sources` — orchestrators not in New Code denominator.

---

## 3) New Code **outside** spine-suite (primary gap drivers)

| File | Uncovered new lines | Why absent from spine 8-file set |
|---|---:|---|
| `parallel_invoke.py` | 33 | Split-brain / inventory invoke helper |
| `closure_guard.py` | 26 | HMAC governance (new module) |
| `institutional_gate.py` (parallel phase) | 14 | cap978 gate, not cap646 spine |
| `macro_correlations.py` | 9 | Macro fallback flags |
| `handlers/*` | 15 | Refactored lazy routing |
| `bigquery_export.py` | 5 | BigQuery mock path |
| `gate_verdict.py` + `closure.py` | 6 | Verdict namespace isolation |

**Subtotal uncovered outside spine focus:** ~98 lines (≈52% of all uncovered new lines).

---

## 4) Shared / expanded modules (dedicated_common, provenance, closure)

| Module | Spine whole-file cov | Sonar new-line cov | Explanation |
|---|---:|---:|---|
| `dedicated_common.py` | 100% | 32.9% | PR added ~70 new lines (`holder_analytics_*`, `exchange_netflow_*`, `provenance_hot_storage_payload`); Sonar CI suite did not execute spine tests → new helpers mostly uncovered |
| `batch01_dedicated.py` | 91.3% | 9.1% | Refactor to shared helpers changed 11 lines; Sonar counts only those lines |
| `closure_guard.py` | n/a (new) | 0% | `write_closure_status` never tested; S2083 BLOCKER on path taint |
| `provenance_hot_storage_payload` | covered in spine | part of 47 miss | lives in `dedicated_common.py` new lines |

---

## 5) Root-cause equation (80% vs 26.09%)

```
Spine 80%  = Σ(covered_stmts_8_files) / Σ(stmts_8_files)     using SPINE_PYTEST
Sonar 26%  = covered_new_lines_253 / 253                    using sonarcloud.yml suite only
```

Three simultaneous differences:

1. **Denominator:** 2425 whole-file statements vs **253 new lines only**
2. **Numerator scope:** 8 modules vs **25+ production files** including cap978, handlers, closure_guard
3. **Test suite:** SPINE_PYTEST ⊄ Sonar `coverage.xml` job → Cobertura import under-reports spine + new modules

---

## 6) Remediation plan (this PR)

1. **Security:** fix `closure_guard.py` path injection via `path_safety.resolve_under` + allowlist (no NOSONAR).
2. **Tests:** `tests/test_sonar_pr356_new_code_coverage.py` — behavioral assertions on every uncovered New Code cluster.
3. **CI:** add `SPINE_PYTEST` + new test file to `.github/workflows/sonarcloud.yml` coverage generation.
4. **Verify:** re-run Sonar → `new_coverage ≥ 80%`, `new_security_rating = A`, QG PASSED.
