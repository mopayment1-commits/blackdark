# Phase 4 Adaptive Batch A — Independent Verification Report

**Verification type:** independent engineering (read-only)  
**Implementation SHA:** `321abff8`  
**Builder evidence SHA:** `5013313f`  
**Audited HEAD:** `5013313f`

## 1. Repository state

| Check | Result |
| --- | --- |
| Delta range | `c58c58a4..321abff8` |
| Product files | `trust_adaptive_common.py`, `smart_money_batch1.py` |
| Register/SSOT changed | **No** |

## 2. Capability verification

### #20 — PASS_ENGINEERING

- Attribution/cohort derives from `address_labels_cohorts` → `b2b_relationships_status_137`
- `attribution_uncertainty_visible` and `coverage_limits_visible` true; `coverage_qualified` when labels empty
- Dependency chain authorized per CAP-0092 consumer paths (`bd_platform/onchain_platform_layer.py`)
- No PARKED/legacy runtime dependency detected on canonical path

### #16 — PASS_ENGINEERING

- `answer_state` derived from net flow (`NET_INFLOW` for positive net)
- `exchange_flow_not_generic_movement` true; `certainty_not_implied` true
- Disclosure tied to real `exchange_netflow_probe` semantics

### #17 — NOT_COMPLETE

**Failing control:** `exchange_whale_ratio` does not invoke `classify_flow` or apply internal-flow classification. `build_whale_ratio_internal_flow_disclosure` sets `internal_not_counted_as_external_flow` true whenever `whale_filtered_ratio` is present (presentation-only).

| Probe | Result |
| --- | --- |
| `internal_flow_filter` + INTERNAL_CONFIRMED | `internal_not_external_flow: true` |
| Whale ratio with INTERNAL_CONFIRMED in params | ratio **1.667** |
| Whale ratio with ECONOMIC_FLOW in params | ratio **1.667** (unchanged) |
| Runtime internal-flow filter on whale path | **false** |

`internal_flow_filter` entrypoint passes; whale-ratio path fails runtime behavior requirement.

### #13 — PASS_ENGINEERING

- `inference_not_raw_flow_fact` true; narratives from `enrich_whale_narratives`
- Supporting evidence and uncertainty visible (`uncertainty_qualified` when sparse)

### #14 — PASS_ENGINEERING

- Ranking from `smart_money_leaderboard` via canonical screener (`ETH` > `BTC` by `total_usd`)
- `screening_from_approved_launch57_evidence` with declared approved components
- `ranking_qualitative_not_certainty` true

## 3. Shared Adaptive support — PASS

- Support-only; no competing truth owner
- Phase 3 Batch B + decision_batch2 regression: **27/27 pass**

## 4. Tests

```
python3 -m pytest tests/launch57/test_phase4_adaptive_batch_a.py tests/launch57/test_smart_money_batch1.py tests/launch57/test_phase3_adaptive_batch_b.py tests/launch57/test_decision_batch2.py -q
# 27 passed, 0 failed
```

## 5. Verdicts

```text
P4A:#20 = PASS_ENGINEERING
P4A:#16 = PASS_ENGINEERING
P4A:#17 = NOT_COMPLETE
P4A:#13 = PASS_ENGINEERING
P4A:#14 = PASS_ENGINEERING
PHASE4_BATCH_A_INDEPENDENT_VERDICT = NOT_COMPLETE
PHASE4_BATCH_B_MAY_BEGIN = false
```

## 6. Confirmations

```text
TEMPORAL_WORKSTREAM_REOPENED = false
PASS_LIVE_NOT_CLAIMED = true
REGISTER_STATUS_PROMOTION = false
```
