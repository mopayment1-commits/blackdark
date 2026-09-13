# PARTIAL Closure Backlog — Phase 0 Freeze (35 items)

**Baseline:** 74 YES | 35 PARTIAL | 0 NO | 1 BLOCKED_EXTERNAL  
**Target:** 109 YES | 0 PARTIAL | 0 NO | 1 BLOCKED_EXTERNAL  
**Status:** CLOSED (all 35 upgraded to YES under R1)

## DSR partials (19)

| req_id | Acceptance criteria (governing quote) | Surfaces | Gap (was) | Closure control |
|---|---|---|---|---|
| DSR-001 | كل Dataset/Stream مادي يجب أن يملك Data Asset Contract canonical | decision, signal, oracle, enrichment, ledger_write | Catalog only | `checkpoint_dsr_001` → `data_asset_contract` |
| DSR-002 | Contract defines owner, purpose, schema, times, rights, retention, lineage… | all material | Catalog only | `checkpoint_dsr_002` field completeness |
| DSR-003 | PIT Evidence Contract for replay/backtest | all material | Catalog only | `checkpoint_dsr_003` `pit_contract` |
| DSR-004 | Reproducible benchmark from snapshot + versions | all material | Catalog only | `checkpoint_dsr_004` `reproducibility_pack` |
| DSR-006 | Schema versioning + compatibility | all material | Catalog only | `checkpoint_dsr_006` + pipeline `schema_evolution` |
| DSR-007 | Corrections record observed/effective/corrected-at | all material | Catalog only | `checkpoint_dsr_007` bitemporal |
| DSR-009 | Outcome evaluator version in lineage | all material | Catalog only | `checkpoint_dsr_009` |
| DSR-010 | Opportunity Universe Contract for recall | all material | Catalog only | `checkpoint_dsr_010` |
| DSR-011 | Entity assertion contract fields | all material | Catalog only | `checkpoint_dsr_011` |
| DSR-014 | Retention class + storage tier | all material | Catalog only | `checkpoint_dsr_014` + `retention.py` |
| DSR-015 | RTO/RPO restore evidence on critical registries | all material | Catalog only | `checkpoint_dsr_015` |
| DSR-017 | Quality failure affects availability/confidence | all material | Partial freshness | `checkpoint_dsr_017` + runtime freshness |
| DSR-018 | Champion/challenger promotion gate | all material | Catalog only | `checkpoint_dsr_018` |
| DSR-019 | Derived asset classification | all material | Catalog only | `checkpoint_dsr_019` |
| DSR-020 | Asset Value Ledger binding | all material | Catalog only | `checkpoint_dsr_020` |
| DSR-021 | Living Data Room index | all material | Catalog only | `checkpoint_dsr_021` |
| DSR-022 | Claim→evidence→version chain | all material | Catalog only | `checkpoint_dsr_022` |
| DSR-023 | Collection purpose/legal basis/minimization | all material | Catalog only | `checkpoint_dsr_023` + `legal.py` |
| DSR-024 | Flywheel gate closes when all DSR checkpoints run | all material | Meta partial | `checkpoint_dsr_024` closure gate |

## D-domain partials (16)

| req_id | Maps to | Closure |
|---|---|---|
| D-01 | DSR-001 | `checkpoint_dsr_001` |
| D-02 | DSR-003 | `checkpoint_dsr_003` |
| D-03 | DSR-006 | `checkpoint_dsr_006` |
| D-04 | DSR-014 | `checkpoint_dsr_014` |
| D-07 | DSR-009 | `checkpoint_dsr_009` |
| D-08 | DSR-010 | `checkpoint_dsr_010` |
| D-09 | DSR-011 | `checkpoint_dsr_011` |
| D-10 | DSR-019 | `checkpoint_dsr_019` |
| D-11 | DSR-014 | `checkpoint_dsr_014` (storage tier) |
| D-12 | DSR-015 | `checkpoint_dsr_015` |
| D-13 | DSR-016 | oracle chain tamper-evident (pre-existing YES) |
| D-14 | DSR-017 | `checkpoint_dsr_017` |
| D-15 | DSR-018 | `checkpoint_dsr_018` |
| D-17 | DSR-020 | `checkpoint_dsr_020` |
| D-19 | DSR-007 | `checkpoint_dsr_007` |
| D-20 | DSR-011 | `checkpoint_dsr_011` |

## R1 evidence (all 35)

- **Caller:** `data_governance/pipeline.py:run_material_pipeline` → `data_governance/dsr_checkpoints.py:apply_dsr_checkpoints`
- **Test:** `tests/test_data_governance_dsr_closure.py::test_dsr_checkpoint_removal_fails` (parametrized per DSR id)
- **Control removal:** monkeypatch checkpoint → `RuntimeError` propagates through `enforce_material_write`

## Residual BLOCKED_EXTERNAL (only)

| req_id | Reason |
|---|---|
| REQ-EV-PRODUCTION_VERIFIED | True production verification pipeline not verifiable in-repo |
