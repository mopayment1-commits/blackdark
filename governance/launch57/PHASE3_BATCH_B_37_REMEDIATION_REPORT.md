# Launch-57 Phase 3 Batch B — #37 Targeted Remediation Report

Implementation SHA: `57dfacfd3b650f34c1ff0398ef7d57cbbc668d03`
Failed IV SHA: `6c9614b6`

## Root cause

decision_engine.composite_score was copied from build_multi_dim_analysis_73 raw composite, which includes unapproved external_macro in its weighted sum; build_approved_evidence_composition only flagged unapproved inputs without excluding them from decision-driving semantics.

## Remediation

Introduce compute_approved_decision_composite to derive decision-driving composite_score from approved Launch-57 dimension sources only (renormalized weights). Raw multi_dimensional output remains observable/auditable; unapproved dimensions are recorded in observable_non_decision_driving and excluded_from_decision_driving.

## Canonical path preserved

`launch57.decision_batch2:cross_market_decision_engine`

## Runtime non-influence proof

```json
{
  "approved_inputs_constant": true,
  "macro_1_raw_composite": 4.0,
  "macro_9_raw_composite": 6.0,
  "macro_1_decision_composite": 5.0,
  "macro_9_decision_composite": 5.0,
  "decision_composite_stable": true,
  "approved_launch57_evidence_only": true,
  "external_macro_observable_only": true
}
```

## Tests

- command: `python3 -m pytest tests/launch57/test_phase3_adaptive_batch_b.py tests/launch57/test_decision_batch2.py tests/launch57/test_phase3_adaptive_batch_a.py -q`
- exit_code: 0
- stdout: ...............                                                          [100%]

## Residual gap

NONE

## Confirmations

```text
P3B_37_REMEDIATION_STATUS = PENDING_VERIFICATION
PHASE3_INTEGRATION_REMAINS_OPEN = true
PHASE4_NOT_STARTED = true
PASS_ENGINEERING_NOT_CLAIMED_FOR_37 = true
PASS_LIVE_NOT_CLAIMED = true
```
