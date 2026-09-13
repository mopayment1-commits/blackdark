# FULL RUNTIME TRUTH TABLE — Data / Storage / Tracking (v4_v2)

Governing SSOT: `docs/standards/domain/BLACKDARK_مرجع_حاكم_للبيانات_والتخزين_والتراك_Institutional_Hardened_v4_v2.md`
Mandatory requirements: **110**

## Counts

| Status | Count |
|---|---:|
| YES | 109 |
| PARTIAL | 0 |
| NO | 0 |
| BLOCKED_EXTERNAL | 1 |
| N/A | 0 |
| **SUM** | **110** |

## Per-requirement truth (R1 evidence)

| req_id | status | surfaces | caller → control | failing test | gap |
|---|---|---|---|---|---|
| DSR-001 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_001 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-002 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_002 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-003 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_003 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-004 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_004 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-005 | YES | decision, signal, oracle, enrichment, ledger_write | blackdark/data_governance/runtime.py:enforce_material_write → data_governance/rights.py:assert_usage_allowed | tests/test_data_governance_runtime_enforcement.py::test_rights_denied_blocks_material_write |  |
| DSR-006 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_006 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-007 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_007 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-008 | YES | decision, signal, oracle, enrichment, ledger_write | decision_ledger.py:record_decision → runtime.py:intelligence_receipt | tests/test_data_governance_runtime_enforcement.py::test_decision_write_attaches_intelligence_receipt |  |
| DSR-009 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_009 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-010 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_010 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-011 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_011 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-012 | YES | decision, signal, oracle, enrichment, ledger_write | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evidence_promotion_blocked_simulated_to_production |  |
| DSR-013 | YES | decision, signal, oracle, enrichment, ledger_write | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evidence_promotion_blocked_simulated_to_production | Promotion gate YES for control; PRODUCTION_VERIFIED evidence remains BLOCKED_EXTERNAL |
| DSR-014 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_014 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-015 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_015 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-016 | YES | decision, signal, oracle, enrichment, ledger_write | oracle_audit_chain.py:append_prediction_record → verify_chain (RuntimeError fail-closed) | tests/test_oracle_audit_chain.py |  |
| DSR-017 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_017 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-018 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_018 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-019 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_019 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-020 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_020 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-021 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_021 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-022 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_022 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-023 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_023 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DSR-024 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_024 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-01 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_001 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-02 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_003 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-03 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_006 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-04 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_014 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-05 | YES | decision, signal, oracle, enrichment, ledger_write | blackdark/data_governance/runtime.py:enforce_material_write → data_governance/rights.py:assert_usage_allowed | tests/test_data_governance_runtime_enforcement.py::test_rights_denied_blocks_material_write |  |
| D-06 | YES | decision, signal, oracle, enrichment, ledger_write | decision_ledger.py:record_decision → runtime.py:intelligence_receipt | tests/test_data_governance_runtime_enforcement.py::test_decision_write_attaches_intelligence_receipt |  |
| D-07 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_009 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-08 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_010 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-09 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_011 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-10 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_019 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-11 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_014 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-12 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_015 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-13 | YES | decision, signal, oracle, enrichment, ledger_write | oracle_audit_chain.py:append_prediction_record → verify_chain (RuntimeError fail-closed) | tests/test_oracle_audit_chain.py |  |
| D-14 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_017 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-15 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_018 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-16 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_021 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-17 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_020 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-18 | YES | decision, signal, oracle, enrichment, ledger_write | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evidence_promotion_blocked_simulated_to_production |  |
| D-19 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_007 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| D-20 | YES | decision, signal, oracle, enrichment, ledger_write | pipeline.py:run_material_pipeline → data_governance/dsr_checkpoints.py:checkpoint_dsr_011 | tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails |  |
| DIG-001 | YES | enrichment, signal, decision, oracle | api/routers/data_governance.py → data_governance/rights.py + freshness.py | tests/test_data_governance_p0_test_matrix.py |  |
| DIG-002 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/normalization.py, data_governance/streaming.py | tests/test_data_governance_dig_closure.py |  |
| DIG-003 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/freshness.py, data_governance/quality.py | tests/test_data_governance_dig_closure.py |  |
| DIG-004 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/provenance.py, data_governance/methodology.py | tests/test_data_governance_dig_closure.py |  |
| DIG-005 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/gates.py, decision_truth/admission.py | tests/test_data_governance_dig_closure.py |  |
| DIG-006 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/legal.py | tests/test_data_governance_dig_closure.py |  |
| DIG-007 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/registry.py | tests/test_data_governance_dig_closure.py |  |
| DIG-008 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/registry.py, data_governance/fallback.py | tests/test_data_governance_dig_closure.py |  |
| DIG-009 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/registry.py, data_sources_registry.py | tests/test_data_governance_dig_closure.py |  |
| DIG-010 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/streaming.py, exchange_ws_hub.py | tests/test_data_governance_dig_closure.py |  |
| DIG-011 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → blackdark/data/jobs.py, data_governance/streaming.py | tests/test_data_governance_dig_closure.py |  |
| DIG-012 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/streaming.py | tests/test_data_governance_dig_closure.py |  |
| DIG-013 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/slo.py | tests/test_data_governance_dig_closure.py |  |
| DIG-014 | YES | enrichment, signal, decision, oracle | api/routers/data_governance.py → data_governance/rights.py + freshness.py | tests/test_data_governance_p0_test_matrix.py |  |
| DIG-015 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/l2_l3.py, data_governance/order_book.py | tests/test_data_governance_dig_closure.py |  |
| DIG-016 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/historical_depth.py | tests/test_data_governance_dig_closure.py |  |
| DIG-017 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/normalization.py, blackdark/canonical/layer.py | tests/test_data_governance_dig_closure.py |  |
| DIG-018 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/raw_landing.py | tests/test_data_governance_dig_closure.py |  |
| DIG-019 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/provenance.py, bd_platform/v4_v2_persistent_registries.py | tests/test_data_governance_dig_closure.py |  |
| DIG-020 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/methodology.py | tests/test_data_governance_dig_closure.py |  |
| DIG-021 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/quality.py, failure/quality.py | tests/test_data_governance_dig_closure.py |  |
| DIG-022 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/reconciliation.py | tests/test_data_governance_dig_closure.py |  |
| DIG-023 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/reliability.py | tests/test_data_governance_dig_closure.py |  |
| DIG-024 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/slo.py | tests/test_data_governance_dig_closure.py |  |
| DIG-025 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/fallback.py | tests/test_data_governance_dig_closure.py |  |
| DIG-026 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/rate_limit.py | tests/test_data_governance_dig_closure.py |  |
| DIG-027 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/rights.py | tests/test_data_governance_dig_closure.py |  |
| DIG-028 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/retention.py | tests/test_data_governance_dig_closure.py |  |
| DIG-029 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/legal.py | tests/test_data_governance_dig_closure.py |  |
| DIG-030 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/retention.py | tests/test_data_governance_dig_closure.py |  |
| DIG-031 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/schema_evolution.py | tests/test_data_governance_dig_closure.py |  |
| DIG-032 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/timestamps.py, timezone/format.py | tests/test_data_governance_dig_closure.py |  |
| DIG-033 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/streaming.py | tests/test_data_governance_dig_closure.py |  |
| DIG-034 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → bd_platform/v4_v2_persistent_registries.py | tests/test_data_governance_dig_closure.py |  |
| DIG-035 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/decision_surface.py | tests/test_data_governance_dig_closure.py |  |
| DIG-036 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → decision_truth/change.py | tests/test_data_governance_dig_closure.py |  |
| DIG-037 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → decision_truth/half_life.py | tests/test_data_governance_dig_closure.py |  |
| DIG-038 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/gates.py | tests/test_data_governance_dig_closure.py |  |
| DIG-039 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/registry.py | tests/test_data_governance_dig_closure.py |  |
| DIG-040 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/normalization.py | tests/test_data_governance_dig_closure.py |  |
| DIG-041 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/fallback.py, data_governance/registry.py | tests/test_data_governance_dig_closure.py |  |
| DIG-042 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/observability.py | tests/test_data_governance_dig_closure.py |  |
| DIG-043 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/gates.py, decision_enrichment.py | tests/test_data_governance_dig_closure.py |  |
| DIG-044 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/raw_landing.py, data_governance/provenance.py | tests/test_data_governance_dig_closure.py |  |
| DIG-045 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → tests/test_data_governance_p0_test_matrix.py | tests/test_data_governance_dig_closure.py |  |
| DIG-046 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/registry.py | tests/test_data_governance_dig_closure.py |  |
| DIG-047 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/registry.py | tests/test_data_governance_dig_closure.py |  |
| DIG-048 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/reliability.py | tests/test_data_governance_dig_closure.py |  |
| DIG-049 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/registry.py | tests/test_data_governance_dig_closure.py |  |
| DIG-050 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/registry.py | tests/test_data_governance_dig_closure.py |  |
| DIG-051 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/decision_surface.py | tests/test_data_governance_dig_closure.py |  |
| DIG-052 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → regulatory_compliance_guard.py | tests/test_data_governance_dig_closure.py |  |
| DIG-053 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/pipeline.py | tests/test_data_governance_dig_closure.py |  |
| DIG-054 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/gates.py | tests/test_data_governance_dig_closure.py |  |
| DIG-055 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/pipeline.py | tests/test_data_governance_dig_closure.py |  |
| DIG-056 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → bd_platform/data_governance_source_driven_engineering.py | tests/test_data_governance_dig_closure.py | Engineering register separated; production verified remains BLOCKED_EXTERNAL |
| DIG-057 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/pipeline.py | tests/test_data_governance_dig_closure.py |  |
| DIG-058 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/pipeline.py, data_governance/decision_surface.py | tests/test_data_governance_dig_closure.py |  |
| DIG-059 | YES | enrichment, signal, decision, oracle | scripts/data_governance_final_reconciliation.py → data_storage_runtime_truth_audit.py | tests/test_data_governance_dig_closure.py |  |
| DIG-060 | YES | enrichment, signal, decision, oracle | runtime.py:enforce_material_write → pipeline.py → data_governance/pipeline.py, decision_enrichment.py | tests/test_data_governance_dig_closure.py |  |
| REQ-0816 | YES | decision, signal, oracle, enrichment, ledger_write | ledgers + systems_api.governance_bridge → runtime.py:intelligence_receipt | tests/test_data_governance_runtime_enforcement.py::test_decision_write_attaches_intelligence_receipt |  |
| REQ-0167 | YES | decision, cap_execute | decision_ledger + cap646/runtime.py → runtime.py:require_capability_dna | tests/test_data_governance_dig_closure.py::test_cap646_execute_governance |  |
| REQ-EV-PRODUCTION_VERIFIED | BLOCKED_EXTERNAL | decision, signal, oracle | cap646/evidence_class.py:assert_promotion_allowed | tests/test_data_governance_runtime_enforcement.py::test_evidence_promotion_blocked_simulated_to_production | True production verification pipeline not verifiable in-repo; anti-promotion gate YES |
| GATE-001 | YES | decision, signal, oracle, cap_execute, enrichment, ledger_write | blackdark/data_governance/runtime.py:governance_enforce_enabled | tests/test_data_governance_runtime_enforcement.py::test_governance_default_enforce_on |  |
| GATE-002 | YES | ledger_write | decision_ledger.py → blackdark/data_governance/runtime.py:enforce_material_write; signal_registry.py → blackdark/data_governance/runtime.py:enforce_material_write; oracle_audit_chain.py → blackdark/data_governance/runtime.py:enforce_material_write; user_exposure_log.py → blackdark/data_governance/runtime.py:enforce_material_write; market_event_library.py → blackdark/data_governance/runtime.py:enforce_material_write; failure_corpus.py → blackdark/data_governance/runtime.py:enforce_material_write | tests/test_data_governance_runtime_enforcement.py |  |
| GATE-003 | YES | decision, signal, oracle, ledger_write | runtime.py:enforce_material_write raises GovernanceViolationError | tests/test_data_governance_runtime_enforcement.py::test_rights_denied_blocks_material_write |  |
