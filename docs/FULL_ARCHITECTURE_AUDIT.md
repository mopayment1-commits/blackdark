# BLACKDARK — مراجعة هندسية شاملة (Architecture & Code Audit)

> **تاريخ:** 2026-08-05  
> **النطاق:** المعمارية، مسار Oracle/ML، خط البيانات، الأمان، Postgres، الاختبارات  
> **المنهج:** فحص كود + استيراد runtime + `pytest`  
> **Completion contract:** [`PRODUCT_COMPLETE_STATUS.md`](./PRODUCT_COMPLETE_STATUS.md) · human-only [`DEFERRED_HUMAN_STEPS.md`](./DEFERRED_HUMAN_STEPS.md)

---

## تحديث إغلاق (code-complete)

تم إغلاق فجوات الربط التنفيذية داخل المستودع: Oracle الموحّد، D5 regime train + flywheel hook، RL soft fusion، `/health/ready` بعد boot، Kafka off-loop، admin plan/roadmap، prod ML deps + model bake، email outbox، Stealth Advisor v2. المتبقي البشري فقط (نشر/أسرار/إعلان).

---

## الخلاصة التنفيذية

المشروع **غني بالمكوّنات** وقابل للتوسع كمنصة crypto intelligence، لكن قبل توسيع تصميم نموذج الذكاء المالي كان هناك **حاصرات جوهرية** تجعل مسار Oracle الموحّد وملامح ML غير شغّالة فعلياً، مع فجوات أمان/نشر خطيرة.

| الحالة بعد هذه الجولة | العدد التقريبي |
|------------------------|----------------|
| حرج (كان يعطل التصميم/التشغيل) | 8+ |
| عالي | 10+ |
| متوسط | عدة |
| إصلاحات مطبّقة في هذه الجولة | مسار Oracle/ML + stale quotes + PG fetch + labeling |

**حكم عام:** التصميم المعماري سليم كفكرة (ingestion → features → rules/ML → guards → flywheel)، لكن التنفيذ كان **غير مكتمل/غير متسق** في نقاط الربط الحرجة. بعد الإصلاحات الحالية يمكن استئناف تصميم النموذج المالي بثقة أعلى على مسار Oracle.

---

## نتائج الاختبارات (قبل/بعد إصلاحات هذه الجولة)

### قبل هذه الجولة
- **144 passed / 9 failed**
- أعطال مؤكدة: `stale_price_guard` ImportError (`get_quote_age_ms`) + حاصرات Oracle/ML

### بعد إصلاحات هذه الجولة
- **154 passed / 5 failed**
- فُتحت اختبارات slippage (4) + أُضيفت 6 اختبارات مسارات حرجة
- المتبقي (غير حاجز لنموذج AI مباشرة): fee_matrix mock، launch `/data` permissions، plan_audit نص عربي، footprint بدون جدول، production_guard شكل الخدمة

### حاصرات runtime مؤكدة بأمر استيراد
| المكوّن | العطل |
|---------|--------|
| `oracle_unified` | ImportError: `is_extreme_positive_sentiment` من `sentiment_engine` |
| `weight_aggregator` | رموز مفقودة: `build_full_market_context`, `apply_modal_adjustments_with_regime`, `detect_market_regime`, … |
| `model_weights_guard` | `public_weights_summary` مفقود |
| `ml/feature_store` | يستدعي APIs بأشكال خاطئة → ميزات multimodal تُصفر دائماً |
| `stale_price_guard` | يعتمد على دوال غير موجودة في `live_book_hub` |

---

## 1) مسار الذكاء الاصطناعي / Oracle (الأهم للتصميم)

### Critical — تم إصلاحه في هذه الجولة
1. **مسار `compute_unified_oracle` كان ميتاً** بسبب imports مكسورة + APIs ناقصة في `weight_aggregator`.
2. **Feature store** كان يدرّب على أصفار (sentiment/OBI/macro) بسبب mismatch مع دوال sync/async الحقيقية.
3. **تسمية الدقة `score_verdict_accuracy`** كانت تفسّر `BULLISH_ANALYTICS` خطأ و`WAIT` كـ avoid.
4. **`dashboard._score_prediction_accuracy`** كان يقارن `"BUY"` بينما الداخلي `"Buy Now"`.
5. **Conflict guard** كان يقرأ `conflicts` غير المُنتَجة — الآن `compute_modal_breakdown` يصدرها.

### High — ما زال قائماً (يحتاج جولة لاحقة)
| # | المشكلة | الأثر |
|---|---------|-------|
| H1 | مساران للقرار: `ai_oracle` (مراجحة) vs `oracle_unified` (داشبورد) | عينات تدريب غير متجانسة |
| H2 | Ensemble يكتب الموديل بدون بوابة `validate_model_deployment` | خطر نشر نموذج متراجع |
| H3 | تأخير flywheel (ساعة) قد يختم أسعار 1h/4h متأخرة | فساد أفق التسمية |
| H4 | عينات مراجحة غالباً `price=0` في `evaluate_and_store` | labels مجهولة/flat |
| H5 | تطبيق ماكرو مزدوج محتمل في `ai_oracle` | تحيز Risk-On/Off |
| H6 | RL policy غير موصول بمسار القرار | خلاف بين الوثائق والتنفيذ |
| H7 | Fail-open في بعض الحراس (sentiment gate عند فراغ الكاش) | قرارات تبدو سليمة وهي ناقصة |

---

## 2) خط البيانات / المراجحة / التشغيل

| الشدة | المشكلة | الدليل |
|-------|---------|--------|
| HIGH | `HOT_STORAGE_MIRROR_SQLITE=false` افتراضياً → الـ aggregator لا يغذي DB التي يقرأها arb | `config.py`, `hot_storage.py` |
| HIGH | عمليات منفصلة (aggregator/arb) لا تتشارك ذاكرة الكتب بدون Redis/mirror | docker-compose + in-memory hubs |
| HIGH | Ready endpoint دائماً ok قبل اكتمال `init_db` | `dashboard.py` lifespan |
| HIGH | `requirements-prod.txt` ينقصه ccxt/pandas/sklearn… بينما Docker يستخدمه | Dockerfile |
| MED | `scan_coordinator` يمسك القفل أثناء المسح كامل | يقتل التوازي |
| MED | Kafka consumer متزامن داخل asyncio task | يجمّد event loop |

---

## 3) PostgreSQL / النشر

| الشدة | المشكلة | الحالة |
|-------|---------|--------|
| CRITICAL | `PgConnectionAdapter.execute` لا يدعم `fetchall/fetchone` | **أُصلح** في هذه الجولة |
| CRITICAL | `_apply_migrations` يخرج مبكراً على Postgres → جداول/أعمدة ML وkeys وrisk ناقصة | **ما زال** |
| HIGH | SQL خاص بـ SQLite (`datetime(... '+' || ?`) و`INSERT OR IGNORE` في runtime | جزئياً مخفف لـ IGNORE |
| HIGH | production_guard لا يفشل الإقلاع (fail-open) | ما زال |

---

## 4) الأمان

| الشدة | المشكلة |
|-------|---------|
| CRITICAL | `/arb/cex-dex/execute` بدون auth ويمكن `dry_run=false` |
| CRITICAL | حارس مفاتيح التنفيذ (`api_key_security_guard`) غير موصول بـ `execution_engine` |
| CRITICAL | أسرار افتراضية ثابتة: vault key، session pepper، B2B demo key |
| HIGH | `require_admin_dev` يمرّر admin لأي localhost client host |
| HIGH | مسارات platform_api متعدّدة تغيّر حالة بدون مصادقة كافية |
| HIGH | auto-execution يشتري دائماً `side=buy` وليس تحوّط مراجحة حقيقي |

---

## 5) اتساق الوثائق مع الكود

| الوثيقة | التناقض |
|---------|---------|
| `AI_MODEL_TRANSFORMATION.md` §5 | يذكر `opportunity_score/confidence` كميزات بينما التدريب يستبعدها (صحيح في الكود) |
| `AI_FINANCIAL_MODEL_DESIGN.md` | يصف مسار موحّد + RL fusion بينما RL غير موصول والمراجحة ما زالت على `ai_oracle` |
| `GAPS_COMPLETED.md` / خطة اليوم | تدّعي اكتمال track-record/accuracy بينما مسار التسمية كان مكسوراً |

---

## 6) ما هو متين فعلاً

- نية anti-leakage في `FEATURE_COLUMNS` + اختبارات `test_ml_integrity`
- تقسيم زمني للتدريب (بدون shuffle)
- استبعاد synthetic من التدريب الحي
- سلسلة تدقيق `oracle_audit_chain` hash-linked
- محركات المراجحة الأربع منطقها الرياضي الأساسي متماسك
- وجود flywheel scheduler وواجهات `/api/ml/*`

---

## 7) الإصلاحات المنفّذة في هذه الجولة

| ملف | الإصلاح |
|-----|---------|
| `oracle_unified.py` | استيراد greed من `sentiment_manipulation_guard` |
| `weight_aggregator.py` | إضافة regime APIs + `build_full_market_context` + conflicts |
| `model_weights_guard.py` | `public_weights_summary` |
| `ml/feature_store.py` | ميزات حقيقية من rolling sentiment / OBI books / macro |
| `ml/labeling_pipeline.py` | تسمية وفق taxonomy التنظيمي |
| `dashboard.py` | توحيد scorer مع labeling pipeline |
| `live_book_hub.py` | `get_quote_age_ms` / `is_quote_fresh` |
| `postgres_backend.py` | نتائج قابلة لـ fetchall/fetchone + تخفيف INSERT OR IGNORE |

---

## 8) حالة P0 بعد الإصلاح الجذري (2026-08-05)

| بند P0 | الحالة |
|--------|--------|
| توحيد مسار القرار arb+dashboard عبر `apply_unified_adjustments` | ✅ |
| Auth على `/arb/cex-dex/execute` + مسارات تعديل أخرى | ✅ |
| ربط `live_execution_allowed` + vault credentials في execution | ✅ |
| Postgres migrations تعمل (لا early-return) + أعمدة ML في SCHEMA | ✅ |
| أسرار الإنتاج fail-closed + production_guard موسّع | ✅ |
| ميزات ML موسّعة + بوابة deploy للـ ensemble | ✅ |

### Flywheel / أول تدريب (2026-08-05)
| بند | الحالة |
|-----|--------|
| جمع عينات حية `dashboard_unified_v1` | ✅ `ml/live_sample_collector.py` |
| Bootstrap قابل للتدريب `market_replay_v1` (ليس historical_seed) | ✅ |
| تصدير Parquet + تدريب baseline منشور | ✅ نموذج `oracle_direction_v20260805_2017` |
| بوابة deploy cold-start + تخطي freeze أثناء bootstrap | ✅ |
| سكربت تشغيل | `scripts/run_flywheel_bootstrap.py` |

### متبقي لاحق (P1)

### P1 — جودة النموذج
1. بوابة deploy للـ ensemble مثل baseline.
2. ختم آفاق 1h/4h عند نضجها الحقيقي لا عند أول poll متأخر.
3. توسيع الميزات: funding spread، basis، whale SII، on-chain netflow.
4. هدف تدريب `verdict_label` بجانب direction.

### P2 — تشغيل وإنتاج
1. تفعيل مسار بيانات مشترك (mirror SQLite/Postgres أو Redis books) بين الحاويات.
2. مواءمة `requirements-prod.txt` مع الاستيرادات الفعلية.
3. Ready checks حقيقية + production_guard fail-closed.

---

## 9) توصية للتصميم المالي

**نعم، يمكن متابعة تصميم النموذج** بعد إصلاحات مسار Oracle/ML الحالية، بشرط:
- اعتبار الوثائق السابقة التي تقول «Phase 0 مكتمل 100%» **مبالغ فيها**
- بناء الميزات والتدريب على taxonomy موحّد للأحكام
- عدم الاعتماد على Postgres/Docker كبيئة تدريب حتى تكتمل migrations ومتطلبات الصورة

---

*تقرير مراجعة هندسية — BLACKDARK. يُحدَّث مع كل جولة إصلاح حرجة.*
