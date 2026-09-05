# ADR-001: Batch Handler Wrapper Deduplication — Revised (CLOSURE-REJECT-04)

**Status:** Superseded by ADR-001-r2  
**Date:** 2026-09-01  
**Standards:** ISO/IEC/IEEE 42010, DDD Bounded Context (Evans 2003)

## Context

`cap646/handlers/batch01.py`, `batch02.py`, and `batch03.py` were structurally identical wrappers routing to their respective `batch0N_production.execute` modules. pylint R0801 flagged Type-2 similarity.

## Prior error (CLOSURE-REJECT-03)

ADR-001 v1 cited Fowler's Rule of Three to **retain** three copies. That inverts the rule: the third duplicate is a signal to **begin** refactoring (Fowler, *Refactoring*, Rule attributed to Don Roberts).

## Decision (r2)

1. **Extract Function** — shared `cap646/handlers/_batch_route.py::route_batch_capability()` holds the common one-liner; batch handlers delegate to it.
2. **Bounded Context justification** — three handler modules remain as explicit DDD boundaries mapping official batch governance artifacts (1–50, 51–100, 101–150) to runtime dispatch in `cap646/runtime.py`. The shared router eliminates duplicated implementation without merging audit boundaries.

## Consequences

- **Positive:** R0801 duplication reduced; Rule of Three applied correctly.
- **Positive:** Per-batch stack traces and RTM alignment preserved.
- **Negative:** Four files instead of three (router + three handlers) — acceptable for clarity.

## Files

| File | Role |
|------|------|
| `cap646/handlers/_batch_route.py` | Shared `route_batch_capability()` |
| `cap646/handlers/batch01.py` | Wrapper → `batch01_production.execute` (IDs 1–50) |
| `cap646/handlers/batch02.py` | Wrapper → `batch02_production.execute` (IDs 51–100) |
| `cap646/handlers/batch03.py` | Wrapper → `batch03_production.execute` (IDs 101–150 prep) |
| `cap646/batch01_production.py` | Spine dispatch for batch01 |
| `cap646/batch02_production.py` | Spine router; delegates to `batch02_dedicated` or batch01 overlap |
| `cap646/batch02_dedicated.py` | Dedicated handlers `_cap051`–`_cap100` (except OVERLAP 55,56,59,60) |
