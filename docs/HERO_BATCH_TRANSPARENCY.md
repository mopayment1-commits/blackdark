# Hero Batch Transparency Report

Generated as part of institutional scope alignment (owner-approved baseline).

## Does Hero Batch 01/02/03 exist?

| Hero track | Exists | Evidence / manifest |
|------------|--------|---------------------|
| Hero Batch 01 | Yes | `data/hero_batch_01_evidence.jsonl`, `scripts/generate_hero_batch_01.py` |
| Hero Batch 02 | Yes | `docs/HERO_BATCH_02_COMPLETION_REPORT.md`, `scripts/partial_batches/batch_02_101_200.json`, `data/hero_batch_02_101_200_evidence.jsonl` |
| Hero Batch 03 | No dedicated manifest found | — |

## ID ranges covered

| Hero track | Covers | Notes |
|------------|--------|-------|
| Hero Batch 01 | Mixed cherry-picked IDs (not sequential 1–50) | Documentation/audit track only |
| Hero Batch 02 | **IDs 101–200** | Manifest `batch_02_101_200.json` — overlaps official batch03 (101–150) and batch04 (151–200) |
| Hero Batch 03 | — | Not present |

## Relationship to official 826 batches

Hero batches are a **separate documentation and evidence track**. They are **not** official 826 batch closure:

- Official Batch 01 = IDs **1–50** only
- Official Batch 02 = IDs **51–100** only
- Official Batch 03 = IDs **101–150** only

Prior work that labeled cherry-picked IDs (e.g. 60, 103, 129, 175, 214, …, 646) as "batch 01" is **out of scope** for official Batch 01 closure. Those IDs are recorded in `docs/CAPABILITIES_826_INVENTORY.json` under their true `official_batch`.

## SPLIT-BRAIN policy

Hero audit classifications of `SPLIT-BRAIN-UNVERIFIED` (or similar) **must not** be converted to `PRODUCTION-ALIGNED` without:

1. Live production spine routing (`production_spine=batch01` or correct batch spine)
2. Goal-specific payload (non-generic `surface`)
3. Runtime without exception
4. Content matching the catalog capability name

## Mis-scoped batch02 work (101–150)

Technical implementation on branch `cursor/complete-826-batch02-e85e` targeted IDs **101–150** while official Batch 02 is **51–100**. That work is recorded as `PENDING_SCOPE_REALIGNMENT` / batch03-prep in the RTM until re-baselined.

## Commits referenced (full GitHub links)

- Initial mis-scoped batch02 spine: https://github.com/mopayment1-commits/blackdark/commit/b965b38
- Duplicate backend fixes (#106/#107/#110/#125): https://github.com/mopayment1-commits/blackdark/commit/ad813afcdae0270409193f64d316dbc9a779653b
- #69 cross-domain merge: https://github.com/mopayment1-commits/blackdark/commit/9746f8156c06f761e70aa979fe5cc508c5a49dc3
- Live payload audit docs: https://github.com/mopayment1-commits/blackdark/commit/53dcf5e257d0c9464ba9ba4cef9bccc95a21b98c
- Review #5 entitlement/OI notes: https://github.com/mopayment1-commits/blackdark/commit/8ce302b
