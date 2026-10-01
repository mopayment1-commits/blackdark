# ADR-BATCH03-002: OVERLAP-PARTIAL TIME Decision — Tolerate (30-day sunset)

**Status:** ACCEPTED  
**Date:** 2026-09-03  
**Scope:** Batch03 IDs #103, #129  
**Standards:** TOGAF G189 MECE · Fowler Strangler Fig

## Context

IDs #103 (API Data Platform) and #129 (Sentiment Intelligence) are listed in official batch03 (101–150) but execute exclusively via `cap646.batch01_production` because runtime routes `BATCH01_IDS` before `BATCH03_IDS`. No `batch03_dedicated` handler exists for these IDs (by design).

## Decision (TIME: **Tolerate**)

| ID | Spine | Rationale |
|----|-------|-----------|
| #103 | batch01 | Elite-tier API platform already bound in batch01; MECE DISTINCT from #129 |
| #129 | batch01 | Sentiment intelligence bound in batch01 overlap extension |

**Sunset date:** **2026-10-03** (30 days from decision)

If not resolved by sunset → decision auto-converts to **Eliminate** (remove duplicate batch03 catalog listing or add dedicated batch03 spine with explicit owner approval).

## Acceptance criteria (tolerate period)

- RTM status `OVERLAP-PARTIAL` with `production_spine=batch01`
- Runtime raises if `batch03_dedicated.execute(103|129)` called directly
- MECE audit: #103 vs #129 = DISTINCT goals/surfaces

## Consequences

- Positive: No double implementation; batch01 spine remains SSOT during tolerate window.
- Negative: Official batch numbering shows batch03 IDs served by batch01 — documented in RTM notes.
