# ADR-003: Batch02 vs Batch03 Dedicated Module Parallelism

## Status
Accepted — CLOSURE-MANDATE-COMPLETION item 3

## Context
`batch02_dedicated.py` and `batch03_dedicated.py` share structural patterns (`_capNNN` handlers, `EXPECTED_SURFACE` maps) for different official ID ranges (51–100 vs 101–150 prep).

## Decision
Extract shared mechanics to `cap646/dedicated_common.py`:
- `make_wrap_binding()` — payload wrapper factory
- `execute_dedicated_caps()` — shared execute dispatch tail

Remaining per-batch differences are **Bounded Context** (TOGAF G189): distinct capability ID sets and goal surfaces — not Rule-of-Three duplication.

## Consequences
- pylint R0801 on cap646/ → **0** after extraction (verified 2026-09-01)
- batch03 prep remains prohibited for institutional closure execution
