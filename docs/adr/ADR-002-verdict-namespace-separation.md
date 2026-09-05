# ADR-002: Verdict Namespace Separation (cap978 Gate vs 826 RTM)

**Status:** Accepted  
**Date:** 2026-09-01  
**Standards:** ISO/IEC/IEEE 42010, ISO/IEC 25010

## Context

`verify_institutional_closure.py --full` previously required `closure_verdict == "VERIFIED COMPLETE"`.
`cap646/runtime.py` bans `VERIFIED_COMPLETE` on 826 RTM `classification` fields.

## Analysis (CLOSURE-MANDATE-FINAL item 1)

| Namespace | Field | Allowed values | Scope |
|-----------|-------|----------------|-------|
| **826 RTM** | `result["classification"]` | `PRODUCTION-ALIGNED`, `NOT_COMPLETE`, `DUPLICATE/ALREADY_COVERED`, `EXTERNAL/BLOCKED` | `cap646/rtm_classification.py` |
| **cap978 per-cap verify** | `verify_functional_978()["verdict"]` | `VERIFIED_COMPLETE`, `FUNCTIONALLY_INCOMPLETE`, … | Legacy CI per-capability |
| **cap978 institutional gate** | `institutional_closure_978()["verdict"]` | **`INSTITUTIONAL_GATE_PASS`** / `NOT_READY` | Gate-full only |

**Conclusion:** `VERIFIED COMPLETE` was a **legacy cap978 gate label**, not the 826 RTM classification — but the naming collision violated ISO/IEC 25010 modularity clarity.

## Decision

1. Rename institutional gate success verdict to **`INSTITUTIONAL_GATE_PASS`** (`cap978/gate_verdict.py`).
2. Keep `VERIFIED_COMPLETE` only inside per-capability `cap978/verify.py` (isolated namespace).
3. `cap646/runtime.py` never emits `VERIFIED_COMPLETE` on RTM fields.

## Consequences

- Prior gate-full `exit 0` used the old string — **invalid for closure claims**; gate-full must be re-run after this ADR.
- `docs/cap978/EVIDENCE_ROOM_SNAPSHOT.json` top-level `verdict` updated to `INSTITUTIONAL_GATE_PASS`.
