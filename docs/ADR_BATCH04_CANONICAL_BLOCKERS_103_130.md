# ADR: Batch04 Canonical Blockers — #103 and #130

**Status:** Accepted (build-phase hold)  
**Date:** 2026-09-03  
**Scope:** Batch04 IDs 159 and 183  
**Related:** `docs/BATCH04_DUPLICATION_DECISIONS.json`, PR #363

## Context

Batch04 duplication analysis confirmed:

| Batch04 ID | Catalog goal | Candidate canonical | Canonical status |
|------------|--------------|---------------------|------------------|
| 159 | API Data Platform | #103 | `PENDING_SCOPE_REALIGNMENT` (batch03_prep spine) |
| 183 | Whale Transaction Intelligence | #130 | `PENDING_SCOPE_REALIGNMENT` + semantic mismatch (catalog #130 = Mindshare Intelligence) |

ISO/IEC 25010 appropriateness rule: no final `REUSED-LINK` or `PRODUCTION-ALIGNED` on #159/#183 until canonicals pass 25010 + behavioral Type-4 match.

## Decision

1. **BLOCKER-159-103** remains active. #159 handler delegates to #103 institutional payload with `catalog_link` stamp only. Closure status stays `NOT_COMPLETE` + `PENDING_CANONICAL_AUDIT`.

2. **BLOCKER-183-130** remains active. #183 uses DISTINCT `whale_transaction` payload (not hero `transaction_risk_insight_130`). Closure status stays `NOT_COMPLETE` + `PENDING_CANONICAL_AUDIT`.

3. **No DISTINCT ADR for #159** at this time — owner must either complete batch03 canonical audit for #103 or author a separate DISTINCT ADR for #159.

4. **Semantic DISTINCT for #183** is already implemented in code; formal REUSED-LINK remains blocked until #130 audit or explicit owner ADR accepting DISTINCT-only path without canonical link promotion.

## Consequences

- `batch04_independent` cannot increment via #159 or #183.
- Pentagonal generator records domain_rule pass/fail but forces `closure_status=NOT_COMPLETE` for both IDs.
- Progress to `LOCAL_GOVERNANCE_COMPLETE` for batch04 requires resolution path below.

## Resolution paths (owner)

| Blocker | Option A | Option B |
|---------|----------|----------|
| BLOCKER-159-103 | Complete batch03 PA closure for #103 + Type-4 match | DISTINCT #159 implementation + ADR |
| BLOCKER-183-130 | Realign #130 catalog scope + PA closure + prove whale semantics | DISTINCT-only #183 + ADR removing REUSED-LINK intent |

## Evidence

- Runtime probe: #159 returns `catalog_link.duplicate_of=103`, `api_data_platform.institutional_api=/api/institutional`
- Runtime probe: #183 returns `whale_transaction.risk_score>=0`, `catalog_link.duplicate_of=130`
- Neither canonical is PRODUCTION-ALIGNED at commit baseline `d83bbb1`+
