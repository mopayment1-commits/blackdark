# CLOSURE-MANDATE-COMPLETION — تقرير البنود 1–10

**الفرع:** `cursor/closure-mandate-completion-e85e`  
**التاريخ:** 2026-09-01  
**الحالة:** `PENDING_CLOSURE` — بند 9 BLOCKED حتى اكتمال البنود 1–7 + إجراءات المالك (هـ)

## Summary Matrix (checksum ✓)

| فئة | العدد |
|-----|-------|
| Complete | 7 |
| AWAITING_OWNER_ACTION | 1 |
| BLOCKED / Sustained | 2 |
| **المجموع** | **10** |

`summary_matrix_checksum`: `row_count=10`, `status_entries=10`, `checksum_ok=true` — `docs/CLOSURE_MANDATE_COMPLETION_AUDIT.json`

---

### 1. تراجع التغطية 50.75% → 25.51%
**Complete** — **IEEE 1012: MEASUREMENT_SCOPE_REGRESSION، ليس Verification Regression على الكود**

| السؤال | الجواب | الدليل |
|--------|--------|--------|
| (أ) هل تغيّر `batch01_dedicated.py`؟ | **لا** — 461 stmt قبل وبعد MANDATE-FINAL | `coverage_regression_analysis` في audit |
| (ب) كود جديد بلا اختبار؟ | `dedicated_common.py` **+46 stmt** — مُغطّى **88.37%** | spine-suite |
| (ج) سبب انخفاض 91.5%→17.47%؟ | تشغيل pytest **بدون** `test_batch01_dedicated.py` | fast-only vs spine-suite |
| (د) بعد الإصلاح | `batch01_dedicated` **90.39%** (458 stmt) | `docs/SPINE_COVERAGE_SNAPSHOT.json` |

**جدول قبل/بعد (weighted spine):**

| السيناريو | weighted % | ملاحظة |
|-----------|------------|--------|
| fast-only (MANDATE-FINAL خطأ قياس) | 25.51% | لا batch01 tests |
| spine-suite (صحيح) | **44.47%** | يشمل batch01_dedicated 90.39% |
| batch01_dedicated وحده | 17.47% → **90.39%** | نفس الملف، اختلاف suite فقط |

اختبارات جديدة: `tests/cap646/test_dedicated_common.py`, `test_batch_spine.py`

---

### 2. #69 — حسم المسار وتأثير #110
**Complete**

| الخطوة | النتيجة |
|--------|---------|
| (أ) 5 رموز BTC/ETH/SOL/AVAX/DOGE | **ثابت** — `outputs_match: true` على كل الرموز |
| (ب) SSOT | **`cap646.batch02_production.cap_069`** — `production_spine: batch02` |
| (ج) Facade | `handlers/onchain.py#69` → `batch02_execute(69)` |
| (د) #110 LINK-ELIGIBLE | **مؤكَّد** — canonical #69 موثوق بعد الإصلاح؛ #110 يبقى prep فقط |

**الدليل:** `tests/cap646/test_cap69_dual_path.py` (6 tests PASS) · `docs/REUSED_LINK_TAXONOMY.json` → `canonical_ssot_path`

---

### 3. R0801 — العدد والمواقع
**Complete** — **0 انتهاكات** بعد Extract Function (كان 3)

| # | الموقع السابق | الحل |
|---|---------------|------|
| 1 | `batch02_dedicated:70-86` ↔ `batch03_dedicated:75-91` | `make_wrap_binding()` في `dedicated_common.py` |
| 2 | `verified:80-88` ↔ `institutional_controls:421-429` | `FIN_004_DEMO_OPPORTUNITY` في `net_edge_truth.py` |
| 3 | `batch02_dedicated:445-450` ↔ `batch03_dedicated:492-497` | `execute_dedicated_caps()` |

ADR: `docs/adr/ADR-003-batch-dedicated-bounded-context.md`

---

### 4. bandit — تفاصيل كاملة
**Complete** — `docs/BANDIT_CLOSURE_PATH_REPORT.json`

**cap646 (3 LOW):** B110/CWE-703 @ `entitlements.py:74,129,143` — ACCEPTED_RISK (fail-closed degradation)

**scripts closure-path (3 MEDIUM):** B310/B314 @ `complete_pdf_capabilities_826.py:124`, `run_spine_coverage_snapshot.py:47`, `wave_00_passive_security_scan.py:17`

---

### 5. batch01..batch17 ↔ IDs
**Complete** — `docs/BATCH_INTERNAL_ID_MAPPING.md` (17 صفًا)

---

### 6. تفاوت زمن gate-full 9–19 دقيقة
**Complete**

| التشغيل | الثواني | الدقائق |
|---------|---------|---------|
| نموذجي (هذه الجلسة) | 553–1102 | **9.2–18.4** |
| السبب | `institutional_closure_978()` يشغّل 978 قدرة + I/O شبكة | ليس اختلاف نطاق الفحص |
| worst-case مرجع CI | **~19 دقيقة** | موارد VM + cold caches |

`timing_ms.parallel_invariant_phase` في sample gate ≈ ثوانٍ؛ الجزء الأكبر = closure 978.

---

### 7. إعادة تحقق شاملة
**Complete**

| الفحص | النتيجة |
|-------|---------|
| (أ) `test_institutional_gate_full` | **EXIT:0** (~18 min هذه الجلسة) |
| (ب) jscpd official 1–100 spine | **0 clones** (بدون batch03 prep) |
| (ب) jscpd مع batch03 prep | 2 clones — مُبرَّر ADR-003 (bounded context) |
| (ج) checksum Summary | ✓ 10=10 |

---

### 8. AWAITING_OWNER_ACTION
**لا يُصنَّف Not Implemented:**

- `SONAR_TOKEN` → Sonar Quality Gate
- موافقة دمج PR #353 → main
- HMAC owner approval

---

### 9. شرط الإغلاق
**BLOCKED** — البنود 1–7 Complete؛ البنود الثلاثة في (8) + spine ≥80% + موافقة المالك.

---

### 10. Batch 03 محظور
**Sustained** — بدون تغيير.
