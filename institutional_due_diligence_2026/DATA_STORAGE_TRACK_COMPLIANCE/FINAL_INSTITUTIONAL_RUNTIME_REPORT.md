# FINAL INSTITUTIONAL RUNTIME REPORT

## Counts

| Status | Count |
|---|---:|
| YES | 74 |
| PARTIAL | 35 |
| NO | 0 |
| BLOCKED_EXTERNAL | 1 |
| N/A | 0 |

## Production enforcement default = ON

- `BLACKDARK_GOVERNANCE_ENFORCE` defaults to **1** (enforce ON).
- Production profile cannot disable enforcement (`test_governance_cannot_disable_in_production`).

## Non-YES requirements

- **DSR-001** (PARTIAL): Catalog/spine reference only; no per-DSR-001 live caller + failing test under R1
- **DSR-002** (PARTIAL): Catalog/spine reference only; no per-DSR-002 live caller + failing test under R1
- **DSR-003** (PARTIAL): Catalog/spine reference only; no per-DSR-003 live caller + failing test under R1
- **DSR-004** (PARTIAL): Catalog/spine reference only; no per-DSR-004 live caller + failing test under R1
- **DSR-006** (PARTIAL): Catalog/spine reference only; no per-DSR-006 live caller + failing test under R1
- **DSR-007** (PARTIAL): Catalog/spine reference only; no per-DSR-007 live caller + failing test under R1
- **DSR-009** (PARTIAL): Catalog/spine reference only; no per-DSR-009 live caller + failing test under R1
- **DSR-010** (PARTIAL): Catalog/spine reference only; no per-DSR-010 live caller + failing test under R1
- **DSR-011** (PARTIAL): Catalog/spine reference only; no per-DSR-011 live caller + failing test under R1
- **DSR-014** (PARTIAL): Catalog/spine reference only; no per-DSR-014 live caller + failing test under R1
- **DSR-015** (PARTIAL): Catalog/spine reference only; no per-DSR-015 live caller + failing test under R1
- **DSR-017** (PARTIAL): Freshness gate wired on runtime path; not all ingestion surfaces use gate_admission
- **DSR-018** (PARTIAL): Catalog/spine reference only; no per-DSR-018 live caller + failing test under R1
- **DSR-019** (PARTIAL): Catalog/spine reference only; no per-DSR-019 live caller + failing test under R1
- **DSR-020** (PARTIAL): Catalog/spine reference only; no per-DSR-020 live caller + failing test under R1
- **DSR-021** (PARTIAL): Catalog/spine reference only; no per-DSR-021 live caller + failing test under R1
- **DSR-022** (PARTIAL): Catalog/spine reference only; no per-DSR-022 live caller + failing test under R1
- **DSR-023** (PARTIAL): Catalog/spine reference only; no per-DSR-023 live caller + failing test under R1
- **DSR-024** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES
- **D-01** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-02** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-03** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-04** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-07** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-08** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-09** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-10** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-11** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-12** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-13** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-14** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-15** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-17** (PARTIAL): Freshness gate wired on runtime path; not all ingestion surfaces use gate_admission
- **D-19** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **D-20** (PARTIAL): Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired.
- **REQ-EV-PRODUCTION_VERIFIED** (BLOCKED_EXTERNAL): True production verification pipeline not verifiable in-repo; anti-promotion gate YES

## Sample re-verification (≥15, read-oriented)

| req_id | status | caller | test |
|---|---|---|---|
| DSR-005 | YES | blackdark/data_governance/runtime.py:enforce_material_write → data_governance/ri | tests/test_data_governance_runtime_enforcement.py::test_righ |
| DSR-008 | YES | decision_ledger.py:record_decision → runtime.py:intelligence_receipt | tests/test_data_governance_runtime_enforcement.py::test_deci |
| DSR-012 | YES | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evid |
| DSR-014 | PARTIAL |  |  |
| DSR-016 | YES | oracle_audit_chain.py:append_prediction_record → verify_chain (RuntimeError fail | tests/test_oracle_audit_chain.py |
| DSR-017 | PARTIAL | runtime.py:enforce_material_write → data_governance/freshness.py:gate_admission | tests/test_data_governance_p0_test_matrix.py::test_freshness |
| D-05 | YES | blackdark/data_governance/runtime.py:enforce_material_write → data_governance/ri | tests/test_data_governance_runtime_enforcement.py::test_righ |
| D-18 | YES | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evid |
| DIG-001 | YES | api/routers/data_governance.py → data_governance/rights.py + freshness.py | tests/test_data_governance_p0_test_matrix.py |
| DIG-005 | YES | runtime.py:enforce_material_write → pipeline.py → data_governance/gates.py, deci | tests/test_data_governance_dig_closure.py |
| DIG-014 | YES | api/routers/data_governance.py → data_governance/rights.py + freshness.py | tests/test_data_governance_p0_test_matrix.py |
| REQ-0816 | YES | ledgers + systems_api.governance_bridge → runtime.py:intelligence_receipt | tests/test_data_governance_runtime_enforcement.py::test_deci |
| REQ-0167 | YES | decision_ledger + cap646/runtime.py → runtime.py:require_capability_dna | tests/test_data_governance_dig_closure.py::test_cap646_execu |
| REQ-EV-PRODUCTION_VERIFIED | BLOCKED_EXTERNAL | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evid |
| GATE-001 | YES | blackdark/data_governance/runtime.py:governance_enforce_enabled | tests/test_data_governance_runtime_enforcement.py::test_gove |
| GATE-002 | YES | decision_ledger.py → blackdark/data_governance/runtime.py:enforce_material_write | tests/test_data_governance_runtime_enforcement.py |
| GATE-003 | YES | runtime.py:enforce_material_write raises GovernanceViolationError | tests/test_data_governance_runtime_enforcement.py::test_righ |

## Declarations (R5)

- **IN_REPO_RUNTIME_COMPLIANCE** = **YES**
- **FULL_FILE_IN_REPO_CLOSURE** = **NO**
- **LIVE_LAUNCH_READY** = **NO**

### Launch blockers (data/storage/tracking)

- REQ-EV-PRODUCTION_VERIFIED

## Statement

No claim of 110/110 YES. Honest counts: 74 YES / 35 PARTIAL / 0 NO / 1 BLOCKED_EXTERNAL.

Prior inflated 110/110 claims are **not** inherited; this report is rebuilt from live call paths only.
