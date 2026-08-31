# Pytest 19-Failures Investigation — Batch 04 Gate

**Date:** 2026-08-30  
**Branch:** `cursor/batch-03-201-300-e85e`  
**Confirmed green baseline:** `origin/cursor/pytest-slow-institutional-e85e` @ `4a62398`  
**Baseline command:** `pytest -m "not slow"` → **922 passed, 0 failed** (reproduced in worktree)

## Executive verdict

The **19 failures from the full-suite log** (`docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_PYTEST.log`) are **not the same set** that was green in the confirmed **922/0** closure.

| Category | Count | Meaning |
|---|---:|---|
| Out of 922 scope (`@pytest.mark.slow`) | 4 | Never collected in institutional default run |
| Never in 922 scope (tests added in batch 01) | 2 | `accessibility_*` — did not exist at baseline |
| Fixed during batch 03 | 1 | `test_batch_test_mapping` — passes on current HEAD |
| In 922 scope, failed due to **branch divergence** (missing institutional commits) | 12 | Not caused by batch 01–03 code regressions |
| True batch 01 defect (new broken test, not a green regression) | 2 | `accessibility_*` — **fixed** in `accessibility_audit_service.py` |

After cherry-picking institutional fixes (`d4ed88c`, `9b5de8a`, `4a62398`) and adding `accessibility_audit_service.py`:

```bash
pytest -m "not slow"  →  1578 passed, 0 failed, 2 skipped, 4 deselected
```

## Scope proof (not assumption)

1. **922 baseline** is on institutional branch with `pytest.ini` `addopts = -m "not slow" --timeout=90 -q`.
2. **Full suite** on batch-03 (before slow filter) collected ~1584 tests → 19 failed.
3. **Common ancestor** `e4bcfd5` already failed pricing/codeql/rvm/wow/cap646 tests **before** batches 1–3.
4. Institutional branch commits **fixed** those tests; batch-03 branch diverged without merging them until this investigation.

## Per-test matrix (original 19)

| # | Test | Age (git) | In 922 scope? | Was green at 922? | Root cause | Batch 1–3 regression? |
|---:|---|---|---|---|---|---|
| 1 | `cap646/test_cap978_closure.py::test_external_registry` | 2026-08-21 (`e963ae0`) | Yes (fast) | Yes | External registry count drift; fixed by `4a62398` | **No** — branch divergence |
| 2 | `cap646/test_cap978_closure.py::test_evidence_room_snapshot` | 2026-08-21 | **No** (`@pytest.mark.slow`) | N/A | Excluded from default institutional run | N/A |
| 3 | `cap646/test_institutional_gate.py::test_external_registry_integrity` | 2026-08-21 (`1326cce`) | Yes | Yes | CAP-644 / registry integrity; fixed by `4a62398` | **No** |
| 4 | `cap646/test_institutional_gate.py::test_committed_artifacts_match_baseline` | 2026-08-21 | Yes | Yes | Committed artifact baseline drift; fixed by `4a62398` | **No** |
| 5 | `cap646/test_institutional_gate.py::test_commercial_launch_checklist` | 2026-08-21 | Yes | Yes | `total_external_items` 3 vs 4; fixed by `4a62398` | **No** |
| 6 | `cap646/test_institutional_gate.py::test_institutional_gate_sample` | 2026-08-21 | **No** (`slow`) | N/A | Excluded | N/A |
| 7 | `cap646/test_institutional_gate.py::test_institutional_gate_full` | 2026-08-21 | **No** (`slow`) | N/A | Excluded | N/A |
| 8 | `cap646/test_soft_launch_closure.py::test_soft_launch_closure_code_complete` | 2026-08-27 (`314d807`) | Yes | Yes | `external_registry_labeled` count; fixed by `4a62398` | **No** |
| 9 | `test_codeql_ssrf_log_safety.py::test_listed_modules_inline_log_scrub_not_helper_only` | 2026-08-11 (`c54586a`) | Yes | Yes | Missing inline CRLF scrub in `billing_service.py`; fixed by `9b5de8a` | **No** |
| 10 | `test_legal_shield_and_pricing_binding.py::test_founder_confirmed_price_ladder` | 2026-08-08 (`071bccc`) | Yes | Yes | PRO price `$19.99` vs expected `$29`; fixed by `9b5de8a` | **No** |
| 11 | `test_legal_shield_and_pricing_binding.py::test_pricing_tiers_order` | 2026-08-08 | Yes | Yes | Tier order `quant` vs `institutional`; fixed by `9b5de8a` | **No** |
| 12 | `test_legal_shield_and_pricing_binding.py::test_no_rejected_199_whale_desk_in_catalog` | 2026-08-08 | Yes | Yes | Catalog tier naming; fixed by `9b5de8a` | **No** |
| 13 | `test_missing_capabilities_closure.py::test_accessibility_static_audit` | **2026-08-30** (`a4f1d9f` batch 01) | **No** (new) | N/A | `ModuleNotFoundError: accessibility_audit_service` | Batch 01 introduced broken test — **fixed** |
| 14 | `test_missing_capabilities_closure.py::test_accessibility_api_report` | **2026-08-30** (`a4f1d9f`) | **No** (new) | N/A | Same missing module | Batch 01 introduced broken test — **fixed** |
| 15 | `test_payments_usd_security.py::test_payments_architecture_usd_no_pan` | 2026-08-08 (`f49eb18`) | Yes | Yes | Pricing ladder drift; fixed by `9b5de8a` | **No** |
| 16 | `test_payments_usd_security.py::test_billing_tiers_currency_usd` | 2026-08-08 | Yes | Yes | Whale `$4999` vs `$4900`; fixed by `9b5de8a` | **No** |
| 17 | `test_pdf_capability_registry.py::test_batch_test_mapping` | 2026-08-30 (`a4f1d9f`) | Yes (new test) | Failed pre-fix | Batch mapping order for 262–300; fixed `0cfa2a8` | **Fixed in batch 03** |
| 18 | `test_rvm_system.py::test_governing_sources_present_and_hashed` | 2026-08-21 (`af89b6e`) | Yes | Yes | Stale PDF sha256 in `rvm/governing.py`; fixed by `4a62398` | **No** |
| 19 | `test_wow_unique_surfaces.py::test_tier_unique_and_wow_eight` | 2026-08-09 (`dd5a306`) | Yes | Yes | Missing `decision_desk` in `UNIQUE_BY_TIER`; fixed by `9b5de8a` | **No** |

## Post-batch-04 track (slow institutional suite)

The 4 `@pytest.mark.slow` tests remain outside default institutional scope. Run via:

```bash
scripts/run_institutional_pytest.sh
```

Track separately after batch 04 opens; not blockers for the 922-scope gate.

## Batch 04 gate status

- **Zero regression** in institutional scope (`-m "not slow"`): **1578 passed, 0 failed**
- Institutional fixes merged into batch-03 branch
- Accessibility module closure complete
- Slow cap646 suite: scheduled post-batch-04 track (approved criterion #7)
