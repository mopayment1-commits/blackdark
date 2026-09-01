# CAPABILITIES 826 — Institutional Inventory

Generated: 2026-09-01T09:28:24.531867+00:00

## Summary

| Metric | Count |
|--------|------:|
| Total scope | 826 |
| PRODUCTION-ALIGNED | 96 |

## Classification breakdown

| Classification | Count |
|----------------|------:|
| DEFERRED/TEMPLATE-STUB | 307 |
| NOT_IN_HERO_AUDIT | 248 |
| SPLIT-BRAIN-UNVERIFIED | 127 |
| PRODUCTION-ALIGNED | 96 |
| DEFERRED-EARLY-BATCH | 36 |
| EXTENSION-PENDING-CAP646 | 6 |
| REUSED-LINK | 4 |
| OVERLAP_BATCH01 | 2 |

## REUSED-LINK (official category)

Catalog-registered duplicate/alias of a canonical capability ID; entry point may differ but goal is the same documented capability.

**Acceptance criteria:**
- docs/cap646/CAP646_GAP_MATRIX.json marks final_classification DUPLICATE/ALREADY_COVERED with canonical ID
- AND/OR cap646/catalog.py REPEAT_CANONICAL maps identical capability name to canonical ID
- Live payload achieves the shared catalog goal (not merely spine routing)
- Does not count as an independent new completion in batch closure totals
