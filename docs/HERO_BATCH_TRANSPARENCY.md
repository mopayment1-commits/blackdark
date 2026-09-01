# Hero Batch Transparency Report

Generated as part of institutional scope alignment (owner-approved baseline).

## Critical distinction: Hero Batches ≠ Official 826 Batches

Two **independent numbering systems** exist in this repository. They must not be conflated.

| System | Batch 03 range | Purpose |
|--------|----------------|---------|
| **Hero Batches** (PR #343, merged 2026-08-31) | **201–300** | Documentation / quad-evidence / hero closure track |
| **Official 826 Batches** (owner mandate) | **101–150** | Sequential production closure for cap646 RTM |

## Does Hero Batch 01/02/03 exist?

| Hero track | Exists | ID range | Evidence |
|------------|--------|----------|----------|
| Hero Batch 01 | Yes | 100 hero-prioritized IDs (non-sequential) | `data/hero_batch_01_evidence.jsonl`, `scripts/generate_hero_batch_01.py` |
| Hero Batch 02 | Yes | **101–200** | `scripts/partial_batches/batch_02_101_200.json`, `data/hero_batch_02_101_200_evidence.jsonl`, `docs/HERO_BATCH_02_COMPLETION_REPORT.md` |
| Hero Batch 03 | **Yes** | **201–300** | `scripts/partial_batches/batch_03_201_300.json`, `data/hero_batch_03_201_300_evidence.jsonl`, `docs/HERO_BATCH_03_COMPLETION_REPORT.md` |
| Hero Batch 04 | Yes | 301–400 | `batch_04_301_400.json`, `docs/HERO_BATCH_04_COMPLETION_REPORT.md` |
| Hero Batch 05 | Yes | 401–500 | `batch_05_401_500.json`, `docs/HERO_BATCH_05_COMPLETION_REPORT.md` |
| Hero Batch 06 | Yes | 501–600 | `batch_06_501_600.json`, `docs/HERO_BATCH_06_COMPLETION_REPORT.md` |

Merged to `main` via **PR #343** (https://github.com/mopayment1-commits/blackdark/pull/343).

## Official 826 batch ranges (owner-approved)

| Official batch | ID range |
|----------------|----------|
| batch01 | 1–50 |
| batch02 | 51–100 |
| batch03 | 101–150 |
| batch04 | 151–200 |
| … | +50 per batch to 826 |

## Relationship to production spine

Hero batches are a **separate documentation and evidence track**. They are **not** official 826 batch closure unless each ID also passes:

1. Live `production_spine` routing on the correct official batch spine
2. Goal-specific payload (non-generic `surface`)
3. Runtime without exception
4. RTM status `PRODUCTION-ALIGNED` under `docs/CAPABILITIES_826_INVENTORY.json`

## SPLIT-BRAIN policy

Hero audit classifications of `SPLIT-BRAIN-UNVERIFIED` (or similar) **must not** be converted to `PRODUCTION-ALIGNED` without full 826 production proof above.

## Mis-scoped technical work (101–150)

Branch `cursor/complete-826-batch02-e85e` implemented `BATCH02_IDS = range(101,151)` — this aligns with **official batch03** (101–150), not official batch02 (51–100). Recorded as `PENDING_SCOPE_REALIGNMENT` in RTM.

## Legacy cherry-pick "batch01" (pre-official scope)

Prior `BATCH01_IDS` cherry-pick (50 IDs including 60, 103, …, 646) is preserved as `LEGACY_BATCH01_EXTENSION_IDS` for spine compatibility. These IDs are **not** official batch01 closure.

## Commits referenced

- Hero batches 01–06 merge: https://github.com/mopayment1-commits/blackdark/pull/343
- Official batch01 realignment: https://github.com/mopayment1-commits/blackdark/commit/29e258a
