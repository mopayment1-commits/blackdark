# RUNTIME ENFORCEMENT TABLE

> Generated from live call graph only. PARTIAL = wired but incomplete. NO = not on live path.

Mandatory requirements: **110**

| req_id | enforced_in_runtime | الدليل من الكود الحي |
|--------|---------------------|----------------------|
| REQ-0001 | **YES** | `decision_ledger.record_decision→enforce_material_write→JSONL persist` |
| REQ-0004 | **YES** | `signal_registry/decision_ledger + enforce_material_write asset layer` |
| REQ-0007A | **YES** | `runtime.enforce_rights_for_contract on every material write` |
| REQ-0007B | **YES** | `runtime.enforce_material_write→derived_assets metadata stamp` |
| REQ-0007C | **YES** | `runtime.enforce_material_write→lineage.propagate_lineage` |
| REQ-0007D | **YES** | `runtime.enforce_material_write→retention_class + collection_policy gate` |
| REQ-0008 | **YES** | `runtime.enforce_replay_framing + database.insert_oracle_prediction` |
| REQ-0810 | **YES** | `signal_registry.register_signal + decision_ledger shadow path` |
| REQ-0811 | **YES** | `ml/market_replay_bootstrap→create_pit_contract + enforce_replay_framing` |
| REQ-0812 | **YES** | `signal_registry.register_signal→enforce_material_write` |
| REQ-0813 | **YES** | `oracle_audit_chain.append_prediction_record→enforce_oracle_chain_record` |
| REQ-0814 | **YES** | `decision_ledger.record_decision→enforce_material_write` |
| REQ-0815 | **YES** | `database.resolve_oracle_prediction→enforce_oracle_outcome_resolution` |
| REQ-0816 | **PARTIAL** | `runtime._stamp_provenance hash on writes; full DB provenance on ingestors only` |
| REQ-0817 | **YES** | `decision_ledger.record_decision model_version field` |
| REQ-0818 | **YES** | `market_replay_bootstrap→create_pit_contract + enforce_replay_framing per sample` |
| REQ-0819 | **YES** | `market_event_library.record_market_event→enforce_material_write` |
| REQ-08110 | **YES** | `failure_corpus.record_failure→enforce_material_write` |
| REQ-08111 | **YES** | `oracle_audit_chain verify_chain + enforce_oracle_chain_record` |
| REQ-0011 | **YES** | `cap646/runtime.execute_capability API path` |
| REQ-0012 | **YES** | `signal→decision→exposure governance metadata chain on writes` |
| REQ-0015 | **YES** | `runtime.assert_governance_subsystem_ready on material writes + cap646` |
| REQ-0161 | **YES** | `runtime.enforce_material_write→validate_contract fail-closed` |
| REQ-0162 | **YES** | `runtime.enforce_material_write→issue_intelligence_receipt receipt_id` |
| REQ-0163 | **YES** | `runtime.enforce_material_write→assert_promotion_allowed + evaluate_promotion_gate` |
| REQ-0164 | **YES** | `runtime.enforce_rights_for_contract blocks do-not-use profiles` |
| REQ-0165 | **YES** | `cap646/runtime not HTML-locked` |
| REQ-0166 | **YES** | `runtime.enforce_material_write→issue_intelligence_receipt` |
| REQ-0167 | **PARTIAL** | `governance sub-block on rows; full Capability DNA not stamped per row` |
| REQ-0168 | **YES** | `runtime.enforce_material_write lineage + rights_profile` |
| REQ-0169 | **YES** | `failure_corpus.record_failure→enforce_material_write` |
| REQ-0231 | **YES** | `enforce_replay_framing + market_replay PIT contract per sample` |
| REQ-0232 | **YES** | `runtime.enforce_replay_framing→create_pit_contract on replay sources` |
| REQ-0233 | **YES** | `runtime.enforce_replay_framing reconstructed_with_later_data label check` |
| REQ-0234 | **YES** | `issue_intelligence_receipt hashes on material writes` |
| REQ-0235 | **YES** | `oracle chain timestamp+inputs before outcome via enforce_oracle_chain_record` |
| REQ-0236 | **YES** | `decision_ledger.link_exposure/link_outcome→enforce_ledger_link_update→record_correction` |
| REQ-0237 | **YES** | `runtime.enforce_material_write opportunity_universe stamp` |
| REQ-0024 | **YES** | `runtime.assert_governance_subsystem_ready→_enforce_cost_guards fail-closed` |
| REQ-0025 | **YES** | `runtime.enforce_material_write receipt + contract trace` |
| REQ-0261 | **YES** | `runtime.enforce_material_write→validate_contract` |
| REQ-0262 | **YES** | `runtime.enforce_rights_for_contract` |
| REQ-0263 | **YES** | `runtime.enforce_replay_framing` |
| REQ-0264 | **YES** | `issue_intelligence_receipt + version fields on writes` |
| REQ-0265 | **YES** | `decision_ledger.link_*→record_correction append-only policy` |
| REQ-0266 | **YES** | `response_metadata.dataset_response + decision_enrichment enforce_data_state_for_decision` |
| REQ-0267 | **YES** | `runtime.assert_governance_subsystem_ready restore drill` |
| REQ-0268 | **YES** | `runtime.enforce_material_write assert_promotion_allowed + promotion_gate` |
| REQ-0269 | **YES** | `runtime.enforce_material_write propagate_lineage` |
| REQ-02610 | **YES** | `cap646/runtime→enforce_capability_execute` |
| REQ-0271 | **YES** | `runtime.enforce_rights_for_contract denies rp_do_not_use` |
| REQ-0272 | **YES** | `runtime.enforce_replay_framing` |
| REQ-0273 | **YES** | `runtime.enforce_replay_framing + source tags` |
| REQ-0274 | **YES** | `runtime.enforce_material_write opportunity_universe metadata` |
| REQ-0275 | **YES** | `runtime._stamp_provenance + lineage on material writes` |
| REQ-0276 | **YES** | `decision_ledger.link_*→enforce_ledger_link_update→record_correction` |
| REQ-0277 | **YES** | `response_metadata.dataset_response confidence_cap on stale/missing` |
| REQ-0278 | **YES** | `runtime.assert_governance_subsystem_ready restore evidence` |
| REQ-0279 | **YES** | `runtime.enforce_rights_for_contract` |
| REQ-02710 | **YES** | `cap646/runtime→enforce_capability_execute→build_data_room_index` |
| REQ-EV-BACKTESTED | **YES** | `infer_evidence_class + enforce_replay_framing on replay sources` |
| REQ-EV-SIMULATED | **YES** | `attach_evidence_metadata + promotion gate on writes` |
| REQ-EV-SHADOW_LIVE_FORWARD | **YES** | `decision_ledger/signal default class on live oracle path` |
| REQ-EV-PRODUCTION_VERIFIED | **PARTIAL** | `promotion_gate blocks upgrade; no external production verification pipeline` |
| REQ-D-01 | **YES** | `runtime.enforce_material_write→validate_contract` |
| REQ-D-02 | **YES** | `runtime.enforce_replay_framing→create_pit_contract` |
| REQ-D-03 | **YES** | `runtime.enforce_material_write→validate_record_against_schema` |
| REQ-D-04 | **YES** | `runtime.enforce_material_write retention_class stamp` |
| REQ-D-05 | **YES** | `runtime.enforce_rights_for_contract` |
| REQ-D-06 | **YES** | `runtime.enforce_material_write→issue_intelligence_receipt` |
| REQ-D-07 | **YES** | `database.resolve_oracle_prediction→enforce_oracle_outcome_resolution` |
| REQ-D-08 | **YES** | `runtime.enforce_material_write opportunity_universe metadata` |
| REQ-D-09 | **YES** | `runtime.enforce_material_write→_record_entity_for_material` |
| REQ-D-10 | **YES** | `runtime.enforce_material_write derived_assets count metadata` |
| REQ-D-11 | **YES** | `runtime.enforce_material_write storage_tier from retention` |
| REQ-D-12 | **YES** | `runtime.assert_governance_subsystem_ready restore drill` |
| REQ-D-13 | **YES** | `oracle_audit_chain verify_chain + enforce_oracle_chain_record` |
| REQ-D-14 | **YES** | `response_metadata + decision_enrichment enforce_data_state_for_decision` |
| REQ-D-15 | **YES** | `runtime.enforce_material_write→_enforce_promotion_gate` |
| REQ-D-16 | **YES** | `cap646/runtime→build_data_room_index` |
| REQ-D-17 | **YES** | `runtime.enforce_material_write→record_asset_value` |
| REQ-D-18 | **YES** | `runtime.enforce_material_write propagate_lineage + promotion gate` |
| REQ-D-19 | **YES** | `decision_ledger.link_*→enforce_ledger_link_update→record_correction` |
| REQ-D-20 | **YES** | `runtime.enforce_material_write→_record_entity_for_material` |
| REQ-DSR-001 | **YES** | `runtime.enforce_material_write→validate_contract` |
| REQ-DSR-002 | **YES** | `validate_contract REQUIRED_FIELDS at write time` |
| REQ-DSR-003 | **YES** | `runtime.enforce_replay_framing→create_pit_contract` |
| REQ-DSR-004 | **YES** | `create_pit_contract + receipt hash on replay writes` |
| REQ-DSR-005 | **YES** | `runtime.enforce_rights_for_contract` |
| REQ-DSR-006 | **YES** | `runtime.enforce_material_write→validate_record_against_schema` |
| REQ-DSR-007 | **YES** | `decision_ledger.link_*→enforce_ledger_link_update→record_correction` |
| REQ-DSR-008 | **YES** | `runtime.enforce_material_write→issue_intelligence_receipt` |
| REQ-DSR-009 | **YES** | `database.resolve_oracle_prediction→enforce_oracle_outcome_resolution` |
| REQ-DSR-010 | **YES** | `runtime.enforce_material_write opportunity_universe metadata` |
| REQ-DSR-011 | **YES** | `runtime.enforce_material_write→_record_entity_for_material` |
| REQ-DSR-012 | **YES** | `runtime.enforce_material_write propagate_lineage / inherit_evidence_origin` |
| REQ-DSR-013 | **YES** | `runtime.enforce_material_write assert_promotion_allowed + promotion_gate` |
| REQ-DSR-014 | **YES** | `runtime.enforce_material_write retention_class + storage_tier` |
| REQ-DSR-015 | **YES** | `runtime.assert_governance_subsystem_ready restore drill` |
| REQ-DSR-016 | **YES** | `oracle_audit_chain→enforce_oracle_chain_record + verify_chain` |
| REQ-DSR-017 | **YES** | `response_metadata + decision_enrichment enforce_data_state_for_decision` |
| REQ-DSR-018 | **YES** | `runtime.enforce_material_write→_enforce_promotion_gate` |
| REQ-DSR-019 | **YES** | `runtime.enforce_material_write derived_assets metadata` |
| REQ-DSR-020 | **YES** | `runtime.enforce_material_write→record_asset_value` |
| REQ-DSR-021 | **YES** | `cap646/runtime→build_data_room_index` |
| REQ-DSR-022 | **YES** | `runtime.enforce_material_write→_register_material_claim` |
| REQ-DSR-023 | **YES** | `cap646/runtime→enforce_capability_execute collection policies` |
| REQ-DSR-024 | **YES** | `cap646/runtime→enforce_capability_execute + assert_governance_subsystem_ready` |
| REQ-T16 | **YES** | `validate_contract REQUIRED_FIELDS at write` |
| REQ-T17 | **YES** | `runtime.enforce_material_write retention tier stamp` |

**YES count:** 107/110
**PARTIAL count:** 3
**NO count:** 0
**Remaining PARTIAL:** REQ-0816, REQ-0167, REQ-EV-PRODUCTION_VERIFIED
