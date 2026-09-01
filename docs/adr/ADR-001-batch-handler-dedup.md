# ADR-001: Batch Handler Wrapper Deduplication (Type-2 Clone)

**Status:** Accepted  
**Date:** 2026-09-01  
**Standards:** ISO/IEC/IEEE 42010, Roy & Cordy (2007) Type-2, Fowler Rule of Three

## Context

`cap646/handlers/batch01.py`, `batch02.py`, and `batch03.py` are structurally identical wrappers routing to their respective `batch0N_production.execute` modules.

## Decision

Retain three thin wrappers (explicit spine routing per official batch scope) rather than a single parameterized handler, because:

1. Official batch boundaries (1–50, 51–100, 101–150) are governance artifacts.
2. Runtime routing in `cap646/runtime.py` dispatches by `BATCH0N_IDS` frozensets.
3. Consolidation would blur audit boundaries required by CLOSURE-REJECT-03.

## Consequences

- **Positive:** Clear per-batch stack traces and RTM alignment.
- **Negative:** Type-2 pylint R0801 similarity flagged — documented in `CAP_DEDUP_AUDIT_1_100.json`.
- **Mitigation:** Shared `_stamp` logic remains in production modules, not handlers.
