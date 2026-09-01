# CLOSURE-REJECT-02 — تقرير الاستجابة المرقّم (البنود 1–28)

**التاريخ:** 2026-09-01  
**الحالة الإجمالية:** `PENDING_CLOSURE` — **لا يُعلَن إغلاق مؤسسي**  
**الفرع:** `cursor/closure-reject-02-e85e`

---

## أ. إبطال وتصحيح (1–3)

### 1. إعادة الحالة إلى PENDING_CLOSURE

| الملف | الحالة السابقة | الحالة الحالية |
|-------|---------------|----------------|
| `docs/BATCH01_826_COMPLETION_MANIFEST.json` | INSTITUTIONAL_CLOSED | **PENDING_CLOSURE** |
| `docs/BATCH02_826_COMPLETION_MANIFEST.json` | INSTITUTIONAL_CLOSED | **PENDING_CLOSURE** |
| `docs/INSTITUTIONAL_CLOSURE_FINAL.json` | INSTITUTIONAL_CLOSED | **PENDING_CLOSURE** + `rejection: CLOSURE-REJECT-02` |
| `docs/INSTITUTIONAL_CLOSURE_BATCH01_BATCH02.md` | INSTITUTIONAL_CLOSED | **PENDING_CLOSURE** |

### 2. الموافقة الصريحة شرط سابق

وُثّق في كل manifest أعلاه:
- `"owner_approval_required": true`
- `"merge_does_not_imply_closure": true`

**الدمج على `main` (commit `9798ab8`, PR #349) لا يمنح صفة الإغلاق المؤسسي.**

### 3. تقارير سابقة أُبطِلت

| التقرير | الخطأ | التصحيح |
|---------|-------|---------|
| رد الوكيل 2026-09-01 «إغلاق مؤسسي نهائي» | ادّعى INSTITUTIONAL_CLOSED + جاهزية حية | **مُبطَل** — انظر `docs/INSTITUTIONAL_CLOSURE_BATCH01_BATCH02.md` |
| `docs/INSTITUTIONAL_CLOSURE_FINAL.json` (ما قبل REJECT) | `all_verified: true` = إغلاق | → orchestrator محلي فقط، `PENDING_CLOSURE` |
| PR #349 merge subject | «INSTITUTIONAL_CLOSED» | العنوان تاريخي؛ الحالة الرسمية **PENDING_CLOSURE** |
| `docs/BATCH02_HONEST_CLOSURE_AUDIT.md` | «CLOSED» | → **PENDING_CLOSURE** |

---

## ب. البوابات (4–6)

### 4. gate-full

| البند | الدليل |
|-------|--------|
| آخر تشغيل على main بعد merge | **FAILURE** — https://github.com/mopayment1-commits/blackdark/actions/runs/33512905843 |
| السبب | `test_institutional_gate_full` — `AttributeError: 'str' object has no attribute 'exists'` في `database.py:1969` |
| الإصلاح المُطبَّق | `database.py` — `Path(config.DB_PATH)` قبل `.exists()` |
| الحالة | **إصلاح مُرسل على الفرع** — إعادة تشغيل gate-full على main **معلّقة** حتى push + CI |
| تشغيل ناجح سابق (schedule) | https://github.com/mopayment1-commits/blackdark/actions/runs/33490933876 (gate-full **success**) |

**لم تُحقَّق gate-full خضراء على main بعد الإصلاح — البند 4 غير مكتمل.**

### 5. إعادة تسمية السكربت الذاتي

| السكربت القديم | السكربت الجديد | ما يتحقق منه كل سكربت |
|---------------|---------------|----------------------|
| `institutional_closure_final_gate.py` (**حُذف**) | `run_batch_verification_orchestrator.py` | — |

**السكربتات الثمانية:**

| # | السكربت | يتحقق من |
|---|---------|----------|
| 1 | `audit_official_batch01_rtm.py` | RTM 50/50 batch01 PRODUCTION-ALIGNED |
| 2 | `audit_official_batch02_rtm.py` | RTM 50/50 batch02 |
| 3 | `verify_batch01_production.py` | تنفيذ spine batch01 لكل ID |
| 4 | `verify_batch01_http_all50.py` | HTTP 200 لـ IDs 1–50 |
| 5 | `verify_batch01_http_11_fixed.py` | HTTP 11 ID سابقًا معطّلة |
| 6 | `verify_entitlement_gateway_proof.py` | entitlement batch01 — **10 IDs** |
| 7 | `verify_official_batch02_production.py` | HTTP 200 لـ IDs 51–100 |
| 8 | `verify_entitlement_batch02_gateway_proof.py` | entitlement batch02 — **10 IDs** |

**النتيجة:** `docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json` — **ليس بوابة CI**.

### 6. SonarCloud (أرقام من API — 2026-09-01)

| المقياس | القيمة |
|---------|--------|
| `duplicated_lines_density` (كل المشروع) | **0.8%** |
| `new_duplicated_lines_density` (كود جديد) | **0.7%** — ✅ تحت عتبة 3.0% |
| Reliability Rating (overall) | **5.0** (أسوأ) |
| Security Rating (overall) | **5.0** (أسوأ) |
| Maintainability Rating (sqale) | **1.0** (أفضل) |
| Quality Gate | **FAILED** — https://sonarcloud.io/dashboard?id=mopayment1-commits_blackdark&branch=main |

**شروط الفشل بالاسم (new code period):**

| الشرط | العتبة | الفعلي | الحالة |
|-------|--------|--------|--------|
| `new_reliability_rating` | ≤1 | **5** | ❌ |
| `new_security_rating` | ≤1 | **5** | ❌ |
| `new_coverage` | ≥80% | **13.8%** | ❌ |
| `new_duplicated_lines_density` | ≤3% | **0.7%** | ✅ |
| `new_maintainability_rating` | ≤1 | **1** | ✅ |
| `new_security_hotspots_reviewed` | 100% | **100%** | ✅ |

**CWE-1041 / python:S1041:** Sonar API أعاد **1618** انتهاكًا مفتوحًا على `branch=main` عند البحث بقاعدة S1041 (معظمها `python:S7503` async في `batch02_dedicated.py`). **لم تُصلَح حتى خضراء — البند 6 غير مكتمل.**

آخر run: https://github.com/mopayment1-commits/blackdark/actions/runs/33512905952

---

## ج. سلامة القدرات — R1 (7–11)

### 7. #53 — هوية القدرة

| البند | الدليل |
|-------|--------|
| الهدف الأصلي المُسجَّل | **BTC-to-Macro Coupling** — `docs/cap646/CAP646_CATALOG.json` id 53 |
| السطح السابق الخاطئ | `ai_decision_intelligence` (مسار generic `evaluate_opportunity`) |
| السطح الحالي | `btc_to_macro_coupling` — `cap646/handlers/ai.py:51-82` |
| هل الهدف الجديد يحققه؟ | **نعم** — الهدف المُسجَّل هو coupling وليس AI oracle عام |
| الحكم | **PRODUCTION-ALIGNED** (ليس NOT_COMPLETE) |
| إثبات 5 رموز + kind | `docs/CAP53_MULTI_SYMBOL_PROOF.json` — BTC/ETH/SOL/AVAX/DOGE، `all_verified: true` |

### 8. المساعدات الدفاعية

| المساعدة | الملف | سلوك الفشل | هل 200 فارغ؟ |
|----------|-------|------------|-------------|
| `build_macro_context_safe` | `macro_correlations.py:329-335` | `except` → `_mock_macro_indicators()` + `macro_context_from_snapshot` | **لا** — يُرجع macro_regime + scores |
| `_opportunity_symbol` | `ai_oracle.py:91-95` | يُرجع `str` من dict أو `"BTC"` | **لا** — لا HTTP |
| `_opportunity_field` | `ai_oracle.py:97-100` | `default=0` عند غياب المفتاح | **لا** — لا HTTP |

**#53 استجابة كاملة (BTC):** انظر `docs/CAP53_MULTI_SYMBOL_PROOF.json` → `proofs[0].spot_futures.full_response` — حقول `btc_to_macro_coupling`, `macro_context`, `success: true`.

### 9. مسارات تنفيذ غير رسمية (1–100)

**الملف:** `docs/EXECUTION_PATH_AUDIT_1_100.json`

| IDs | المسار | التبرير |
|-----|--------|---------|
| 1,2,3,4,10,21,38,39,45 | `batch01_free_tier` → `execute_free_tier_capability` | مُعلَن في `batch01_production._BATCH01_FREE_TIER` |
| 55,56,59,60 | `overlap_batch01_legacy` | OVERLAP_BATCH01 — لا handler batch02 |

**باقي IDs 1–100:** `batch01_dedicated` أو `batch01_handler_group` أو `batch02_dedicated` — مسار spine رسمي.

### 10. Hero Batch 03 (201–300, PR #343)

| السؤال | الجواب |
|--------|--------|
| هل يُعاد تقييمها؟ | **نعم** — بالمعيار PRODUCTION-ALIGNED الجديد |
| متى؟ | **بعد** إغلاق مؤسسي لـ batch01+02 + موافقتك الصريحة |
| تقاطع مع 1–100؟ | **لا** — `intersection: []` في `docs/PROGRESS_826_CANONICAL.json` |

### 11. VERIFIED_COMPLETE في cap978/verify.py

**لم يُستأصل** — يبقى في namespace cap978 CI الداخلي.  
**وُثّق:** تعليق في `cap978/verify.py:139-143` + `classification_taxonomy.VERIFIED_COMPLETE` في inventory.  
**تاريخ إزالة مستهدف:** 2026-09-30 → استبدال بـ `PRODUCTION-ALIGNED` / `FUNCTIONALLY_INCOMPLETE`.

---

## د. سلامة الدفعة 02 — R2 (12–16)

### 12. #51, #52, #54, #57, #58

| ID | العرض (catalog) | السبب الجذري R1 | الإصلاح R2 | الإثبات |
|----|----------------|-----------------|------------|---------|
| 51 | Macro & Traditional Finance Integration | لم يكن في spine batch02 الرسمي | `batch02_dedicated._cap051` | `BATCH02_HTTP_PROOF_51_100.json` id 51 HTTP 200 |
| 52 | Cross-Asset Return Breadth |同上 | `_cap052` |同上 id 52 |
| 54 | Global Liquidity Intelligence |同上 | `_cap054` |同上 id 54 |
| 57 | **Profitability Map** (ليس Open Interest) |同上 | `_cap057` → `profitability_analyzer_582` |同上 id 57 |
| 58 | Custom No-Code Charting |同上 | `_cap058` → `chart_config` |同上 id 58 |

### 13. MECE #57 vs #85

**الحكم: DISTINCT** — `docs/MECE_DUPLICATE_AUDIT_1_100.json`  
- #57 = Profitability Map / `profitability_map` / `profitability_analyzer_582`  
- #85 = Futures Open Interest / `futures_open_interest_intelligence` / `derivatives_overview`  
- **تصحيح R2:** المستخدم ذكر «Open Interest» لـ#57 — الكتالوج يسجّل «Profitability Map».

### 14. OVERLAP_BATCH01

**مُسجَّل رسميًا:** `docs/REUSED_LINK_TAXONOMY.json` → `OVERLAP_BATCH01`  
- IDs: 55, 56, 59, 60  
- **لا handler batch02** — `independent_build: false`  
- **لا تُحتسب كبناء مستقل** في تقدم 826

### 15. #106/#107/#110/#125

| الحالة | LINK-ELIGIBLE |
|--------|---------------|
| محتسبة في التقدم؟ | **لا** |
| أدلة ثلاثية | canonical في taxonomy + `batch03_dedicated.py` — **إغلاق محظور** حتى batch03 |

### 16. تصحيح الإحصاء

**الصحيح:** IDs 61–100 = batch02 dedicated (40). IDs 51–60 تشمل 4 OVERLAP (55,56,59,60) بلا handler batch02.  
**العبارة الخاطئة «61–100 ما عدا overlap»** — **مُصحَّحة** في `BATCH02_826_COMPLETION_MANIFEST.json`.

---

## هـ. الأدلة — R4 (17–22)

### 17. HTTP batch01 — 50/50

| الملف | السكربت | التاريخ | النتيجة |
|-------|---------|---------|---------|
| `docs/BATCH01_HTTP_PROOF_1_50.json` | `verify_batch01_http_all50.py` | 2026-09-01T13:06:29Z | **50/50** `all_verified: true` |
| `docs/BATCH01_HTTP_PROOF_11_FIXED.json` | `verify_batch01_http_11_fixed.py` | 2026-09-01 | **11/11** (مجموعة فرعية سابقة) |

كل ID 1–50 مُدرج في `proofs[]` داخل `BATCH01_HTTP_PROOF_1_50.json` مع `status_code: 200`.

### 18. PR #348

| البند | الدليل |
|-------|--------|
| الحالة | **MERGED** — https://github.com/mopayment1-commits/blackdark/pull/348 |
| merge commit | `f3f5c5cb2d09a3df94382be86e1cf36cf54c76f0` |
| في main؟ | **نعم** — `git merge-base --is-ancestor f3f5c5c main` |
| علاقته بـ#349 | #348 دُمج أولاً؛ #349 يتضمن نفس المحتوى + batch02 |

### 19. Entitlement

| الدفعة | الملف | IDs | skip_entitlement |
|--------|-------|-----|------------------|
| batch01 | `docs/BATCH01_ENTITLEMENT_GATEWAY_PROOF.json` | 10 IDs (1,8,21,38,39,24,47×2,50,103) | **نفي:** `no_skip_entitlement: true` |
| batch02 | `docs/BATCH02_ENTITLEMENT_GATEWAY_PROOF.json` | 10 IDs (51,53,55-60,69,85,100,103) | **نفي:** `no_skip_entitlement: true` |

رفض صحيح: #47 free → `tier_insufficient`؛ #103 free → denied.

### 20. pytest

```
python -m pytest -m "not slow" --tb=no
→ 2604 passed, 2 skipped, 4 deselected, 0 failed
```

المدة: 315.47s — **2026-09-01 على الفرع الحالي**.

### 21. مستندات ساقطة

| المستند | الحالة |
|---------|--------|
| `docs/BATCH02_HONEST_CLOSURE_AUDIT.md` | **مُحدَّث** → PENDING_CLOSURE |
| `capabilities_checklist.xlsx` | **موجود** — مُدرج في manifests؛ صفوف 51–100 محدّثة سابقًا |

### 22. سجل إنشاء manifests

| الملف | commit الإنشاء | التاريخ |
|-------|---------------|---------|
| `BATCH01_826_COMPLETION_MANIFEST.json` | `26ea9632043a99c66ba9e505cfdd9326dccaa226` | 2026-08-31T22:08:17Z |
| `BATCH01_PRODUCTION_PROOF.json` | **نفس commit** `26ea963` | 2026-08-31T22:08:17Z |

---

## و. رقم التقدم (23)

**الرقم الحاسم الوحيد: `114/826`**

الملف: `docs/PROGRESS_826_CANONICAL.json`

| المكوّن | الاحتساب |
|---------|----------|
| (أ) 338/500/507/534 | ضمن 114 إذا status=PRODUCTION-ALIGNED في inventory |
| (ب) Hero 201–300 PR #343 | **لا يُحتسب** حتى إعادة تقييم — `hero_production_aligned_count` للمرجعية فقط |
| (ج) OVERLAP 55,56,59,60 | **تُحتسب مرة واحدة** ضمن 114 — ليست +4 إضافية |
| (د) LINK-ELIGIBLE 106,107,110,125 | **مُستبعدة** من البسط |

---

## ز. جاهزية التشغيل الحي (24–26)

### 24. Google SRE PRR — **غير مُحقَّق**

| المتطلب | الحالة |
|---------|--------|
| (أ) مراقبة وتنبيهات cap646 | ❌ غير موثّق |
| (ب) rollback مُختبَر | ❌ موثّق فقط — `docs/ROLLBACK_BATCH01_BATCH02.md` |
| (ج) p95 معلن | ❌ |
| (د) حمل متزامن | ❌ |

**الصياغة البديلة المُطبَّقة:** «مكتمل وظيفيًا — جاهزية التشغيل الحي غير مُقيَّمة بعد»

### 25. «المنصة جاهزة للمستخدمين»

**حُذف من كل التوثيق المُحدَّث.** النطاق = **100/826** IDs رسمية batch01+02.

### 26. tag + rollback

| البند | الدليل |
|-------|--------|
| tag | `batch01-02-pending-closure-v1` على commit post-fix (يُنشأ عند push) |
| rollback | `docs/ROLLBACK_BATCH01_BATCH02.md` |

---

## ح. شرط الإغلاق (27–28)

### 27. قائمة التحقق

| البند | مكتمل؟ |
|-------|--------|
| 1–3 إبطال | ✅ |
| 4 gate-full خضراء على main | ❌ (إصلاح مُرسل، CI معلّق) |
| 5 إعادة تسمية orchestrator | ✅ |
| 6 SonarCloud خضراء | ❌ |
| 7–22 أدلة | ✅ (مع فجوات PRR/Sonar/gate-full) |
| 23 رقم 114/826 | ✅ |
| 24–26 جاهزية حية | ✅ (ادّعاء مُزال) |
| موافقتك الصريحة | ❌ **معلّقة** |

### 28. Batch 03

**محظور.** `batch03_prep` لا يُحتسب ولا يُغلق.

---

## الخلاصة

**لا يوجد إغلاق مؤسسي.** الحالة الرسمية: **`PENDING_CLOSURE`**.  
المعوّقات المتبقية: **gate-full على main**، **SonarCloud QG**، **موافقتك المكتوبة**.
