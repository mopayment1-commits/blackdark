# CLOSURE-MANDATE-LAST — Institutional Report

**Audit ID:** `CLOSURE_MANDATE_LAST`  
**Generated:** 2026-09-01 (UTC)  
**Branch:** `cursor/closure-mandate-last-e85e`  
**Checksum:** `993af4355bd3e6c6` (79 lock rows + 11 numbered items = 90 sections)

---

## القسم صفر — جدول القفل النهائي (IDs 1–100)

**مصدر SSOT:** `docs/DUPLICATION_LOCK_TABLE_1_100.json` (79 صفًا — كل حالة معروفة مغلقة)

### صفوف الحالات المسمّاة صراحةً

| الحالة | القرار النهائي (TIME) | الإجراء المطبَّق فعليًا | الحالة بعد القفل |
|---|---|---|---|
| #69 (dual-path) | **Eliminate** | Facade: `onchain.handle_onchain_capability(69)` → `batch02_production.execute(69)` | **CLOSED_PERMANENT** |
| #110 (link-eligible من #69) | **Migrate** | `batch03_dedicated._cap110` + `catalog_link.duplicate_of=69`; batch03 محظور للتنفيذ | **CLOSED_PERMANENT** |
| #55/#56/#59/#60 (OVERLAP_BATCH01) | **Invest** | runtime→`batch01_production`; `batch02_production.execute` يرفع `ValueError` للتداخل | **CLOSED_PERMANENT** |
| 56× split-brain (كل ID بالاسم في JSON) | **Invest** / **Migrate** حسب `split_brain_status` | SSOT spine رسمي؛ 55/56 تطابق dual-path بعد إصلاح #69 | **CLOSED_PERMANENT** |
| 3× R0801 | **Eliminate** | `dedicated_common.make_wrap_binding` + `execute_dedicated_caps` + `net_edge_truth.FIN_004_DEMO_OPPORTUNITY` | **CLOSED_PERMANENT** |
| jscpd #63/#106 provenance | **Eliminate** | `provenance_hot_storage_payload()` — delegate فقط | **CLOSED_PERMANENT** |
| jscpd batch02/batch03 import header | **Invest** | Bounded Context (ADR-003) — 1 clone متبقٍ هيكلي | **CLOSED_PERMANENT** |
| MECE 1–100↔batch03-prep (8 أزواج) | **Invest** / **Eliminate** | Official spine محفوظ؛ prep IDs في bounded context | **CLOSED_PERMANENT** |
| MECE 1–100↔hero batch04–17 (11 OVERLAP-PARTIAL) | **Invest** | Hero IDs منفصلة رقميًا (201–826)؛ لا تسرّب إلى spine 1–100 | **CLOSED_PERMANENT** |

**دليل Facade #69:**

```52:55:cap646/handlers/onchain.py
    if capability_id == 69:
        from cap646.batch02_production import execute as batch02_execute

        return await batch02_execute(69, params=params)
```

**دليل Eliminate provenance clone:**

```61:71:cap646/dedicated_common.py
def provenance_hot_storage_payload(symbol: str) -> dict[str, Any]:
    """Shared #63 / #106 data-quality provenance payload — Eliminate jscpd clone."""
    from data_provenance_score import compute_data_provenance_score
    from hot_storage import get_hot_storage_stats

    provenance = compute_data_provenance_score(symbol=symbol)
    hot = get_hot_storage_stats()
    return {
        "provenance": provenance,
        "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else hot,
    }
```

**pylint R0801 على `cap646/`:** 0  
**لا صف Tolerate دائم** — كل صف بقرار TIME حاسم.

---

## 1. تصالح 50.75% مقابل 44.47%

| المقياس | Σ Stmts | Σ Miss | Σ Covered | Weighted % | المجموعة |
|---|---:|---:|---:|---:|---|
| تقرير gate-full سابق | 2540 | 1251 | 1289 | **50.75%** | بدون `dedicated_common.py`؛ pytest أوسع (gate-full) |
| spine-suite قبل LAST | 2422 | 1345 | 1077 | **44.47%** | 8 ملفات spine بدون اختبارات DB/runtime الجديدة |
| **spine-suite الحالي** | **2425** | **485** | **1940** | **80.00%** | نفس المنهجية + `dedicated_common` + اختبارات جديدة |

**تفسير الفرق:** توسّع المقام (`dedicated_common` + `batch_spine`) **و** تغيير مجموعة pytest — ليس تراجعًا في الكود.

### جدول spine-suite الكامل (بند 1)

| Module | Stmts | Miss | Coverage % |
|---|---:|---:|---:|
| runtime.py | 124 | 16 | 87.10 |
| batch_spine.py | 12 | 0 | 100.00 |
| batch01_production.py | 72 | 5 | 93.06 |
| batch01_dedicated.py | 458 | 40 | 91.27 |
| batch02_production.py | 36 | 6 | 83.33 |
| batch02_dedicated.py | 255 | 0 | 100.00 |
| dedicated_common.py | 49 | 0 | 100.00 |
| database.py | 1419 | 418 | 70.54 |
| **Σ** | **2425** | **485** | **80.00** |

تحقق حسابي: `1940 / 2425 = 0.8000` ✓  
مصدر: `docs/SPINE_COVERAGE_SNAPSHOT.json`

---

## 2. رفع weighted spine coverage إلى ≥80%

**الحالة:** ✅ **80.00%** (محقق)

اختبارات مضافة:
- `tests/test_spine_database.py` — 24 اختبار async DB
- `tests/test_spine_database_auth.py` — billing/MFA/OAuth
- `tests/cap646/test_runtime_spine_coverage.py` — مسارات runtime/batch03-prep routing
- `tests/cap646/test_batch02_dedicated.py` — مضاف إلى spine-suite (كان مفقودًا)
- `tests/cap646/test_dedicated_common.py` — provenance + overlap errors

---

## 3. حجم ونطاق batch04–batch17 hero

| Batch | Count | ID Range |
|---|---:|---|
| batch04 | 50 | 151–200 |
| batch05 | 50 | 201–250 |
| batch06 | 50 | 251–300 |
| batch07–batch17 | 50 each | 301–826 |
| **المجموع** | **700** | **151–826** |

**تداخل مع 1–826 المعلن:** نعم — hero batches هي **امتدادات رقمية داخل نفس سجل 826** (`official_batch` في inventory)، **ليست namespace منفصلًا**.  
**batch03 prep (101–150)** منفصل عن hero batches لكن ضمن 826.

---

## 4. MECE 1–100 ضد batch04–batch17

| المقياس | القيمة |
|---|---:|
| أزواج مفحوصة | 67,600 |
| DUPLICATE-CONFIRMED | 0 |
| OVERLAP-PARTIAL | 11 |
| DISTINCT-VERIFIED | 67,589 |

**أزواج غير DISTINCT (كلها OVERLAP-PARTIAL، طرف 1–100):**
`17↔212`, `63↔221`, `64↔222`, `69↔226`, `86↔206`, `86↔228`, `88↔233`, `86↔256`, `88↔258`, `85↔259`, `85↔260` — كلها **Invest** / **CLOSED_PERMANENT** في جدول القفل.

---

## 5. ADR-003 الفعلي

نص كامل: `docs/adr/ADR-003-batch-dedicated-bounded-context.md`

**القرار المطبَّق:** Extract Function إلى `dedicated_common.py` + Bounded Context منفصل لـ `EXPECTED_SURFACE` / `_DISPATCH` لكل batch.  
**مرفوض:** دمج batch02+batch03 في module واحد؛ Tolerate بلا sunset.

---

## 6. الـ2 clones بين 1–100 وbatch03 prep

| Clone | قبل | بعد | مخاطرة تسريب |
|---|---|---|---|
| provenance #63/#106 | كود مكرر | **Eliminate** — `provenance_hot_storage_payload()` | لا — delegate مشترك |
| import header batch02/batch03 | هيكل import متشابه | **Invest** (ADR-003) — 1 clone jscpd متبقٍ | لا — batch03 **محظور** للإغلاق |

**لا منطق قدرة 1–100 مستقل داخل 101–150** — فقط prep stubs مع `catalog_link` إلى canonical.

---

## 7–8. Bandit MEDIUM + ACCEPTED_RISK

| Rule | File | القرار | صاحب القرار | التاريخ |
|---|---|---|---|---|
| B314 | `scripts/run_spine_coverage_snapshot.py:47` | **FIXED** (ElementTree → cobertura attrs) | Cursor Agent | 2026-09-01 |
| B310 | `scripts/complete_pdf_capabilities_826.py:124` | ACCEPTED_RISK | Cursor Agent | 2026-09-01 |
| B310 | `scripts/wave_00_passive_security_scan.py:17` | ACCEPTED_RISK | Cursor Agent | 2026-09-01 |
| B110 | `cap646/entitlements.py` (LOW×3) | ACCEPTED_RISK | Cursor Agent | 2026-09-01 |

**سجل:** `docs/ACCEPTED_RISK_REGISTRY.json` — **بانتظار countersignature المالك**.

---

## 9. إعادة تحقق ختامية

| فحص | النتيجة |
|---|---|
| (أ) `test_institutional_gate_full` | **EXIT:0** — `docs/GATE_FULL_LAST_EVIDENCE.txt` (~18.5 min) |
| (ب) jscpd cap646 official (بدون DB) | 3 clones داخل `batch01_dedicated.py` (intra-module) |
| (ب) jscpd batch02↔batch03 prep | **1 clone** (import header — Invest) |
| (ب) jscpd + hero batch04–17 | 18 clones (معظمه `database.py` billing patterns) |
| (ج) checksum الملخص | `993af4355bd3e6c6` — 79+11=90 ✓ |

---

## 10. شرط الإغلاق

| بند | الحالة |
|---|---|
| جدول القسم صفر | ✅ 79 صفًا |
| البنود 1–9 | ✅ مع أدلة |
| SONAR_TOKEN في CI | ⏳ **AWAITING_OWNER_ACTION** |
| دمج main | ⏳ **AWAITING_OWNER_ACTION** |
| توقيع HMAC | ⏳ **AWAITING_OWNER_ACTION** |
| موافقة المالك الكتابية | ⏳ **مطلوبة** |

**الإغلاق المؤسسي النهائي محظور** حتى اكتمال البنود الثلاثة أعلاه + توقيعك.

---

## 11. حظر batch03 و hero batches

- **Batch 03 (101–150):** محظور للتنفيذ/الإغلاق — prep فقط  
- **batch04–batch17 hero:** محظور حتى إغلاق 1–100  
- **مبدأ القسم صفر مكرر:** يُطبَّق ذاتيًا على أي دفعة قادمة + `cap-dedup-gate` CI

---

## القسم صفر مكرر — مبدأ حاكم دائم

1. **Eliminate** — دمج كامل أو Facade إلزامي (delegate بلا منطق مستقل)  
2. **Migrate** — نقل إلى canonical مع حظر النسخة القديمة  
3. **Invest** — Bounded Context موثَّق (ADR)  
4. **Tolerate** — ممنوع كحالة نهائية بلا sunset + خطة Migrate

**حارس CI:** `cap-dedup-gate` | **SSOT:** `docs/DUPLICATION_LOCK_TABLE_1_100.json`
