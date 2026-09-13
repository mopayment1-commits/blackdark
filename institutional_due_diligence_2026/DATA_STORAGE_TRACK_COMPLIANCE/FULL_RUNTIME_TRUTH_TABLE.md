# FULL RUNTIME TRUTH TABLE — Data / Storage / Tracking (v4_v2)

Governing SSOT: `docs/standards/domain/BLACKDARK_مرجع_حاكم_للبيانات_والتخزين_والتراك_Institutional_Hardened_v4_v2.md`
Mandatory requirements: **110**

## Counts

| Status | Count |
|---|---:|
| YES | 14 |
| PARTIAL | 48 |
| NO | 48 |
| BLOCKED_EXTERNAL | 0 |
| N/A | 0 |
| **SUM** | **110** |

## Per-requirement truth (R1 evidence)

| req_id | status | surfaces | caller → control | failing test | gap |
|---|---|---|---|---|---|
| DSR-001 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-001 live caller + failing test under R1 |
| DSR-002 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-002 live caller + failing test under R1 |
| DSR-003 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-003 live caller + failing test under R1 |
| DSR-004 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-004 live caller + failing test under R1 |
| DSR-005 | YES | decision, signal, oracle, enrichment, ledger_write | blackdark/data_governance/runtime.py:enforce_material_write → data_governance/rights.py:assert_usage_allowed | tests/test_data_governance_runtime_enforcement.py::test_rights_denied_blocks_material_write |  |
| DSR-006 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-006 live caller + failing test under R1 |
| DSR-007 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-007 live caller + failing test under R1 |
| DSR-008 | YES | decision, signal, oracle, enrichment, ledger_write | decision_ledger.py:record_decision → runtime.py:intelligence_receipt | tests/test_data_governance_runtime_enforcement.py::test_decision_write_attaches_intelligence_receipt |  |
| DSR-009 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-009 live caller + failing test under R1 |
| DSR-010 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-010 live caller + failing test under R1 |
| DSR-011 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-011 live caller + failing test under R1 |
| DSR-012 | YES | decision, signal, oracle, enrichment, ledger_write | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evidence_promotion_blocked_simulated_to_production |  |
| DSR-013 | YES | decision, signal, oracle, enrichment, ledger_write | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evidence_promotion_blocked_simulated_to_production | Promotion gate YES for control; PRODUCTION_VERIFIED evidence remains BLOCKED_EXTERNAL |
| DSR-014 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-014 live caller + failing test under R1 |
| DSR-015 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-015 live caller + failing test under R1 |
| DSR-016 | YES | decision, signal, oracle, enrichment, ledger_write | oracle_audit_chain.py:append_prediction_record → verify_chain (RuntimeError fail-closed) | tests/test_oracle_audit_chain.py |  |
| DSR-017 | PARTIAL | decision, signal, oracle, enrichment, ledger_write | runtime.py:enforce_material_write → data_governance/freshness.py:gate_admission | tests/test_data_governance_p0_test_matrix.py::test_freshness_gate_admits_recent_payload | Freshness gate wired on runtime path; not all ingestion surfaces use gate_admission |
| DSR-018 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-018 live caller + failing test under R1 |
| DSR-019 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-019 live caller + failing test under R1 |
| DSR-020 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-020 live caller + failing test under R1 |
| DSR-021 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-021 live caller + failing test under R1 |
| DSR-022 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-022 live caller + failing test under R1 |
| DSR-023 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Catalog/spine reference only; no per-DSR-023 live caller + failing test under R1 |
| DSR-024 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES |
| D-01 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-02 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-03 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-04 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-05 | YES | decision, signal, oracle, enrichment, ledger_write | blackdark/data_governance/runtime.py:enforce_material_write → data_governance/rights.py:assert_usage_allowed | tests/test_data_governance_runtime_enforcement.py::test_rights_denied_blocks_material_write |  |
| D-06 | YES | decision, signal, oracle, enrichment, ledger_write | decision_ledger.py:record_decision → runtime.py:intelligence_receipt | tests/test_data_governance_runtime_enforcement.py::test_decision_write_attaches_intelligence_receipt |  |
| D-07 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-08 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-09 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-10 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-11 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-12 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-13 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-14 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-15 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-16 | YES | decision, signal, oracle, enrichment, ledger_write | oracle_audit_chain.py:append_prediction_record → verify_chain (RuntimeError fail-closed) | tests/test_oracle_audit_chain.py |  |
| D-17 | PARTIAL | decision, signal, oracle, enrichment, ledger_write | runtime.py:enforce_material_write → data_governance/freshness.py:gate_admission | tests/test_data_governance_p0_test_matrix.py::test_freshness_gate_admits_recent_payload | Freshness gate wired on runtime path; not all ingestion surfaces use gate_admission |
| D-18 | YES | decision, signal, oracle, enrichment, ledger_write | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evidence_promotion_blocked_simulated_to_production |  |
| D-19 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| D-20 | PARTIAL | decision, signal, oracle, enrichment, ledger_write |  |  | Gate closure depends on full DSR/D/DIG reconciliation — not all mandatory items YES Domain defect not independently runtime-wired. |
| DIG-001 | YES | enrichment, signal, decision, oracle | api/routers/data_governance.py → data_governance/rights.py + freshness.py | tests/test_data_governance_p0_test_matrix.py |  |
| DIG-002 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/normalization.py, data_governance/streaming.py |
| DIG-003 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/quality.py, data_governance/reliability.py |
| DIG-004 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/provenance.py, data_governance/methodology.py |
| DIG-005 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/gates.py |
| DIG-006 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/legal.py |
| DIG-007 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/registry.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-008 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/fallback.py |
| DIG-009 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/registry.py, data_sources_registry.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-010 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/streaming.py |
| DIG-011 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/streaming.py |
| DIG-012 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/streaming.py |
| DIG-013 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/slo.py |
| DIG-014 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/slo.py |
| DIG-015 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/l2_l3.py, data_governance/order_book.py |
| DIG-016 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/historical_depth.py |
| DIG-017 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/normalization.py |
| DIG-018 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/raw_landing.py |
| DIG-019 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/provenance.py, bd_platform/v4_v2_persistent_registries.py |
| DIG-020 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/methodology.py |
| DIG-021 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/quality.py, failure/quality.py |
| DIG-022 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/reconciliation.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-023 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/reliability.py |
| DIG-024 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/slo.py |
| DIG-025 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/fallback.py |
| DIG-026 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/rate_limit.py |
| DIG-027 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/rights.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-028 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/retention.py |
| DIG-029 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/legal.py |
| DIG-030 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/retention.py |
| DIG-031 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/schema_evolution.py |
| DIG-032 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/timestamps.py, timezone/format.py |
| DIG-033 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/streaming.py |
| DIG-034 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: bd_platform/v4_v2_persistent_registries.py |
| DIG-035 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/decision_surface.py |
| DIG-036 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: decision_truth/change.py |
| DIG-037 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: decision_truth/half_life.py |
| DIG-038 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/gates.py |
| DIG-039 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/registry.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-040 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/normalization.py |
| DIG-041 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/fallback.py |
| DIG-042 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/observability.py |
| DIG-043 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/gates.py |
| DIG-044 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/raw_landing.py, data_governance/provenance.py |
| DIG-045 | PARTIAL | enrichment, signal, decision, oracle | modules exist: tests/test_data_governance_p0_test_matrix.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-046 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/registry.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-047 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/registry.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-048 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/reliability.py |
| DIG-049 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/registry.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-050 | PARTIAL | enrichment, signal, decision, oracle | modules exist: data_governance/registry.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-051 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/decision_surface.py |
| DIG-052 | PARTIAL | enrichment, signal, decision, oracle | modules exist: regulatory_compliance_guard.py | tests/test_data_governance_p0_test_matrix.py | Module exists but no per-requirement failing test proving live production caller under R1 |
| DIG-053 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/pipeline.py |
| DIG-054 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/gates.py |
| DIG-055 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/pipeline.py |
| DIG-056 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: bd_platform/data_governance_source_driven_engineering.py |
| DIG-057 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/pipeline.py |
| DIG-058 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/pipeline.py, data_governance/decision_surface.py |
| DIG-059 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: scripts/data_governance_final_reconciliation.py |
| DIG-060 | NO | enrichment, signal, decision, oracle |  |  | Missing modules: data_governance/pipeline.py |
| REQ-0816 | PARTIAL | decision, signal, oracle, enrichment, ledger_write | decision_ledger.py:record_decision → runtime.py:intelligence_receipt | tests/test_data_governance_runtime_enforcement.py::test_decision_write_attaches_intelligence_receipt | Receipt on wired ledgers; SQL DE spine (blackdark/data/systems_api) not yet gated |
| REQ-0167 | YES | decision | decision_ledger.py:record_decision → runtime.py:require_capability_dna | tests/test_data_governance_runtime_enforcement.py::test_record_decision_calls_runtime_gate | DNA enforced on decision ledger; not on cap646 execute rows |
| REQ-EV-PRODUCTION_VERIFIED | PARTIAL | decision, signal, oracle | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evidence_promotion_blocked_simulated_to_production | BLOCKED_EXTERNAL for true production verification pipeline; gate YES, evidence NO |
| GATE-001 | YES | decision, signal, oracle, cap_execute, enrichment, ledger_write | blackdark/data_governance/runtime.py:governance_enforce_enabled | tests/test_data_governance_runtime_enforcement.py::test_governance_default_enforce_on |  |
| GATE-002 | YES | ledger_write | decision_ledger.py → blackdark/data_governance/runtime.py:enforce_material_write; signal_registry.py → blackdark/data_governance/runtime.py:enforce_material_write; oracle_audit_chain.py → blackdark/data_governance/runtime.py:enforce_material_write; user_exposure_log.py → blackdark/data_governance/runtime.py:enforce_material_write; market_event_library.py → blackdark/data_governance/runtime.py:enforce_material_write; failure_corpus.py → blackdark/data_governance/runtime.py:enforce_material_write | tests/test_data_governance_runtime_enforcement.py |  |
| GATE-003 | YES | decision, signal, oracle, ledger_write | runtime.py:enforce_material_write raises GovernanceViolationError | tests/test_data_governance_runtime_enforcement.py::test_rights_denied_blocks_material_write |  |
