# ADR-003: Batch Dedicated Module Shared Mechanics vs Bounded Contexts

## Status
Accepted — CLOSURE-MANDATE-LAST (supersedes completion draft)

## Context
Official Batch 02 (`cap646/batch02_dedicated.py`, IDs 51–100) and Batch 03 prep (`cap646/batch03_dedicated.py`, IDs 101–150, **prohibited for closure execution**) share structural patterns:
- `_capNNN` async handlers
- `EXPECTED_SURFACE` maps per batch
- `execute()` dispatch tails

Prior pylint R0801 flagged three duplicate regions; jscpd flagged two cross-batch clones (import header + provenance payload).

Per **Gartner TIME** and **CWE-1041**, structural similarity across different capability ID ranges is not automatically "redundant code" — it may be **Bounded Context** (TOGAF G189) when goals and ID namespaces differ.

## Decision
1. **Extract Function** (Fowler) into `cap646/dedicated_common.py`:
   - `sym`, `addr`, `seed`, `wrap`, `success_from`
   - `make_wrap_binding()` — eliminates per-batch `_wrap` body duplication
   - `execute_dedicated_caps()` — eliminates per-batch `execute()` tail duplication
   - `provenance_hot_storage_payload()` — eliminates #63/#106 jscpd clone

2. **Retain separate** `EXPECTED_SURFACE` and `_DISPATCH` maps per batch — these are **Bounded Context** artifacts, not Rule-of-Three violations.

3. **Reject** merging batch02 and batch03 into one module — would violate Batch 03 execution prohibition and blur official spine boundaries.

## Alternatives Rejected
| Alternative | Why rejected |
|-------------|----------------|
| Single `batch_dedicated.py` for 51–150 | Collapses prohibited batch03 prep into official spine |
| Rule-of-Three "keep as-is" on `_wrap` bodies | Violates CWE-1041; pylint R0801 = 3 |
| Tolerate forever without sunset | Violates CLOSURE-MANDATE-LAST Section Zero rules |

## Consequences
- pylint R0801 on `cap646/`: **0** (verified)
- jscpd official spine 1–100 (excl. batch03 prep): **0 clones**
- jscpd with batch03 prep: import-header similarity may remain (Bounded Context — **Invest**, not Eliminate)
- batch03 prep remains **prohibited** for institutional closure until owner opens Batch 03

## Evidence
- `cap646/dedicated_common.py`
- `docs/DUPLICATION_LOCK_TABLE_1_100.json`
- `docs/adr/ADR-003-batch-dedicated-bounded-context.md` (this file)
