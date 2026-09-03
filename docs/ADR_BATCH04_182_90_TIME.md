# ADR: Batch04 #182 ↔ Hero #90 — TIME Decision (Catalog Rename)

**Status:** Accepted — Option B implemented  
**Date:** 2026-09-03  
**Scope:** Batch04 ID 182

## Context

Hero function `white_label_infrastructure_status_182` declares `duplicate_of: [90, 140, 174]` and `merged_into: "institution_portal_90"`. Official cap646 **#90** is *Derivatives Market Sentiment Composite* (batch02, PRODUCTION-ALIGNED).

## Type-4 Contract (5 symbols)

Compared `execute_capability(182)` vs `execute_capability(90)` for BTC/ETH/SOL/AVAX/DOGE:

- **5/5 DIFFERENCE** on surface (`developer_activity_change_detection` vs `derivatives_market_sentiment_composite`)
- Hero `duplicate_of=90` refers to seed feature `institution_portal_90`, not cap646 #90

## TIME Decision

| Option | Verdict |
|--------|---------|
| A — Eliminate (Facade → cap646 #90) | **Rejected** — Type-4 proves semantic non-equivalence |
| B — Catalog rename | **Selected** — rename to **White-Label Infrastructure Status** |
| C — Invest (institution portal build) | Deferred under BUILD_PHASE_HOLD |

## Implementation

- Catalog only (same files as ADR-181-87)
- Runtime surface unchanged: `developer_activity_change_detection`
- No handler change (`_cap182` hero bridge retained)
