# تقرير لجنة الفحص النافي للجهالة (1/2)
## حصر كامل — نقاط الضعف والعيوب الحالية عند BLACKDARK

> **الصفة:** رئيس لجنة فحص نافٍ للجهالة (Acquirer / Fund DD Chair)  
> **المنتج:** BLACKDARK Trust OS  
> **التاريخ:** 2026-08-09  
> **قاعدة الصدق:** لا تجميل · لا خلط بين «كود جاهز» و«إنتاج مثبت» · لا خلط مع تقرير القدرات الناقصة (تقرير منفصل)  
> **التقرير الشقيق:** [`DD_COMMITTEE_MISSING_CORE_CAPABILITIES_AR.md`](./DD_COMMITTEE_MISSING_CORE_CAPABILITIES_AR.md)

---

## 0) حكم اللجنة التنفيذي

| السؤال | الحكم |
|--------|--------|
| هل المنتج بلا عيوب؟ | **لا** |
| هل نواة القرار/الإثبات قوية نسبيًا؟ | **نعم** (Ledger · Veto · Net-Edge · Evidence) |
| أكبر عيب أمام مستحوذ/صندوق اليوم؟ | **غياب إثبات التشغيل الحي** (HA موقّع + إيراد + SSO/عزل) مع **جودة نماذج bootstrap** |
| هل يصلح الادعاء «جاهز لاستحواذ premium / إطلاق فيروسي مثبت»؟ | **لا** — حتى تُغلق البنود الحرجة أدناه |

**تصنيف العيب:**
- **P** = عيب منتج/جودة بيانات أو هندسة  
- **O** = تشغيل / أسرار / بنية تحتية (HUMAN_OPS)  
- **M** = سوق / علامة / تجاري  
- **H** = فجوة صدق/ادعاء (Honesty gap)

---

## 1) حرج — Critical

| # | نقطة الضعف / العيب | النوع | الدليل | أثر على اللجنة |
|---|---------------------|------|--------|----------------|
| C1 | **لا إثبات حمل موقّع (HA/viral)** — Soft Launch فقط؛ `proven_signed_load_test=false` | O | `docs/LOAD_TEST_RUN_LOG.md` · `viral_capacity.py` · `docs/VIRAL_LAUNCH_CAPACITY.md` | أي رقم 1k–10k مستخدمين = ادّعاء غير قابل للدفاع |
| C2 | **الوضع الافتراضي Soft Launch / SQLite / عامل واحد** ⇒ `viral_codepath_ready=false` | O/P | `viral_capacity.py` · `production_guard.py` · `.env.example` | ليس وضع صندوق ولا إطلاق فيروسي |
| C3 | **إيراد صفر / لا LOI استحواذ premium** — لا مشترين مدفوعين مثبتين | M | `docs/PRODUCT_COMPLETE_STATUS.md` · `docs/MKT_MARKET_BARRIERS.md` | التقييم ينزل لـ acqui-hire/أصل بيانات |
| C4 | **تنفيذ DEX حي ناقص** — مسار CEX↔DEX يُجبر dry-run / blocked حتى Jupiter كامل | P | `bd_platform/cex_dex_executor.py` · تدقيق 2026-08-06 | منتج «مراجحة قابلة للتنفيذ» غير مكتمل على ساق DEX |

---

## 2) عالي — High

| # | نقطة الضعف / العيب | النوع | الدليل | أثر |
|---|---------------------|------|--------|-----|
| H1 | **HUMAN_OPS مفتوح بالاسم:** PSP/webhook، WhatsApp Cloud، OAuth secrets، Postgres+Redis، صف حمل، نشر Glass Box، 60ث مؤسس، محامٍ/WAF/Pentest | O | `docs/DEFERRED_HUMAN_STEPS.md` | الإطلاق التجاري معلّق على حسابات خارجية |
| H2 | **D5 Regime bootstrap / عيّنات ضعيفة** — `per_regime_models_live_bootstrapped`؛ أنظمة بلا عيّنات كافية؛ accuracy holdout منخفضة على بعض الأنظمة؛ موازنة synthetic في التدريب | P/H | `data/models/regime/training_status.json` · `PRODUCT_COMPLETE_STATUS.md` | نموذج «نظام السوق» غير ناضج بما يكفي للجنة كمية |
| H3 | **Half-Life بارد على المسار الاتجاهي** — fallback أفق 1س مع `cold_start: true` عند ضعف التاريخ | P | `decision_enrichment.py` · `opportunity_tracker.py` | وعد «زمن = مال» أضعف حتى تتراكم العيّنات |
| H4 | **التنفيذ المالي الحقيقي dry-run افتراضيًا** — طبقات حماية متعددة قبل LIVE؛ المحاكي يتجاهل بعض واقع الانزلاق/الجزئي | P (سلامة) / O (للتشغيل الحي) | `execution_engine.py` · `production_guard.py` · `legal_content.py` | ليس عيب أمان؛ لكنه يحدّ ادّعاء «تنفيذ حي كامل» |
| H5 | **الدفع/الهوية غير جاهزين للحملة بدون أسرار** — Lemon/Stripe/KYC؛ مؤسسي = استفسار/فاتورة لا checkout ذاتي كامل | O | `payments_usd.py` · `DEFERRED_HUMAN_STEPS.md` | لا ARR حي |
| H6 | **وضع أمني ≠ شهادة امتثال** — لا SOC2/ISO/Pentest/WAF في المستودع كإثبات | O | `security_posture.py` · `docs/SECURITY_HARDENING.md` | قتل في استبيان أمن الصناديق |
| H7 | **توتر صدق التغطية** — سجل كون قد يظهر جاهزية واسعة بينما مصادر ingestion الحية قد تكون 0؛ تغطية أضيق من Glassnode/Kaiko | P/M/H | `platform_universe.py` · `coverage_honesty.py` · دراسة F10 | خطر مبالغة تغطية إن لم تُعرض لوحة الصدق دائمًا |
| H8 | **ادعاء «product complete» مع D5 ما زال bootstrap** | H | `ZERO_NON_HUMAN_DEFERRALS.md` مقابل `training_status.json` | فجوة صدق أمام DD دقيق |

---

## 3) متوسط — Medium

| # | نقطة الضعف / العيب | النوع | الدليل |
|---|---------------------|------|--------|
| M1 | **D8 صفوف pending / أنواع بإشارة وزن منخفضة** (lexicon غير مكتمل لبعض الأنواع) | P | `signal_registry.py` · تدقيق شامل |
| M2 | **WhatsApp دفع خادم يحتاج توكن Meta** — بدونها wa.me فقط | O | `alert_service.py` |
| M3 | **OAuth Google/GitHub خامل بلا client secrets** | O | `oauth_service.py` · `AUTH_IDENTITY_PROFILE.md` |
| M4 | **امتداد المتصفح Load unpacked فقط** — لا نشر Chrome Web Store | O/M | `browser_extension/README.md` |
| M5 | **قفل سلسلة التدقيق process-local**؛ كتب مشتركة ليست الافتراضي؛ سقف B2B WS (~50) | P | `oracle_audit_chain.py` · `b2b_websocket_hub.py` |
| M6 | **تغطية اختبارات ضيقة** — fail_under على مجموعة وحدات محدودة لا قلب dashboard/execution كامل | P | `.coveragerc` |
| M7 | **Net-Edge على المسار الاتجاهي استشاري (soft)** لا قتل صلب دائمًا | P | `decision_enrichment.py` |
| M8 | **خطر عيّنات صغيرة** — استبعاد synthetic من الـ hit-rate صحيح، لكنه يترك أنظمة بلا بيانات كافية | P | `ml/train_regime_models.py` · `database.py` |
| M9 | **أكواد إطلاق ترويجية افتراضية مضمّنة** ما لم تُستبدل | P | `config.py` |
| M10 | **علامة أحدث + تغطية أضيق** — ضعف تنافسي نسبي (مُخفَّف بـ Miss Feed/Coverage Honesty لا مُلغى) | M | `BRAND_COVERAGE_RADICAL_CLOSURE_AR.md` · دراسة السوق |
| M11 | **تعارض وثائقي لغة الواجهة** — دستور English-only مقابل إلزام 15 لغة لاحق؛ مفاتيح ناقصة → EN | H/P | `PRODUCT_CONSTITUTION_AR.md` · `i18n_service.py` |

---

## 4) منخفض — Low

| # | نقطة الضعف / العيب | النوع | الدليل |
|---|---------------------|------|--------|
| L1 | لا Phone/SMS auth في v1؛ MFA اختياري للمستخدم لا إجباري للمنظمة | P | `AUTH_IDENTITY_PROFILE.md` |
| L2 | لا SEPA/ACH/crypto rails — USD hosted فقط | P | `PAYMENTS_USD_SECURITY.md` |
| L3 | حجم `dashboard.py` / مسارات قرار مزدوجة محتملة — عبء صيانة | P | تدقيق معماري |
| L4 | بوابات جودة خارجية (Sonar/Lighthouse/CI) ليست «خضراء للأبد» | O | جرد السبت/الأحد |
| L5 | خطر عملية: ادعاء اكتمال على فرع غير المدمج تاريخيًا | H | `FINAL_STRICT_CONFIRMATION_SAT_SUN_AR.md` |

---

## 5) ملخص كمي للجنة

| الشدة | العدد التقريبي |
|-------|----------------|
| Critical | 4 |
| High | 8 |
| Medium | 11 |
| Low | 5 |
| **المجموع المحصور** | **~28 نقطة ضعف/عيب موثّقة** |

| حسب الطبيعة | الغالب |
|-------------|--------|
| تشغيل/أسرار O | PSP · HA · OAuth · WA · WAF/Pentest · Glass Box post |
| منتج/بيانات P | D5 bootstrap · Half-Life بارد · DEX حي · D8 pending · audit HA · coverage tension |
| سوق M | علامة · تغطية نسبية · 0 paid |
| صدق H | complete vs bootstrap · تغطية اسمية vs حية · لغة UI |

---

## 6) ما ليس عيبًا (حتى لا يُخلط)

- dry-run الافتراضي **قرار سلامة** لا إهمال — العيب هو ادعاء تنفيذ حي بلا مفاتيح/سماح.  
- HUMAN_OPS المدرجة بالاسم **ليست سهو كود** — لكنها **عيوب جاهزية إطلاق** أمام اللجنة.  
- Kill-Rate / Miss Feed / Coverage Honesty **تخفّف** ضعف العلامة/التغطية ولا تمسحها من قائمة المخاطر التنافسية.

---

## 7) توصية رئيس اللجنة (للعيوب فقط)

1. **قبل أي pitch مؤسسي:** أغلق C1+C2+H5 (Postgres/Redis + صف حمل موقّع + دفعة تجريبية حية).  
2. **قبل أي ادّعاء نموذج ناضج:** أفصح D5 bootstrap علنًا واستبدل bootstrap بعيّنات حية (H2/H8).  
3. **امنع تسويق التغطية الاسمية** — اعرض Coverage Honesty فقط (H7).  
4. **لا تستخدم عبارة «بلا عيوب / 100% مطلق»** في غرفة البيانات.

---

*تقرير 1/2 — نقاط الضعف والعيوب فقط. القدرات الأساسية الناقصة = التقرير 2/2.*
