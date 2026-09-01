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

## 6) الحالة الحية — #106 / #107 / #125 (post-`ad813af`, verified 2026-09-01T08:53Z)

Command: `execute_capability(id, skip_entitlement=True, params={"symbol":"BTC"})`

### #106 — Data Quality & Provenance Layer

| Field | Live value |
|-------|------------|
| `surface` | `data_quality_provenance_layer` |
| `production_spine` | `batch02` |
| `backend` | `cap646.batch02_production.cap_106` |
| `data_quality_provenance.provenance.score` | **66.0** |
| `provenance.band` | `caution` |
| `provenance.posture` | `Decide with caution — some inputs soft or thin` |
| `provenance.components.freshness` | `{score: 18.0, state: "unknown", freshness_ms: null}` |
| `provenance.components.venue_depth` | `{score: 35.0, live_venues: 100}` |
| `provenance.components.source_diversity` | `{score: 11.0, categories: ["derivatives","prices"]}` |
| `provenance.components.executable_gate` | `{score: 2.0, executable: false}` |
| `provenance.api` | `/api/oracle/provenance-score` |
| `hot_storage` | `{enqueued:0, dropped:0, flushed:0, buffer_depth:0, active_backends:[]}` |
| `catalog_link` | `{duplicate_of: 63, classification: "REUSED-LINK"}` |

**Goal check:** DQP score + tiered storage stats — **not** contagion vector.

### #107 — Metric Methodology Registry

| Field | Live value |
|-------|------------|
| `surface` | `metric_methodology_registry` |
| `production_spine` | `batch02` |
| `backend` | `cap646.batch02_production.cap_107` |
| `methodology_registry.total_in_memory` | **2000** |
| `methodology_registry.labeled` | **1903** |
| `methodology_registry.unlabeled` | **97** |
| `methodology_registry.linked_prediction_ids` | **1567** |
| `methodology_registry.by_type` | `spot_futures:223, unified_live:1421, cross_exchange:204, oracle_direction:99, market_replay:48, oracle_api:5` |
| `methodology_registry.lexicon` (sample keys) | `oracle_direction, oracle_decision, cross_exchange, triangular, spot_futures, funding, arbitrage, whale_transfer` |
| `catalog_link` | `{duplicate_of: 64, classification: "REUSED-LINK"}` |

**Goal check:** signal registry methodology stats + lexicon — **not** whale/retail ratio.

### #125 — Futures Open Interest Intelligence

| Field | Live value |
|-------|------------|
| `surface` | `futures_open_interest_intelligence` |
| `production_spine` | `batch02` |
| `backend` | `cap646.batch02_production.cap_125` |
| `open_interest_usd` | **0** |
| `open_interest_contracts` | **0.0** |
| `free_tier.source` | `binance_futures_public` |
| `free_tier.symbol` | `BTCUSDT` |
| `free_tier.available` | **false** (Binance futures OI feed unavailable in this env) |
| `free_tier.funding_rate_pct` | `0.0` |
| `catalog_link` | `{duplicate_of: 85, classification: "REUSED-LINK"}` |

**Goal check:** derivatives OI structure/surface — **not** custody tracking. **Caveat:** OI numeric fields are zero/`available:false` in live env (feed limitation), not a wrong-handler issue.

---

## 7) #69 — تعديل خارج نطاق الدفعات المعلنة

| Question | Answer |
|----------|--------|
| **نطاق الدفعات** | #69 ∉ Batch01 (1–59) و ∉ Batch02 (101–150) |
| **التصنيف الحالي في `CAPABILITIES_826_INVENTORY.json`** | **`SPLIT-BRAIN-UNVERIFIED`** — `backend: ai_oracle.evaluate_opportunity` (inventory **not yet updated** for onchain handler merge) |
| **هل تُحسب ضمن إغلاق Batch02؟** | **لا** — ليست من الـ44 ولا الـ4 REUSED-LINK ولا overlap |
| **القرار المؤسسي** | **تحتاج دورة اعتماد مستقلة** قبل اعتبار تعديل #69 نهائيًا: (1) عيّنة محتوى حي موثّقة لـ#69 post-merge، (2) تحديث inventory binding/classification، (3) موافقة صريحة منفصلة عن إغلاق Batch02 |
| **التبرير داخل PR Batch02** | دمج #110→#69 كان **أثرًا جانبيًا إلزاميًا** لقرار REUSED-LINK (#110) — لا يُوسَّع به نطاق Batch02 ولا يُغلق #69 ضمنها |

**Live #69 post-merge (reference):** `surface=cross_domain_decision_intelligence_layer`, `backend_module=cap646.handlers.onchain`, `composite_score=5.0`, `multi_dimensional.ok=true`

---

## 8) `scripts/verify_batch02_production.py` — post-`9746f81`

```
{
  "all_verified": true,
  "count": 50
}
Wrote /workspace/docs/BATCH02_PRODUCTION_PROOF.json
```

`verified_at`: **2026-09-01T08:53:26.174330+00:00**  
`overlap_batch01_ids`: `[103, 129]`  
Per-ID proofs for #106/#107/#125: `option_a_verified: true`, surfaces match expected.

**Limitation (explicit):** verify script checks surface/path/success — **not** institutional REUSED-LINK vs independent classification. Honest closure still **44 + 2 + 4**, not 50 independent.

---

## 9) STOP

Batch 02 **NOT CLOSED**. Batch 03 **BLOCKED**. #69 merge **PENDING independent sign-off**.

