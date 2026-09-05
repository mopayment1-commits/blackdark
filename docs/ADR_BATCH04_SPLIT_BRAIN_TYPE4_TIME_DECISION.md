# ADR: Batch04 SPLIT-BRAIN Type-4 — Gartner TIME Decision

**Status:** Accepted (BUILD_PHASE_HOLD)  
**Date:** 2026-09-03  
**Scope:** Batch04 IDs 151–200 — hero layer vs catalog-aligned batch04 spine  
**Evidence:** `docs/BATCH04_SPLIT_BRAIN_TYPE4_CONTRACT.json` · `tests/cap646/test_batch04_split_brain_type4_contract.py`  
**Related:** `docs/ADR_BATCH04_CANONICAL_BLOCKERS_103_130.md` · PR #363  
**Baseline commits:** `44f2ca2`, `0b72d81`

## Context

Type-4 behavioral contract compared **official batch04 spine** (`execute_capability` → `cap646.batch04_production`) against **bd_platform hero layer** (`hero_underlying` from RTM) for a representative sample:

| Dimension | Value |
|-----------|------:|
| Sample IDs | 10 (151, 153, 156, 159, 161, 177, 183, 189, 194, 200) |
| Symbols | 5 (BTC, ETH, SOL, AVAX, DOGE) |
| Total comparisons | 50 |
| MATCH (goal-equivalent) | **0** |
| DIFFERENCE | **50** |

**Root cause:** Hero layer reuses ID-number suffixes (`*_159`, `*_200`) with semantics that do not match catalog capability goals (`api_data_platform`, `token_circulation_intelligence`). This is architectural SPLIT-BRAIN, not accidental code duplication (Roy & Cordy Type-4 / CWE-1041).

ISO/IEC/IEEE 42010 requires an explicit architectural decision before any Migrate/Eliminate action. Gartner TIME framework mandates a recorded disposition per duplication class.

## Decision

**Default TIME disposition for all 50 batch04 IDs during BUILD_PHASE_HOLD: `Tolerate` (temporary).**

Rationale: Strangler Fig migration (Fowler) is in progress. Batch04 spine is the forward canonical path; hero layer remains read-only reference until per-ID or per-cluster Migrate decisions are made post-HOLD.

### Tolerate parameters

| Parameter | Value |
|-----------|-------|
| **Start** | 2026-09-03 (BUILD_PHASE_HOLD lock) |
| **End / review ceiling** | **2026-12-03** (90-day Tolerate window) |
| **Exit criteria** | Owner grants build approval AND at least one of: (a) batch-level Migrate ADR approved for a cluster, (b) per-ID Type-4 MATCH proven for promoted IDs, (c) explicit Eliminate ADR for retired hero paths |
| **Auto-escalation** | If Tolerate ceiling passes without exit criteria met → mandatory owner review; no automatic PRODUCTION-ALIGNED promotion |

## TIME disposition by group

### Group A — SPLIT-BRAIN Strangler stubs (40 IDs, Stub-Template)

**IDs:** 154–155, 157–158, 160, 163–174, 176–182, 184–188, 190–200 (excluding blockers/review IDs)

| TIME | Disposition | Justification |
|------|-------------|---------------|
| **Tolerate** | ✅ **Selected** | Generic catalog payload stubs exist on batch04 spine; hero layer retained for diagnostic reference during Strangler Fig |
| Invest | ❌ Rejected | No owner budget for parallel hero enhancement — would deepen SPLIT-BRAIN |
| Migrate | ⏳ Deferred | Requires catalog-faithful handler per ID post-HOLD; cannot execute under HOLD |
| Eliminate | ❌ Rejected | Premature — hero fns still referenced in inventory and gap reports; no ADR for retirement |

### Group B — Strangler Brownfield with hero delegation (7 IDs, CANDIDATE_REVIEW)

**IDs:** 151, 152, 153, 156, 161, 162, 189

| TIME | Disposition | Justification |
|------|-------------|---------------|
| **Tolerate** | ✅ **Selected** | Custom handlers wrap hero data in catalog surfaces; Type-4 still DIFFERENCE on semantic goal |
| Invest | ❌ Rejected | PA closure blocked under HOLD; invest without verification violates ISO 12207 |
| Migrate | ⏳ Deferred | First PA candidates after HOLD lift — Type-4 re-audit required before promotion |
| Eliminate | ❌ Rejected | These are the strongest Strangler candidates, not elimination targets |

### Group C — Owner blockers (2 IDs)

**IDs:** 159 (BLOCKER-159-103), 183 (BLOCKER-183-130)

| TIME | Disposition | Justification |
|------|-------------|---------------|
| **Tolerate** | ✅ **Selected** | Owner decisions locked: #159 suspended NOT_COMPLETE; #183 DISTINCT Option B |
| Invest | ❌ Rejected | Would reopen closed owner decisions |
| Migrate | ⏳ Deferred | #159 awaits #103 maturity (Tolerate ceiling **2026-10-03** per blocker ADR); #183 already DISTINCT |
| Eliminate | ❌ Rejected | Catalog entries are official batch04 scope |

### Group D — Batch01 overlap (1 ID)

**ID:** 175

| TIME | Disposition | Justification |
|------|-------------|---------------|
| **Tolerate** | ✅ **Selected** | OVERLAP-PARTIAL — canonical route is batch01; permanent exclusion from batch04_independent |
| Invest | ❌ Rejected | No batch04 investment — canonical exists |
| Migrate | ❌ Rejected | Would duplicate batch01 PRODUCTION-ALIGNED path |
| Eliminate | ❌ Rejected | Capability is live on batch01 spine |

### Group E — Type-4 sample DIFFERENCE (all 10 sampled IDs)

All 10 sampled IDs show **DIFFERENCE** across all 5 symbols. No cluster shows behavioral MATCH. Therefore **no Invest or Migrate promotion** is justified from Type-4 evidence alone.

## Consequences

1. Hero layer remains **non-canonical** for batch04 routing — `production_spine=batch04` is authoritative.
2. No REUSED-LINK promotion based on hero `feature_ref` ID suffix alone.
3. `pentagonal_domain_status=COMPLETE` means **local domain_rules probe pass only** — not PA, not PRR.
4. Next phase after HOLD lift: per-cluster Migrate ADRs with Type-4 re-audit (minimum 5 symbols per promoted ID).

## Compliance mapping

| Standard | Application |
|----------|-------------|
| ISO/IEC/IEEE 42010 | This ADR records the architectural SPLIT-BRAIN disposition |
| Gartner TIME | Tolerate default with 90-day ceiling and explicit exit criteria |
| Fowler Strangler Fig | Tolerate aligns with incremental migration — no Big Bang Eliminate |
| Roy & Cordy Type-4 | 50/50 DIFFERENCE proves semantic non-equivalence |
| Google SRE PRR | No production readiness claim until HOLD lifted and PRR executed |

## References

- `docs/BATCH04_SPLIT_BRAIN_TYPE4_CONTRACT.json`
- `docs/BATCH04_PREBUILD_CLASSIFICATION_151_200.json`
- `docs/ADR_BATCH04_CANONICAL_BLOCKERS_103_130.md`
- `docs/BATCH04_RTM_151_200.json` (`build_phase: BUILD_PHASE_HOLD`)
