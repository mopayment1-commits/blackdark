# ADR: Batch04 Canonical Blockers — #103 and #130

**Status:** Accepted (BUILD_PHASE_HOLD)  
**Date:** 2026-09-03  
**Scope:** Batch04 IDs 159 and 183  
**Related:** `docs/BATCH04_DUPLICATION_DECISIONS.json`, `docs/BATCH04_RTM_151_200.json`, PR #363

## Context

Batch04 duplication analysis confirmed:

| Batch04 ID | Catalog goal | Candidate canonical | Canonical status (verified) |
|------------|--------------|---------------------|----------------------------|
| 159 | API Data Platform | #103 | `OVERLAP-PARTIAL` (batch01 spine, `cap_103`) |
| 183 | Whale Transaction Intelligence | #130 | `PRODUCTION-ALIGNED` (batch03, `_cap130`, Mindshare Intelligence) |

ISO/IEC 25010 appropriateness rule: no final `REUSED-LINK` or `PRODUCTION-ALIGNED` on #159/#183 until canonicals pass 25010 + behavioral Type-4 match.

Prior ADR errors corrected on disk:

- #103 was wrongly labeled `PENDING_SCOPE_REALIGNMENT` — true status is `OVERLAP-PARTIAL` per `docs/BATCH03_ACCEPTANCE_101_150.json`.
- #130 was wrongly labeled `PENDING_SCOPE_REALIGNMENT` — true status is `PRODUCTION-ALIGNED` in Batch03 (`mindshare_intelligence`, 5/5 domain rules).
- Evidence line "Neither canonical is PRODUCTION-ALIGNED" was incorrect — #130 **is** PRODUCTION-ALIGNED; #103 is OVERLAP-PARTIAL.

## Owner final decisions (2026-09-03)

### BLOCKER-159-103 — NOT_COMPLETE (suspended)

- **Decision:** Remains `NOT_COMPLETE`. No Option A (REUSED-LINK) and no Option B (DISTINCT ADR) at this time.
- **Gate:** Wait for #103 maturity (Tolerate ceiling **2026-10-03**) or a separate DISTINCT ADR later.
- **Rule:** No `REUSED-LINK` promotion before canonical readiness (official dictionary only).
- **Implementation:** Batch04 `_cap159` emits `api_data_platform` payload with `canonical_overlap=103`, `canonical_status=OVERLAP-PARTIAL`, `classification=NOT_COMPLETE`. No `catalog_link` REUSED-LINK stamp.

### BLOCKER-183-130 — DISTINCT-only (Option B approved)

- **Decision:** Option B approved — DISTINCT-only for #183. No final REUSED-LINK to #130.
- **Constraint:** #130 remains `PRODUCTION-ALIGNED` in Batch03 — **no changes** to Batch03 binding.
- **Implementation:** Batch04 `_cap183` emits dedicated `whale_transaction` payload. No `catalog_link` to #130.

### Revert policy

- **No revert** of post-`f9bfafb` build work (Strangler Fig diagnostic value). Reclassified as `BUILD_PHASE_HOLD`, not production closure.

## Consequences

- `batch04_independent` cannot increment via #159 or #183.
- Pentagonal generator records domain_rule pass/fail but forces `closure_status=NOT_COMPLETE` for both IDs.
- Progress to `LOCAL_GOVERNANCE_COMPLETE` for batch04 requires owner build approval after gaps 4–7 closed.

## Resolution paths (owner — historical reference)

| Blocker | Option A | Option B | Owner choice |
|---------|----------|----------|--------------|
| BLOCKER-159-103 | Complete batch03 PA closure for #103 + Type-4 match | DISTINCT #159 + ADR | **Suspended** — neither now |
| BLOCKER-183-130 | Realign #130 catalog + PA closure | DISTINCT-only #183 | **Option B approved** |

## Evidence

- Runtime probe #159: `surface=api_data_platform`, `production_spine=batch04`, `classification=NOT_COMPLETE`, `canonical_overlap=103`, `canonical_status=OVERLAP-PARTIAL`
- Runtime probe #183: `surface=whale_transaction_intelligence`, `whale_transaction.risk_score>=0`, `classification=NOT_COMPLETE`, no REUSED-LINK
- Runtime probe #103: `production_spine=batch01`, status `OVERLAP-PARTIAL`
- Runtime probe #130: `surface=mindshare_intelligence`, `production_spine=batch03`, status `PRODUCTION-ALIGNED`
- Type-4 SPLIT-BRAIN contract: `tests/cap646/test_batch04_split_brain_type4_contract.py` (10 IDs × 5 symbols)
