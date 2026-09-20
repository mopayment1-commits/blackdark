# Phase 4 / #17 — Independent Re-Verification Report

**Verification type:** independent engineering re-verification (read-only)  
**Remediation implementation SHA:** `847c3837`  
**Remediation evidence SHA:** `3ed3a6a3`  
**Product under test:** `847c3837` (no later product changes)

## 1. Repository state

| Check | Result |
| --- | --- |
| Audited HEAD | `3ed3a6a3` (evidence only after implementation) |
| Later product changes | **None** |
| Prior NOT_COMPLETE IV | Preserved @ `fe9d6b87` |

## 2. Failed control re-test — PASS

**Control:** Whale-ratio path must apply canonical `classify_flow` at runtime.

| Check | Result |
| --- | --- |
| `classify_flow` → `exchange_whale_ratio` → filtered output | **Yes** |
| INTERNAL_CONFIRMED suppresses ratio | `exchange_whale_ratio: null` |
| ECONOMIC_FLOW retains ratio | `exchange_whale_ratio: 1.667` |
| Disclosure matches runtime | `runtime_filter_applied: true`; suppressed flags match |
| Single classifier (no duplicate path) | **Yes** — `exchange_internal_flow_filter.classify_flow` only |
| PARKED/legacy dependency | **None** |

## 3. Runtime probes (real `classify_flow`)

| Classification | `exchange_whale_ratio` | `answer_state` | `internal_not_counted` |
| --- | --- | --- | --- |
| INTERNAL_CONFIRMED | `null` | `suppressed_internal_flow` | true |
| ECONOMIC_FLOW | `1.667` | `long` | false |

## 4. Tests

```
python3 -m pytest tests/launch57/test_phase4_adaptive_batch_a.py tests/launch57/test_smart_money_batch1.py -q
# 11 passed, 0 failed
```

Behavioral test `test_capability_17_whale_ratio_runtime_internal_flow_filter` fails if runtime filter removed.

## 5. Verdicts

```text
P4A:#17_REVERIFICATION = PASS_ENGINEERING
PHASE4_BATCH_A_INDEPENDENT_VERDICT = PASS_ENGINEERING
PHASE4_BATCH_B_MAY_BEGIN = true
```

## 6. Confirmations

```text
PASS_LIVE_NOT_CLAIMED = true
REGISTER_STATUS_PROMOTION = false
```
