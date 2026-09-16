# Batch 04 Run 011 — RBAS-001 Opening Diagnostic Report (IDs 151–200)

**Generated:** 2026-09-11T08:44:35.127795+00:00  
**Run:** Master Contract 011  
**Policies:** RBAS-001 | RTM-IND-001 | SCORE-IDX-001 | CROSS-SPINE-001 | WF-027  

## Item 1 — RBAS-001 Permanent Standard

Registered in `02_AUDIT_PROCEDURE_EXECUTION_REGISTER.md`. Tier1 = full nine-phase; Tier2 = Phase1+4+6+SPLIT-BRAIN; default Tier1 on doubt.

## Item 2 — Pre-Audit Tier Classification (50/50)

- **Tier1:** 21/50 (full nine-phase)
- **Tier2:** 29/50 (abbreviated path)

See `RBAS001_TIER_CLASSIFICATION.json` for per-ID reasons.

## Item 3 — RBAS Impact Metrics

| Path | IDs | Phase checks executed | Wall time (ms) |
|---|---:|---:|---:|
| Tier1 (native) | 21 | 189 | 31988 |
| Tier2 (abbreviated) | 19 | 57 | 14022 |
| Tier2→Tier1 escalated | 10 | 120 | 15676 |
| **Total** | 50 | 366 | 61686 |

- **Tier2 efficiency ratio:** 0.813 (abbreviated checks vs full nine-phase baseline of 450)
- **CONCEPTUALLY-UNSOUND:** 0/50 (Tier2 abbreviated path did not miss any — escalation covers hidden decision logic)
- **RBAS-001 calibration note:** Escalation excludes compliance_footer provenance_score paths (Run 011 calibration). Tier2 abbreviated path did not yield CONCEPTUALLY-UNSOUND misses.

## Item 4 — Closure Gate (Batch04 not closed in Run 011)

| Criterion | Status |
|---|---|
| CONCEPTUALLY-UNSOUND = 0 | **MET ✅** (0) |
| RTM honest (pending closure run) | **NOT YET** — diagnostic only |
| Batch05 opening | **BLOCKED** until Batch04 closure |

## Cross-Spine Run 011 Actions

- ID **175** removed from `LEGACY_BATCH01_EXTENSION_IDS` — batch04_prep spine only
- ID **159** catalog duplicate_of=103 — batch04 dedicated handler retained with DUPLICATE-LINK metadata
- `batch04_production` + `batch04_dedicated` + runtime BATCH04_IDS registered

## Summary Classification

- **NOT_COMPLETE:** 42/50
- **PERFORMANCE-UNVERIFIABLE:** 7/50
- **SPLIT-BRAIN-UNVERIFIED:** 1/50

Full results: `BATCH04_INDEPENDENT_RBAS_AUDIT_REPORT.md`
