# Cap #56 Hero Binding — Authoritative Correction

**Date:** 2026-09-02  
**Issue:** Contradiction between OVERLAP_BATCH01 routing docs and pentagonal interface metadata.

## Authoritative answer

| Question | Answer |
|----------|--------|
| Is cap #56 bound to Single-Sentence Oracle? | **YES** — `HERO_ENGINES["Single-Sentence Oracle"]` includes capability_id **56** |
| Is cap #56 bound to Arbitrage Scanner? | **NO** |
| Production spine | **batch01** only: `cap646/batch01_production.py:cap_056` |
| OVERLAP_BATCH01 | Listed in official batch02 RTM (51–100) but `batch02_production.execute(56)` raises `ValueError`; runtime routes to batch01 |

## Wrong source (corrected)

| File | Wrong value | Correction |
|------|-------------|------------|
| `docs/PENTAGONAL_TEMPLATE_1_100.json` row #56 `interface.e2e_test` | `scripts/verify_official_batch02_production.py` | **batch01 spine** — use `scripts/verify_official_batch01_production.py` or cap646 GET probe |
| Informal reading of "batch02 RTM includes #56" | Implies independent batch02 handler | **OVERLAP_BATCH01** — batch01 extension only; see `docs/REUSED_LINK_TAXONOMY.json` → `OVERLAP_BATCH01.registered_ids.56` |

## Split-brain clarification

"Capability 56 split-brain" in `PRIOR_ISSUES` refers to **batch02 catalog listing vs batch01 execution spine** — NOT absence from Oracle hero binding. Oracle hero binding is correct and unchanged.

## Evidence

- `scripts/generate_pentagonal_hero_binding_report.py` HERO_ENGINES Oracle list includes 56
- `docs/HERO_SIX_BINDING_REPORT.json` feed_map: Oracle → cap 56 → `cap_056`
- `docs/DUPLICATION_LOCK_TABLE_1_100.json` row `#56 OVERLAP_BATCH01` → runtime→batch01_production
