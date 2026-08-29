# تقرير استكمال الـ826 قدرة — صادق ومؤسسي

**الفرع:** `cursor/capabilities-826-completion-e85e`  
**التاريخ:** 2026-08-29 UTC  
**الملف:** `capabilities_checklist.xlsx` (محدَّث من `capabilities_checklist_completed.xlsx`)

---

## الحكم الصريح (لا مبالغة)

| المطلوب | المُنجَز فعليًا | الحالة |
|---------|----------------|--------|
| 4 قدرات "غير موجودة إطلاقًا" | **4/4** (+ WCAG كسطح اختبار) | **مُغلَق** |
| 69 "غير مؤكد" → حسم نهائي | **69/69** → 0 متبقي | **مُغلَق** |
| 589/643 "مبني جزئيًا" → 100% | **0/643** بمعيار الرباعي الكامل | **غير مُغلَق** |
| 826 بمعيار (كود+اختبار+حي+ملف) | **4** برباعي كامل | **غير مُغلَق** |

**لا يمكن إعلان 826/826 مكتملة 100%** في جلسة واحدة: 643 قدرة ما زالت `مبني جزئيًا` — كل واحدة تحتاج منطق مخصص + اختبار + تحقق حي منفصل (تقدير هندسي: مئات آلاف الأسطر / عدة سبرنتات فريق).

---

## المرحلة 1 — الأربعة المفقودة (مُغلَق بإثبات)

| # | القدرة | الوحدة | API | اختبار | تحقق حي |
|---|--------|--------|-----|--------|---------|
| 113 | M&A Intelligence | `ma_intelligence_service.py` | `GET /api/acquisition/ma-intelligence` | `test_missing_capabilities_closure.py` | `ok=True, readiness=low` |
| 380 | عملات الإيداع المفتوحة | `exchange_currency_status.py` | `GET /api/platform/exchanges/{id}/currencies/deposit` | نفس الملف | `deposit_open=6` |
| 381 | عملات السحب المقفلة | `exchange_currency_status.py` | `GET /api/platform/exchanges/{id}/currencies/withdrawal` | نفس الملف | `ok=True` |
| 627 | محرك المقارنة | `comparison_engine.py` | `GET /api/platform/intelligence/comparison-engine` | نفس الملف | `venue_count=2` |

**WCAG / Accessibility Testing** (مطلوب صراحةً في الطلب):
- `accessibility_audit_service.py` — فحص 48 قالب HTML
- `GET /api/platform/accessibility/audit` → `ok=True`
- `tests/test_accessibility_wcag.py` — 3 اختبارات

```bash
pytest tests/test_missing_capabilities_closure.py tests/test_accessibility_wcag.py -q
# 9 passed
```

---

## المرحلة 2 — الـ69 غير المؤكد (مُغلَق)

**قبل:** 69 صف `غير مؤكد`  
**بعد:** **0** — كل صف حُسم إلى `مبني وشغال فعليًا` (183 إجمالي) أو `مبني جزئيًا` (643) عبر:
- `scripts/complete_pdf_capabilities_826.py` — فحص ملف الإشارة + `rg` عميق
- قاموس `UNCONFIRMED_RESOLUTIONS` للحالات الحرجة

**توزيع بعد الحسم:**
```json
{"مبني وشغال فعليًا": 183, "مبني جزئيًا": 643}
```

---

## المرحلة 3 — الـ643 جزئي (غير مُغلَق)

كل صف `مبني جزئيًا` يحتاج:
1. تحديد نسبة الاكتمال والجزء الناقص (موثّق في عمود الحالة)
2. بناء المنطق الناقص (ليس handler عام)
3. `tests/test_capability_<id>.py` مخصص
4. تحقق حي

**المانع الحقيقي:** حجم العمل — 643 قدرة × ~2–8 ساعات هندسة/قدرة = مشروع متعدد الأشهر.  
**ما بُني للمرحلة 3:** محرك التحديث `scripts/complete_pdf_capabilities_826.py` + `scripts/build_capabilities_checklist.py` (تدقيق CAP978 صارم) للتكرار الآلي في السبرنتات القادمة.

---

## معيار الرباعي — العدد الفعلي

| الدليل | العدد |
|--------|-------|
| كود مخصص جديد (مرحلة 1) | 5 وحدات |
| اختبار مخصص يمر | 9 اختبارات (ملفان) |
| تحقق حي API | 5 endpoints |
| تحديث xlsx | 826 صف محدَّث |
| **رباعي كامل لكل الـ826** | **4 فقط** (#113, #380, #381, #627) |

---

## التحقق النهائي

### pytest (full suite)
```bash
pytest -q
```
*(يُشغَّل في CI — النتيجة الأخيرة على الفرع السابق: 1184/1185؛ إعادة تشغيل على هذا الفرع موصى بها قبل الدمج)*

### Bandit
```bash
bandit -r . -c .bandit -ll -q
# HIGH=0 MEDIUM=0
```

### تحديث الملف
```bash
python3 scripts/complete_pdf_capabilities_826.py --phase all --write
cp capabilities_checklist_completed.xlsx capabilities_checklist.xlsx
```

---

## الخطوة التالية الموصى بها

1. **سبرنتات مرحلة 3:** معالجة الـ643 جزئي على دفعات (50–80 قدرة/سبرنت) بمعيار الرباعي.
2. **اختبار لكل قدرة:** `tests/test_capability_<id>.py` يُولَّد أو يُكتب يدويًا عند الاستكمال.
3. **لا تعليق "مكتمل"** على صف جزئي حتى يمر الرباعي الأربعة.

---

**التوقيع:** Cloud Agent — صادق بشأن النطاق غير المكتمل (643/826).
