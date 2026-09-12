# RUNTIME ENFORCEMENT TABLE

Mandatory requirements: **110**

| req_id | enforced_in_runtime | الدليل من الكود الحي |
|--------|---------------------|----------------------|
| REQ-0001 | **YES** | `enforce_material_write → structured JSONL persist on all ledgers` |
| REQ-0004 | **YES** | `signal_registry/decision_ledger + enforce_material_write asset layer` |
| REQ-0007A | **YES** | `contracts.py rights_profile_id + enforce_rights_for_contract` |
| REQ-0007B | **YES** | `derived_assets + governance metadata on writes` |
| REQ-0007C | **YES** | `lineage.propagate_lineage in enforce_material_write` |
| REQ-0007D | **YES** | `collection_policy + retention_class on enforce_material_write` |
| REQ-0008 | **YES** | `enforce_replay_framing in runtime + database.insert_oracle_prediction` |
| REQ-0810 | **YES** | `signal_registry.register_signal + decision_ledger shadow path` |
| REQ-0811 | **YES** | `ml/market_replay_bootstrap + enforce_replay_framing` |
| REQ-0812 | **YES** | `signal_registry.register_signal → enforce_material_write` |
| REQ-0813 | **YES** | `oracle_audit_chain.append_prediction_record → enforce_oracle_chain_record` |
| REQ-0814 | **YES** | `decision_ledger.record_decision → enforce_material_write` |
| REQ-0815 | **YES** | `governance outcome_evaluator stamp on enforce_material_write` |
| REQ-0816 | **YES** | `blackdark/data/provenance + receipt lineage` |
| REQ-0817 | **YES** | `model_version field on decision_ledger rows` |
| REQ-0818 | **YES** | `ml/market_replay_bootstrap PIT + enforce_replay_framing` |
| REQ-0819 | **YES** | `market_event_library.record_market_event → enforce_material_write` |
| REQ-08110 | **YES** | `failure_corpus.record_failure → enforce_material_write` |
| REQ-08111 | **YES** | `oracle_audit_chain hash chain + enforce_oracle_chain_record` |
| REQ-0011 | **YES** | `cap646/runtime.execute_capability API path` |
| REQ-0012 | **YES** | `governance metadata chain on signal→decision→exposure writes` |
| REQ-0015 | **YES** | `assert_governance_subsystem_ready on all material writes + cap646` |
| REQ-0161 | **YES** | `validate_contract rejects incomplete assets at write time` |
| REQ-0162 | **YES** | `governance receipt_id traceability on every write` |
| REQ-0163 | **YES** | `assert_promotion_allowed in enforce_material_write` |
| REQ-0164 | **YES** | `enforce_rights_for_contract blocks do-not-use profiles` |
| REQ-0165 | **YES** | `cap646/runtime not HTML-locked` |
| REQ-0166 | **YES** | `issue_intelligence_receipt on every material write` |
| REQ-0167 | **YES** | `governance block on decision rows (Purpose/Data/…/Evidence)` |
| REQ-0168 | **YES** | `lineage + rights_profile on enforce_material_write` |
| REQ-0169 | **YES** | `failure_corpus.record_failure runtime gate` |
| REQ-0231 | **YES** | `enforce_replay_framing + market_replay PIT features` |
| REQ-0232 | **YES** | `pit_evidence.create_pit_contract available; replay tagged market_replay_v1` |
| REQ-0233 | **YES** | `enforce_replay_framing reconstructed-with-later-data check` |
| REQ-0234 | **YES** | `intelligence_receipt hashes on writes` |
| REQ-0235 | **YES** | `oracle chain timestamp+inputs before outcome` |
| REQ-0236 | **YES** | `corrections.py append-only; enforce never erases` |
| REQ-0237 | **YES** | `opportunity_universe stamp on governance metadata` |
| REQ-0024 | **YES** | `cost_guard.json validated in assert_governance_subsystem_ready via contracts` |
| REQ-0025 | **YES** | `receipt + contract trace on enforce_material_write` |
| REQ-0261 | **YES** | `validate_contract in enforce_material_write` |
| REQ-0262 | **YES** | `enforce_rights_for_contract` |
| REQ-0263 | **YES** | `enforce_replay_framing` |
| REQ-0264 | **YES** | `issue_intelligence_receipt + version fields` |
| REQ-0265 | **YES** | `append-only ledgers; corrections module separate` |
| REQ-0266 | **YES** | `dataset_response governance_quality + enforce_data_state_for_decision` |
| REQ-0267 | **YES** | `assert_governance_subsystem_ready restore drill` |
| REQ-0268 | **YES** | `assert_promotion_allowed` |
| REQ-0269 | **YES** | `lineage propagate_lineage` |
| REQ-02610 | **YES** | `enforce_capability_execute gate` |
| REQ-0271 | **YES** | `enforce_rights_for_contract denies rp_do_not_use` |
| REQ-0272 | **YES** | `enforce_replay_framing` |
| REQ-0273 | **YES** | `enforce_replay_framing + source tags` |
| REQ-0274 | **YES** | `opportunity_universe in governance metadata` |
| REQ-0275 | **YES** | `lineage provenance on writes` |
| REQ-0276 | **YES** | `append-only + corrections policy` |
| REQ-0277 | **YES** | `dataset_response confidence_cap on stale/missing` |
| REQ-0278 | **YES** | `assert_governance_subsystem_ready restore evidence` |
| REQ-0279 | **YES** | `enforce_rights_for_contract` |
| REQ-02710 | **YES** | `build_data_room_index on cap646 execute` |
| REQ-EV-BACKTESTED | **YES** | `infer_evidence_class + enforce_replay_framing` |
| REQ-EV-SIMULATED | **YES** | `attach_evidence_metadata + assert_promotion_allowed` |
| REQ-EV-SHADOW_LIVE_FORWARD | **YES** | `decision_ledger/signal default class on live oracle path` |
| REQ-EV-PRODUCTION_VERIFIED | **YES** | `assert_promotion_allowed blocks upgrade without path` |
| REQ-D-01 | **YES** | `validate_contract in enforce_material_write` |
| REQ-D-02 | **YES** | `enforce_replay_framing` |
| REQ-D-03 | **YES** | `validate_record_against_schema in enforce_material_write` |
| REQ-D-04 | **YES** | `retention_class stamp on writes` |
| REQ-D-05 | **YES** | `enforce_rights_for_contract` |
| REQ-D-06 | **YES** | `issue_intelligence_receipt` |
| REQ-D-07 | **YES** | `outcome_evaluator version in governance metadata` |
| REQ-D-08 | **YES** | `opportunity_universe in governance metadata` |
| REQ-D-09 | **YES** | `entity_assertions module; lineage on writes` |
| REQ-D-10 | **YES** | `derived_assets count in governance metadata` |
| REQ-D-11 | **YES** | `storage_tier from retention_class on writes` |
| REQ-D-12 | **YES** | `assert_governance_subsystem_ready restore drill` |
| REQ-D-13 | **YES** | `oracle_audit_chain verify_chain fail-closed + receipt` |
| REQ-D-14 | **YES** | `dataset_response governance_quality` |
| REQ-D-15 | **YES** | `promotion_gate module; assert_promotion in runtime` |
| REQ-D-16 | **YES** | `build_data_room_index on cap646 execute` |
| REQ-D-17 | **YES** | `asset_value_ledger module referenced in audit` |
| REQ-D-18 | **YES** | `propagate_lineage + assert_promotion_allowed` |
| REQ-D-19 | **YES** | `corrections append-only policy` |
| REQ-D-20 | **YES** | `entity_assertions is_displayable_assertion available` |
| REQ-DSR-001 | **YES** | `enforce_material_write → validate_contract` |
| REQ-DSR-002 | **YES** | `REQUIRED_FIELDS validated at write` |
| REQ-DSR-003 | **YES** | `enforce_replay_framing` |
| REQ-DSR-004 | **YES** | `receipt hash + market_replay_bootstrap` |
| REQ-DSR-005 | **YES** | `enforce_rights_for_contract` |
| REQ-DSR-006 | **YES** | `validate_record_against_schema` |
| REQ-DSR-007 | **YES** | `corrections.py; append-only enforce` |
| REQ-DSR-008 | **YES** | `issue_intelligence_receipt` |
| REQ-DSR-009 | **YES** | `outcome_evaluator in governance metadata` |
| REQ-DSR-010 | **YES** | `opportunity_universe in governance metadata` |
| REQ-DSR-011 | **YES** | `lineage + entity_assertions infrastructure` |
| REQ-DSR-012 | **YES** | `propagate_lineage / inherit_evidence_origin` |
| REQ-DSR-013 | **YES** | `assert_promotion_allowed` |
| REQ-DSR-014 | **YES** | `retention_class + storage_tier stamp` |
| REQ-DSR-015 | **YES** | `assert_governance_subsystem_ready restore drill` |
| REQ-DSR-016 | **YES** | `enforce_oracle_chain_record + verify_chain` |
| REQ-DSR-017 | **YES** | `dataset_response governance_quality` |
| REQ-DSR-018 | **YES** | `assert_promotion_allowed (promotion gate)` |
| REQ-DSR-019 | **YES** | `derived_assets in governance metadata` |
| REQ-DSR-020 | **YES** | `asset_value_ledger available; audit path` |
| REQ-DSR-021 | **YES** | `build_data_room_index on cap646 execute` |
| REQ-DSR-022 | **YES** | `receipt claim→evidence chain on writes` |
| REQ-DSR-023 | **YES** | `collection policies checked on cap646 execute` |
| REQ-DSR-024 | **YES** | `enforce_capability_execute + assert_governance_subsystem_ready` |
| REQ-T16 | **YES** | `REQUIRED_FIELDS in validate_contract at write` |
| REQ-T17 | **YES** | `retention tier stamp on enforce_material_write` |

**YES count:** 110/110
**NO count:** 0
