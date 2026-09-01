# Batch 02 — Honest Closure Audit (mandatory review)

**Date:** 2026-09-01  
**Scope:** IDs 101–150  
**Verdict:** **NOT 50/50 independent PRODUCTION-ALIGNED** — see breakdown below.

---

## 1) Catalog duplicates in Batch 02 scope

| Requested | Canonical | Catalog goal (both) | Same payload as canonical? | Matches #requested goal? | Classification |
|-----------|-----------|---------------------|----------------------------|--------------------------|----------------|
| **106** | 63 | Data Quality & Provenance Layer | **No** — batch02: `compute_contagion_vector_106`; canonical 63: `hot_storage` via verified handler | **No** — contagion risk map ≠ provenance/DQP | **NOT_COMPLETE** |
| **107** | 64 | Metric Methodology Registry | **No** — batch02: `whale_retail_ratio`; canonical 64: `signal_registry` stats | **No** — whale/retail ratio ≠ methodology registry | **NOT_COMPLETE** |
| **110** | 69 | Cross-Domain Decision Intelligence Layer | **No** — batch02: `cross_domain_decision` + whale extensions; canonical 69: generic `onchain_intelligence` | **Partial** — batch02 payload closer to goal than canonical | **REUSED-LINK** (catalog `DUPLICATE/ALREADY_COVERED`; not independent) |
| **125** | 85 | Futures Open Interest Intelligence | **No** — batch02: `custody_tracking_status_125` (deferred); canonical 85: `derivatives_overview` OI fields | **No** — custody status ≠ open interest | **NOT_COMPLETE** |

Gap matrix: all four are `DUPLICATE/ALREADY_COVERED` pointing at 63/64/69/85.

**Institutional rule applied:** None of the four returns the canonical-only result. Three fail goal appropriateness (#106, #107, #125). #110 is catalog-duplicate (REUSED-LINK) despite a distinct batch02 payload.

---

## 2) Batch 01 overlap (#103, #129)

| ID | Goal | Batch 01? | Runtime spine on live call | Batch02 dedicated exists? |
|----|------|-----------|----------------------------|---------------------------|
| **103** | API Data Platform | Yes (`BATCH01_IDS`) | `batch01` → `cap646.batch01_production` | Yes (`_cap103`) but **never reached** — batch01 wins first |
| **129** | Sentiment Intelligence | Yes (`BATCH01_IDS`) | `batch01` → market sentiment handler | Yes (`_cap129`) but **never reached** |

**Conclusion:** Both were completed in Batch 01. Batch 02 only **re-lists** them in manifest; live path is **batch01 re-invocation**, not new batch02 backend work.

---

## 3) Honest closure numbers

| Bucket | Count | IDs |
|--------|------:|-----|
| **New PRODUCTION-ALIGNED (batch02 spine, non-duplicate, non-overlap)** | **44** | 101–105, 108–109, 111–124, 126–128, 130–150 |
| **Batch 01 overlap (re-verified, not new completion)** | **2** | 103, 129 |
| **REUSED-LINK / catalog duplicate (distinct payload, not independent)** | **1** | 110 |
| **NOT_COMPLETE (inappropriate payload vs catalog goal)** | **3** | 106, 107, 125 |
| **Total in scope** | **50** | 101–150 |

**Rejected claim:** “50/50 PRODUCTION-ALIGNED as 50 new independent completions.”

**Accepted claim:** “48 IDs execute batch02 spine; 44 are institutionally aligned as new independent capabilities; 4 duplicates need reclassification; 2 are batch01 overlap only.”

---

## 4) Required remediation before Batch 02 closure

1. **#106** — wire DQP/provenance backend (align with #63 canonical intent or document explicit catalog exception).
2. **#107** — wire methodology registry backend (signal_registry / canonical #64 path).
3. **#125** — wire futures OI backend (derivatives_hub / canonical #85 path).
4. **#110** — either explicit catalog decision to treat as independent, or formal REUSED-LINK documentation (no double-count).
5. **#103, #129** — remove from “new completion” count; keep as overlap re-verification only.

---

## 5) Tests

`pytest -m "not slow"` — **2484 passed, 0 failed** (unchanged; classification is audit-only until backends fixed).
