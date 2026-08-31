# SPLIT_BRAIN_ROUTING — severity classification (144 capabilities)

**Generated:** 2026-08-31 UTC  
**Method:** Static trace (`cap646`/`api` import chain) + live `execute_capability` vs `pdf_capability_registry` on 10-sample panel.

---

## 1) Executive classification (all 144)

| Class | Count | % | Meaning | Same risk as #311? |
|-------|------:|--:|---------|-------------------|
| **A — Audit code NOT executed in production** | **142** | **98.6%** | دالة التدقيق الموثّقة **لا تُستدعى** عبر `cap646/runtime` → `backend_executor` → `resolve_binding` ولا عبر `cap646/handlers/*` | **نعم — نزاهة تدقيق** (ادّعاء ≠ تنفيذ) |
| **B — Same module, different entrypoint** | **2** | **1.4%** | `#396`, `#528` — نفس العائلة (`news_classifier`) لكن entrypoint مختلف | **جزئيًا** — أقرب لـ «توثيق خاطئ لمسار صحيح» |
| **C — Audit fn referenced in cap646/api** | **0** | **0%** | لا توجد حالة يُستدعى فيها audit binding من سلسلة الإنتاج | — |

### جواب مباشر على السؤال 1

**SPLIT_BRAIN_ROUTING ليس في الغالب «توثيق خاطئ لنفس الكود».**

- في **~99%** من الحالات: **كود التدقيق موجود** (ويعمل في `pdf_capability_registry`/الاختبارات) لكن **لا يُنفَّذ في الإنتاج** عند `GET /api/cap646/{id}`.
- الإنتاج يشغّل **backend مختلفًا** عبر `cap646/backend_registry.py` (keyword / track / gap_matrix / handler مخصص).
- **الفرق عن #311:** الإنتاج لا يعيد seed metrics مزيفة؛ يعيد **payload حقيقي من backend آخر** — غالبًا **مجال وظيفي مختلف** عن اسم القدرة في الكتالوج.
- **الخطورة:** **نزاهة تدقيق/ادّعاء VERIFIED-DEEP** = خطورة عالية (مثل #311). **تأثير المستخدم** = متفاوت: من «الإنتاج أصح من التدقيق» (#49) إلى «نتيجة خاطئة تمامًا» (#409, #517).

### تمييز صريح

| النمط | الوصف | 144-split |
|-------|--------|-----------|
| **توثيق خاطئ لمسار صحيح** | نفس الدالة تُنفَّذ لكن التوثيق يذكر module/entrypoint آخر | **~2 IDs فقط** |
| **تدقيق لكود لا يُنفَّذ فعليًا** | الدالة الموثّقة لا تُستدعى في الإنتاج؛ backend آخر يُنفَّذ | **~142 IDs** |

---

## 2) Ten-sample panel (live evidence)

See runtime comparison in session logs; summary:

| ID | Catalog name | Audit binding | Production binding | Audit called in prod? | User outcome |
|----|--------------|---------------|-------------------|----------------------|--------------|
| 2 | Wallet Profiler | `trade_simulator.simulate_spot_trade` | `bd_platform.free_tier_capabilities.wallet_profiler` | **NO** | **Different/wrong** — simulation ≠ profiler |
| 18 | Custom Wallet Labels | `alert_orchestration.alert_orchestration_status_18` | `cap646.handlers.onchain` → on-chain context | **NO** | **Wrong** — not wallet labels |
| 49 | Options Intelligence Suite | `flash_crash_protection.flash_crash_protection_status_49` | `cap646.handlers.verified` → `options_fetcher.fetch_options_overview` | **NO** | **Production closer to catalog name** than audit |
| 59 | Personalized Research Dashboards | `legal_commercial_layer.create_sar_workflow_59` | `cap646.handlers.ai` | **NO** | **Wrong** |
| 60 | Metric-Based Smart Alerts | `legal_commercial_layer.pricing_transparency_manifest_60` | `cap646.handlers.alerts` | **NO** | **Partial/wrong** — generic alerts |
| 101 | AI Data Analyst / Ask AI | `infra_intelligence_layer.validate_oracle_freshness_101` | `cap646.handlers.ai` | **NO** | **Partial** — AI generic, not freshness |
| 201 | Network Growth Intelligence | `derivatives_ta_research_layer.quantitative_analysis_framework_201` | `cap646.handlers.market` → canonical layer | **NO** | **Wrong** |
| 316 | Idea/Chart Sharing | `sse_stream.sse_digest_status_316` | `tradingview_bridge.chart_config` | **NO** | **Wrong** — chart config ≠ SSE digest |
| 409 | Unlocks | `quicktake_feed.quicktake_feed_status_409` | `cap646.handlers.onchain` | **NO** | **Wrong** — news feed ≠ unlocks |
| 517 | FIX Connectivity | `comparison_engine.run_comparison_engine` | `data_lake.lake_status` | **NO** | **Wrong** — lake status ≠ FIX |

**Panel result:** 0/10 يُنفِّذ audit binding في الإنتاج. 8/10 نتيجة مستخدم **خاطئة أو مختلفة جوهريًا**. 1/10 (#49) الإنتاج **أقرب للصواب** من التدقيق. 1/10 (#60) **جزئي**.

---

## 3) Recommended decision (pre-merge)

1. **تعليق ادّعاءات VERIFIED-DEEP** على الـ144 حتى ربط صريح في `backend_registry` أو إعادة تصنيف.
2. **لا يُعتبر SPLIT_BRAIN «مقبولًا توثيقيًا»** — يحتاج نفس مستوى جدية #311 لكن بخطة إصلاح مختلفة (ربط registry وليس إعادة بناء 144 دفعة واحدة).
3. **Option A للـ311 (#338,#500,#507,#534)** يبقى معتمدًا لكن **لا يُغلق SPLIT_BRAIN العام** — يعالج 4 IDs فقط.
