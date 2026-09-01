# Batch 02 — Honest Closure Audit (mandatory review #2)

**Date:** 2026-09-01  
**Scope:** IDs 101–150  
**Status:** **NOT CLOSED**  
**Batch 03:** **BLOCKED**

---

## 0) Critical contradiction resolved — #106, #107, #125

### Was code modified between Report #1 and Report #2?

**Yes.** Report #1 (`e091f5f`, docs-only) described live behavior **before** backend fixes. Report #2 (`ad813af`) applied code changes **after** that audit.

| ID | Report #1 (pre-fix, accurate at `e091f5f`) | Report #2 (post-fix, accurate at `ad813af`) |
|----|---------------------------------------------|-----------------------------------------------|
| **106** | `compute_contagion_vector_106` — wrong goal | `compute_data_provenance_score` + `hot_storage` |
| **107** | `compute_whale_retail_ratio_107` — wrong goal | `signal_registry.registry_stats()` |
| **125** | `custody_tracking_status_125` — wrong goal | `derivatives_overview` OI fields |

**Commit:** `ad813afcdae0270409193f64d316dbc9a779653b`  
**File:** `cap646/batch02_dedicated.py`

```diff
#106: compute_contagion_vector_106 → compute_data_provenance_score + hot_storage
#107: compute_whale_retail_ratio_107 → signal_registry.registry_stats()
#125: custody_tracking_status_125 → derivatives_overview (OI fields)
```

**Which report was inaccurate?** Report #1 was accurate **for code at that moment** but stated remediation was pending. Report #2 described **post-fix** behavior without always repeating that a code commit (`ad813af`) intervened — that sequencing gap caused the apparent contradiction.

**Current live state (verified 2026-09-01):** all three return goal-aligned payloads via batch02 spine.

---

## 1) REUSED-LINK — catalog evidence per pair

Institutional basis requires **both** gap-matrix duplicate marking **and** identical capability name in catalog / `REPEAT_CANONICAL`.

### #106 → #63

| Source | Evidence |
|--------|----------|
| `cap646/catalog.py` L14–L15 | `"Data Quality & Provenance Layer": 63` |
| `docs/cap646/CAP646_CATALOG.json` L437–441 / L738–742 | #63 and #106 share capability name **"Data Quality & Provenance Layer"** |
| `docs/cap646/CAP646_GAP_MATRIX.json` L1720–1736 | `"final_classification": "DUPLICATE/ALREADY_COVERED"`, `"reason": "Duplicate of ID63 \`Data Quality & Provenance Layer\`"` |

**Post-spine:** matches original goal → **REUSED-LINK** (not independent PRODUCTION-ALIGNED)

### #107 → #64

| Source | Evidence |
|--------|----------|
| `cap646/catalog.py` L16 | `"Metric Methodology Registry": 64` |
| `docs/cap646/CAP646_CATALOG.json` L444–448 / L745–749 | identical capability name |
| `docs/cap646/CAP646_GAP_MATRIX.json` L1739–1754 | `"DUPLICATE/ALREADY_COVERED"`, `"reason": "Duplicate of ID64: ID64 signal_registry canonical registry"` |

**Post-spine:** matches original goal → **REUSED-LINK**

### #110 → #69

| Source | Evidence |
|--------|----------|
| `cap646/catalog.py` L17 | `"Cross-Domain Decision Intelligence Layer": 69` |
| `docs/cap646/CAP646_CATALOG.json` L479–483 / L766–770 | identical capability name |
| `docs/cap646/CAP646_GAP_MATRIX.json` L1785–1802 | `"DUPLICATE/ALREADY_COVERED"`, `"reason": "Duplicate of ID69: ID69/251 ai_oracle + trust_pulse + decision_certificate"` |

**Decision (mandatory #110):** **Option (a) — merge into canonical #69**

- Shared module: `cap646/cross_domain_decision.py`
- Canonical handler updated: `cap646/handlers/onchain.py` — #69 now returns `surface=cross_domain_decision_intelligence_layer` (not `onchain_intelligence`)
- #110 batch02 entry remains REUSED-LINK alias using same shared builder
- Live proof: `test_canonical_69_cross_domain_not_generic_onchain` in `tests/cap646/test_batch02_dedicated.py`

### #125 → #85

| Source | Evidence |
|--------|----------|
| `cap646/catalog.py` L24 | `"Futures Open Interest Intelligence": 85` |
| `docs/cap646/CAP646_CATALOG.json` L591–595 / L871–875 | identical capability name |
| `docs/cap646/CAP646_GAP_MATRIX.json` L2006–2019 | `"DUPLICATE/ALREADY_COVERED"`, `"reason": "Duplicate of ID85 \`Futures Open Interest Intelligence\`"` |

**Post-spine:** matches original goal → **REUSED-LINK**

---

## 2) Overlap — #103, #129

| ID | Batch 01 complete? | Batch 02 backend | Live `production_spine` |
|----|-------------------|------------------|-------------------------|
| **103** | Yes | **Removed** — reserved overlap | `batch01` |
| **129** | Yes | **Removed** — reserved overlap | `batch01` |

**Decision:** dead `_cap103` / `_cap129` **deleted**. `BATCH02_OVERLAP_BATCH01_IDS` documents reservation; `batch02_dedicated.execute(103|129)` raises `ValueError` directing to batch01 spine.

**Not counted** in 44 new PRODUCTION-ALIGNED.

---

## 3) Honest closure numbers (live-verified)

| Bucket | Count | IDs |
|--------|------:|-----|
| **New PRODUCTION-ALIGNED** | **44** | 101–102, 104–105, 108–109, 111–124, 126–128, 130–150 |
| **Overlap Batch 01** | **2** | 103, 129 |
| **REUSED-LINK** | **4** | 106, 107, 110, 125 |
| **NOT_COMPLETE** | **0** | — |
| **Total in scope** | **50** | 101–150 |

---

## 4) REUSED-LINK official category

Defined in `docs/CAPABILITIES_826_INVENTORY.json` → `classification_taxonomy.REUSED-LINK` (generated by `scripts/generate_capabilities_826_inventory.py`).

---

## 5) Tests

`pytest -m "not slow"` — **0 failed** (run after this commit).

---

## 6) STOP

Batch 02 **NOT CLOSED**. Batch 03 **BLOCKED** until explicit approval.
