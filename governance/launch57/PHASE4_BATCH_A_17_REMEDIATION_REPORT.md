# Launch-57 Phase 4 / #17 Targeted Remediation Report

Implementation SHA: `847c38375b81dd5f5ba65cb3322698464e4ac181`
Failed IV SHA: `fe9d6b87`

## Root cause

exchange_whale_ratio computed whale significance from compute_whale_ls_ratio_114 without invoking classify_flow; disclosure flagged internal_not_counted_as_external_flow whenever whale_filtered_ratio was present.

## Remediation

Invoke canonical classify_flow in exchange_whale_ratio and gate significance via apply_internal_flow_whale_significance_filter; disclosure derives from runtime filtered result.

## Runtime proof

```json
{
  "internal_confirmed_exchange_whale_ratio": null,
  "economic_flow_exchange_whale_ratio": 1.5,
  "decision_driving_behavior_differs": true,
  "runtime_filter_applied": true
}
```

## Tests

- command: `python3 -m pytest tests/launch57/test_phase4_adaptive_batch_a.py::test_capability_17_whale_ratio_runtime_internal_flow_filter tests/launch57/test_phase4_adaptive_batch_a.py::test_capability_17_internal_flow_not_external tests/launch57/test_smart_money_batch1.py -q`
- exit_code: 0
- stdout: .......                                                                  [100%]

## Confirmations

```text
P4A_17_REMEDIATION_STATUS = PENDING_VERIFICATION
PHASE4_BATCH_B_NOT_STARTED = true
PASS_ENGINEERING_NOT_CLAIMED_FOR_17 = true
PASS_LIVE_NOT_CLAIMED = true
```
