# ADR-BATCH03-001: REUSED-LINK TIME Decision — Migrate (Canonical + Facade)

**Status:** ACCEPTED  
**Date:** 2026-09-03  
**Scope:** Batch03 IDs #106, #107, #110, #125  
**Standards:** Fowler Rule of Three · ISO/IEC 25010 Modularity · CWE-1041

## Context

Catalog declares DUPLICATE/ALREADY_COVERED for four batch03 IDs whose goals are already served by batch02 canonicals (#63, #64, #69, #85). Prior batch03_prep work implemented goal-equivalent facades with `catalog_link.duplicate_of`.

## Decision (TIME: **Migrate**)

| Duplicate | Canonical | Action |
|-----------|-----------|--------|
| #106 | #63 | Facade via `provenance_hot_storage_payload` + top-level `catalog_link` |
| #107 | #64 | Facade via `registry_stats()` + `catalog_link` |
| #110 | #69 | Facade via `build_cross_domain_decision_payload` + `catalog_link` |
| #125 | #85 | Facade via `derivatives_overview` + `catalog_link` |

- **Eliminate:** rejected — catalog IDs 106/107/110/125 remain user-facing in official batch03 RTM.
- **Invest:** rejected — canonical SSOT already PRODUCTION-ALIGNED in batch02.
- **Tolerate:** rejected — no sunset-only deferral; Type-4 contract enforced in CI.

## Structural guarantee

- `tests/cap646/test_batch03_reused_link_contract.py` — 5 symbols × 4 pairs
- `tests/cap646/test_batch03_gateway_canonical_entitlement_contract.py` — gateway/runtime tier alignment
- `cap646/institutional_gateway.py` — `canonical_id()` before entitlement check

## Consequences

- Positive: SSOT preserved in batch02; batch03 IDs covered without double-counting independent builds.
- Positive: CI contract prevents semantic regression.
- Negative: Four facade handlers maintained until catalog deduplication policy changes.
