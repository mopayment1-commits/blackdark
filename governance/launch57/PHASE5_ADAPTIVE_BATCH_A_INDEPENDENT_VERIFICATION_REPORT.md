# Phase 5 / Batch A — Independent Verification Report

**Verification type:** independent engineering (read-only)  
**Implementation SHA:** `cef10db5`  
**Builder evidence SHA:** `8793b78c`  
**Product under test:** `cef10db5` (no later `launch57/` product changes)

## 1. Repository state

| Check | Result |
| --- | --- |
| Builder evidence implementation SHA | `cef10db5` — uniquely identified |
| Audited HEAD | `8793b78c` (governance evidence only after implementation) |
| Later product changes invalidating IV | **None** (`git diff cef10db5..HEAD -- launch57/` empty) |
| Canonical dispatch | `cap646.institutional_official_production` → `execute_launch57_derivatives_batch1` |
| Entry gate | `PHASE4_INDEPENDENT_VERDICT = PASS_ENGINEERING @ 8164312d` |

## 2. Capability verdicts

| # | Verdict | Key control |
| --- | --- | --- |
| 25 | PASS_ENGINEERING | OI direct evidence; price-context direction only; OI-trend limitation explicit; funding/taker contradiction drives `QUALIFIED_OI_CONTRADICTION` |
| 26 | PASS_ENGINEERING | Funding direction wired; contradiction surfaces; single-venue limitation (no cross-venue consensus claim) |
| 27 | PASS_ENGINEERING | Empty alerts → `success=false`, `NO_QUALIFYING_LIQUIDATION_CLUSTER`; global coverage FORBIDDEN in contract |
| 28 | PASS_ENGINEERING | Taker/leverage disagreement → `COMPONENT_DISAGREEMENT`; `market_indicator_only` preserved on leverage payload |
| 29 | PASS_ENGINEERING | Disagreement → `composite_score=null`, disagreements visible; aligned path preserves sentiment score without new weighting |

## 3. Bypass controls

| # | Bypass simulation | Result |
| --- | --- | --- |
| 25 | `apply_open_interest_derivatives_semantics` contradiction cleared | Answer state changes `QUALIFIED_OI_CONTRADICTION` → `OI_OBSERVABLE` |
| 26 | `apply_funding_rate_derivatives_semantics` contradiction cleared | Answer state changes `QUALIFIED_FUNDING_CONTRADICTION` → `LONG_CROWDED` |
| 27 | `apply_liquidation_derivatives_semantics` forced `LIQUIDATION_SIGNAL` | `success` changes `false` → `true` on empty alerts |
| 28 | `apply_taker_leverage_derivatives_semantics` disagreement cleared | Answer state changes `COMPONENT_DISAGREEMENT` → `TAKER_PRESSURE` |
| 29 | `compute_derivatives_sentiment_composite` disagreement suppressed | `composite_score` changes `null` → `0.8` |

## 4. Dependency-aware regression

Phase 5 Batch A appended derivatives helpers to shared support; only directly affected prior consumer regression-tested:

```text
python3 -m pytest tests/launch57/test_phase5_adaptive_batch_a.py tests/launch57/test_derivatives_batch1.py tests/launch57/test_phase4_adaptive_batch_c.py tests/launch57/test_smart_money_batch3.py -q
# 20 passed, 0 failed
```

Unaffected prior capabilities (Phase 4 Batch A/B, smart_money batch1/2) not re-verified per scope.

## 5. Residual gaps (non-blocking)

- `launch57/trust_adaptive_common.py` contains duplicate identical derivatives helper definitions; Python binds the later copy; runtime behavior verified identical.

## 6. Final verdicts

```text
PHASE5_BATCH_A_INDEPENDENT_VERDICT = PASS_ENGINEERING
PHASE5_BATCH_B_MAY_BEGIN = true
PASS_LIVE_NOT_CLAIMED = true
```

Audit conclusion only. No SSOT/register promotion.
