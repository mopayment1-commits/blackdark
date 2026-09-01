# Batch 02 — Honest Closure Audit (post-decomposition)

**Date:** 2026-09-01  
**Scope:** IDs 101–150  
**Verdict:** **NOT CLOSED** — honest count: **44 new PRODUCTION-ALIGNED + 2 overlap + 4 REUSED-LINK + 0 NOT_COMPLETE**

---

## 1) Catalog duplicates — per-ID decomposition

Institutional rule: classification by **actual goal achievement** for the requested ID, not spine routing alone. Catalog duplicates (`REPEAT_CANONICAL` + gap matrix `DUPLICATE/ALREADY_COVERED`) are **REUSED-LINK**, not independent new completions.

### #106 → canonical #63

| Field | Value |
|-------|-------|
| **(a) Original ID goal** | **Data Quality & Provenance Layer** — score/lineage/provenance for data inputs |
| **(b) Canonical #63 goal** | Same: **Data Quality & Provenance Layer** |
| **(c) Post batch02 spine** | **Matches original ID goal** — `compute_data_provenance_score` + `hot_storage`; surface `data_quality_provenance_layer` |
| **(d) Classification** | **REUSED-LINK** — catalog explicitly marks duplicate of #63; not an independent new completion |

### #107 → canonical #64

| Field | Value |
|-------|-------|
| **(a) Original ID goal** | **Metric Methodology Registry** — registry stats for signal/metric methodology |
| **(b) Canonical #64 goal** | Same: **Metric Methodology Registry** |
| **(c) Post batch02 spine** | **Matches original ID goal** — `signal_registry.registry_stats()`; surface `metric_methodology_registry` |
| **(d) Classification** | **REUSED-LINK** — catalog duplicate of #64 |

### #110 → canonical #69

| Field | Value |
|-------|-------|
| **(a) Original ID goal** | **Cross-Domain Decision Intelligence Layer** — multi-dimensional + cross-market decision synthesis |
| **(b) Canonical #69 goal** | Same catalog name; canonical handler returns generic `onchain_intelligence` (weaker) |
| **(c) Post batch02 spine** | **Matches original ID goal** — `build_multi_dim_analysis_73` + `cross_market_decision_intelligence_567`; surface `cross_domain_decision_intelligence_layer` |
| **(d) Classification** | **REUSED-LINK** — catalog duplicate of #69; batch02 spine is alias entry point, not independent capability |

### #125 → canonical #85

| Field | Value |
|-------|-------|
| **(a) Original ID goal** | **Futures Open Interest Intelligence** — OI contracts/USD from derivatives feed |
| **(b) Canonical #85 goal** | Same: **Futures Open Interest Intelligence** |
| **(c) Post batch02 spine** | **Matches original ID goal** — `derivatives_overview` with `open_interest_usd` / `open_interest_contracts`; surface `futures_open_interest_intelligence` |
| **(d) Classification** | **REUSED-LINK** — catalog duplicate of #85 |

**Note:** Passing through batch02 spine does **not** make these PRODUCTION-ALIGNED as new independent completions.

---

## 2) Overlap with Batch 01 — #103, #129

| ID | Catalog goal | Completed in Batch 01? | Batch 02 backend | Classification |
|----|--------------|------------------------|------------------|----------------|
| **103** | API Data Platform | **Yes** (`BATCH01_IDS`) | **No new backend** — runtime uses `batch01` spine (`cap646.batch01_production`) | **OVERLAP_BATCH01** — not counted in 44 new |
| **129** | Sentiment Intelligence | **Yes** (`BATCH01_IDS`) | **No new backend** — runtime uses `batch01` spine | **OVERLAP_BATCH01** — not counted in 44 new |

`batch02_dedicated._cap103` / `_cap129` exist in code but are **dead code** at runtime (batch01 wins first in `runtime.py`).

---

## 3) Honest closure numbers

| Bucket | Count | IDs |
|--------|------:|-----|
| **New PRODUCTION-ALIGNED** | **44** | 101–102, 104–105, 108–109, 111–124, 126–128, 130–150 |
| **Overlap with Batch 01** | **2** | 103, 129 |
| **REUSED-LINK / catalog alias** | **4** | 106, 107, 110, 125 |
| **NOT_COMPLETE** | **0** | — |
| **Total in scope** | **50** | 101–150 |

**Rejected:** “50/50 PRODUCTION-ALIGNED as 50 new independent completions.”  
**Accepted:** “44 new + 2 overlap re-verification + 4 catalog aliases = 50 scoped IDs.”

Machine-readable: `docs/BATCH02_CLASSIFICATION.json`

---

## 4) Tests

`pytest -m "not slow"` — run after classification/back-end fixes; must be **0 failed**.
