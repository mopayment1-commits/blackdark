# Batch03 Pending Work Audit — Section 3 (IDs 101–150)

**Audited at:** 2026-09-03  
**Baseline:** Batch01 + Batch02 **INSTITUTIONAL_CLOSED** per `docs/INSTITUTIONAL_CLOSURE_BATCH01_BATCH02.md`, `docs/BATCH02_OFFICIAL_RTM_51_100.json`, `docs/BATCH01_OFFICIAL_RTM_1_50.json`

---

## 0. Sequential baseline gate

**Batch01 وBatch02 مؤكَّدتان CLOSED** عبر:
- `docs/INSTITUTIONAL_CLOSURE_BATCH01_BATCH02.md` — `INSTITUTIONAL_CLOSED`, 100/100
- `docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json` — orchestrator 8/8
- `docs/BATCH02_OFFICIAL_RTM_51_100.json` — 50/50 PRODUCTION-ALIGNED
- لا استثناء مفتوح على الدفعتين 1–100

---

## 1. إعادة فحص 44 PRODUCTION-ALIGNED السابقة

العدد السابق (44) كان **مشتقًا** (50 − 4 REUSED − 2 overlap) وليس RTM رسميًا. بعد الفحص الحي (`scripts/audit_official_batch03_rtm.py`):

| الحالة | العدد | IDs |
|--------|------:|-----|
| PRODUCTION-ALIGNED (مستقل) | **44** | 101–102, 104–105, 108–109, 111–124, 126–128, 130–150 |
| OVERLAP-PARTIAL | **2** | 103, 129 |
| REUSED-LINK | **4** | 106, 107, 110, 125 |
| NOT_COMPLETE | **0** | — |

**حكم:** الـ44 مستقلة **مؤكَّدة** — `success=true`, `surface` مطابق, `production_spine=batch03`, لا generic handler.

---

## 2. MECE — #103 و #129

| ID | Goal | Spine | قرار MECE |
|----|------|-------|-----------|
| **103** | API Data Platform | batch01 (`cap646.batch01_production`) | **DISTINCT** من #129 — goal/surface مختلفان؛ تداخل spine فقط (OVERLAP-PARTIAL) |
| **129** | Sentiment Intelligence | batch01 | **DISTINCT** من #103 — لا DUPLICATE |

---

## 3. نزاع REUSED-LINK — Type-4 (#106, #107, #110, #125)

| Duplicate | Canonical | Canonical batch02 | Type-4 (5 symbols) | قرار |
|-----------|-----------|-------------------|-------------------|------|
| 106 | 63 | PRODUCTION-ALIGNED | PASS | **REUSED-LINK** |
| 107 | 64 | PRODUCTION-ALIGNED | PASS | **REUSED-LINK** |
| 110 | 69 | PRODUCTION-ALIGNED | PASS | **REUSED-LINK** |
| 125 | 85 | PRODUCTION-ALIGNED | PASS | **REUSED-LINK** |

دليل: `docs/BATCH03_DEDUP_AUDIT.json`, `tests/cap646/test_batch03_reused_link_contract.py`

**إصلاح:** رفع `catalog_link` إلى المستوى الأعلى في `cap646/dedicated_common.wrap()` — كان مدمجًا في payload فقط.

---

## 4. تحويل التصنيفات القديمة

| التصنيف القديم | التصنيف الرسمي الجديد |
|----------------|----------------------|
| PENDING_SCOPE_REALIGNMENT | PRODUCTION-ALIGNED / OVERLAP-PARTIAL / REUSED-LINK |
| SPLIT-BRAIN-UNVERIFIED | NOT_COMPLETE (لا يوجد في النطاق بعد الفحص) |
| VERIFIED_COMPLETE | **محظور** — غير مستخدم |
| batch03_prep spine | **batch03** (`cap646/batch03_production.py`) |

---

## 5. حظر REUSED-LINK — canonical readiness

| Canonical | Batch02 RTM | جاهز لـ REUSED-LINK |
|-----------|-------------|---------------------|
| #63 | PRODUCTION-ALIGNED | ✅ |
| #64 | PRODUCTION-ALIGNED | ✅ |
| #69 | PRODUCTION-ALIGNED | ✅ |
| #85 | PRODUCTION-ALIGNED | ✅ |

---

## 6. ملاحظة أمنية (GET entitlement)

#125 على مسار gateway: `entitlement_engine.check(125)` يسمح free بينما `runtime` يفحص canonical #85 (pro). **النتيجة:** free يحصل `success=false` + `teaser` — لا تسريب بيانات. يُوصى بمواءمة gateway مع `canonical_id()` في دفعة لاحقة (خارج نطاق 101–150).
