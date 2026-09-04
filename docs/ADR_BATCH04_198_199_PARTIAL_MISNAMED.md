# ADR — Batch04 #198/#199 PARTIAL_MISNAMED (TIME: Tolerate)

**Date:** 2026-09-04  
**Status:** Accepted  
**Decision:** Catalog rename + local heuristic proxy (no Glassnode subscription)

## Context

- **#198** catalog claimed "Age Consumed / Dormancy Intelligence" (Glassnode-exclusive).
- **#199** catalog claimed "Mean Dollar Invested Age" (Glassnode MDIA).
- Hero bridge wired research PDF ingestion — semantic MISWIRE.

## Decision (Gartner TIME: **Tolerate**)

| ID | New catalog name | Surface (unchanged) | Proxy source |
|----|------------------|---------------------|--------------|
| #198 | On-Chain Dormancy Proxy | `age_consumed_dormancy_intelligence` | `onchain_advanced` hodl_waves + SOPR heuristic |
| #199 | Invested-Age Proxy | `mean_dollar_invested_age` | `onchain_advanced` MVRV/realized age heuristic |

## Consequences

- `accuracy_disclaimer` required on every response.
- `closure_status=PRODUCTION-ALIGNED` with `metric_type=PARTIAL_MISNAMED`.
- Not comparable to Glassnode commercial metrics.
- Eliminate deferred unless owner funds Glassnode tier.
