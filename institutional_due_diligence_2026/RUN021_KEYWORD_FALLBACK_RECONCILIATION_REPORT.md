# Run 021 — Keyword Fallback / Foundational Research Reconciliation

**Generated:** 2026-09-11T20:05:00Z  
**Scope:** Batches 01–13 (closed engineering gate review)  
**Orchestrator:** STOPPED — no Batch14+ until this report is accepted  
**Evidence JSON:** `institutional_due_diligence_2026/RUN021_KEYWORD_FALLBACK_RECONCILIATION.json`

## PASS_LIVE (honest ceiling first)

**PASS_LIVE = 0/826** — all audits in `local_dev_vm` only.

---

## البند 1 — فحص `keyword_fallback` في الدفعات المغلقة

### 1.1 نتيجة grep الحرفية

| Pattern | النتيجة |
|---------|---------|
| `keyword_fallback` | **0 matches** في كامل المستودع |
| `KEYWORD_FALLBACK` | **0 matches** |

**لا يوجد identifier حرفي باسم `keyword_fallback` في أي `batch0X_dedicated.py`.**

### 1.2 الآليات المكافئة (ما يقصده البحث التأسيسي)

| الآلية | الموقع | IDs المتأثرة (1–650) | في مسار Run021 audit؟ |
|--------|--------|----------------------|------------------------|
| **`capability_keyword`** | `cap646/backend_registry.py` → `_keyword_binding()` | **144** | **لا** — مسار pdf/production registry؛ يظهر في split-brain free_tier فقط |
| **`invoke_underlying` + keyword routing** | `cap646/batch0X_underlying.py` → `_route_underlying_handler()` | **448** (batch04–12) | **نعم** — هذا هو مسار dedicated في Run021 |
| **`cap646.fallbacks.*`** | `cap646/fallbacks.py` | **3** في batch01 (16, 41, 50) | **نعم** — degraded-data fallbacks صريحة |
| **TEMPLATE-SEED-STUB** | `bd_platform/*_layer.py` → `_base()+_metric()` | **212** (hero evidence 1–650) | **غالبًا لا** — Run021 لا يستدعي الدالة المسماة في الكatalog |

### 1.3 تفصيل batch01 (الدفعة الوحيدة مع fallbacks صريحة)

| ID | الآلية | الفرق حقيقي vs احتياطي |
|----|--------|-------------------------|
| **16** | `source = "ticker_fallback"` عند غياب klines | **حقيقي:** klines 48h → move/vol. **احتياطي:** ticker 24h فقط — نفس الهدف، دقة أقل |
| **41** | `method: "fallback_neutral"` SOPR | **حقيقي:** onchain SOPR proxy. **احتياطي:** ratio=1.0 neutral — **لا يُدّعى SOPR حقيقي** |
| **50** | `cap646.fallbacks.resolve_order_book` | **حقيقي:** live_book_hub WS. **احتياطي:** seed from Binance ticker — spread synth 1bps |

هذه **fallbacks بيانات متدهورة** (مصدر مُوسَم)، وليست **keyword routing** لقدرة مختلفة.

### 1.4 تفصيل batch04–12 (448 IDs — `invoke_underlying` فقط)

كل handler = `payload = await invoke_underlying(N)` بدون منطق goal-specific.

**مثال حي ID 307 (Batch07 — مغلق):**

| المسار | الناتج |
|--------|--------|
| **Run021 dedicated** `invoke_underlying(307)` | `surface=alerts_workflow`, inbox فارغ — handler alerts عام |
| **Catalog function** `smart_alerts_307()` | `smart_alerts=2023.2` — metric من seed (`TEMPLATE-SEED-STUB`) |

**النتيجتان مختلفتان تمامًا.** Run021 يمرّر Phase 1 لأن `success=true` + spine صحيح، لكن **لا ينفّذ لا المنطق الحقيقي ولا الـstub المسمّى** — ينفّذ handler ثالث (keyword-routed generic).

### 1.5 batch02–03 + batch12 custom

| Batch | custom handlers | ملاحظة |
|-------|-----------------|--------|
| 02–03 | 50+50 goal-specific | **لا invoke_underlying** |
| 12 | **584** فقط (Path A risk gate) | 49 IDs = invoke_underlying |
| 04 | **196** فقط custom | 49 IDs = invoke_underlying |

### 1.6 Batch13

| الحالة | التفاصيل |
|--------|----------|
| **غير مغلق** | لا RTM — `ABORT Batch13: closure failed exit=1` |
| dedicated | 50/50 `invoke_underlying` (fixes 647–650 **أُزيلت** بواسطة `generate_batch_scripts` regeneration) |

---

## البند 2 — تسوية الأرقام المتضاربة

### 2.1 جدول المقاييس

| المصدر | الرقم | ماذا يقيس فعليًا |
|--------|-------|------------------|
| **Run021 "600/826 Type A=0"** | 600 IDs في RTM batches 1–12 | **بوابة هندسة:** CS=0 + SB=0 — **ليس** "600 قدرة production-ready" |
| **Run021 RTM v6** | **0** PRODUCTION-ALIGNED / **550** NOT_COMPLETE / **50** PERF-UNV | التصنيف الصادق post-audit |
| **Inventory Sep-01** | **114** PRODUCTION-ALIGNED | **Hero era Aug-30** — **لم يُحدَّث** بعد Run021 v6 |
| **TEMPLATE_STUB manifest** | **311** total | `_base()+_metric()` seed stubs — ≈ "MOCK_OR_STUB" في البحث |
| **Hero evidence** | **212** deferred_template_stub (1–650) | subset مُختبَر في hero batches |
| **Ledger v6** | PARTIAL=550, PASS_ENG=50, PASS_LIVE=**0** | tri-state post batch12 |

### 2.2 هل يتصالحان؟

**نعم — كمقاييس مختلفة. لا — كادّعاء completion واحد.**

```
Run021 "600 مغلقة" = 600 ID اجتازت بوابة Type A (CS+SB=0)
                      ≠ 600 PRODUCTION-ALIGNED
                      ≠ 114 inventory hero classification

Inventory "114 PRODUCTION-ALIGNED" = تصنيف Aug-30 pre-Run021
                                   ≠ Run021 RTM (0 PA في batches 1–12)
```

**Run021 لم يفوت عيبًا في Type A gate** — لكن **Inventory 114 PA stale** و**لم يُسقَط** بعد v6 re-audit.

### 2.3 تفسير "307 MOCK_OR_STUB"

| المرجع | العدد |
|--------|-------|
| TEMPLATE_STUB manifest | **311** |
| Hero deferred_template_stub (1–650) | **212** |
| ID **307** | exemplar — `smart_alerts_307` = seed metric 2023.2 |

"307" في البحث التأسيسي = **فئة MOCK_OR_STUB (~311)** أو **ID 307 كنموذج** — ليس count Run021.

---

## البند 3 — هل الدفعات "مغلقة زورًا"؟

### 3.1 بمعيار v6 الحالي (Type A gate)

| الدفعة | CS | SB | PA in RTM | حكم |
|--------|----|----|-----------|-----|
| 01–12 | 0 | 0 | **0** | **إغلاق هندسي صادق** — NOT_COMPLETE مُقرّ |
| 13 | — | — | — | **غير مغلق** |

**لا إعادة فتح إلزامية** لـ Type A=0 under v6 — RTM لا يدّعي PA.

### 3.2 بمعيار "دليل حي حقيقي ≠ keyword/generic routing"

| الدفعة | IDs generic delegate | حكم |
|--------|---------------------|-----|
| **01–03** | 0 (custom) + 3 explicit data fallbacks | **لا keyword_fallback routing** |
| **04–12** | **448** invoke_underlying | **دين هيكلي** — generic handler ≠ catalog goal |
| **13** | 50 (غير مغلق) | — |

**التوصية:**

- **لا إعادة فتح wholesale** لـ batch01–03 أو batch12 (584 Path A).
- **Batch04–12:** 448 IDs تحتاج **استبدال invoke_underlying** بمنطق goal-specific (Path A) أو توثيق Path B صريح — **قبل** ادّعاء PASS_ENGINEERING أعلى من PARTIAL.
- هذا **تحسين gate** وليس invalidate CS=0 الحالي.

---

## البند 4 — شروط استئناف Batch14+

**STOP حتى:**

1. ✅ هذا التقرير مُسلَّم
2. ⬜ إضافة Phase 1 gate: `scan_keyword_fallback()` في audit scripts
3. ⬜ تحديث Inventory 114 PA → v6 ledger (supersede stale Sep-01)
4. ⬜ إصلاح `generate_batch_scripts` لعدم مسح CONCEPTUAL_FLAGS / custom handlers

**Gate مقترح Phase 1 (إلزامي من Batch14):**

```python
def phase1_no_generic_delegate(cid, dedicated_source: str) -> tuple[str, str|None]:
    if "invoke_underlying" in dedicated_source and cid not in ALLOWED_DELEGATE_IDS:
        return "FAIL", "GENERIC_DELEGATE: invoke_underlying keyword routing — not goal-specific"
    if "capability_keyword" in binding_source:
        return "FAIL", "KEYWORD_BINDING: backend_registry capability_keyword fallback"
    return "PASS", None
```

---

## ملخص تنفيذي (5 أسطر)

1. **`keyword_fallback` حرفيًا: 0** — المكافئ = `capability_keyword` (144 ID) + `invoke_underlying` routing (448 ID batch04–12).
2. **Run021 600/826 = Type A gate** (CS+SB=0) — **0 PRODUCTION-ALIGNED** في RTM؛ Inventory 114 PA = **stale Aug-30**.
3. **311 TEMPLATE_STUB ≈ MOCK_OR_STUB** — Run021 لا ينفّذها؛ ينفّذ handlers عامة مختلفة.
4. **Batch01–03 + batch12/584: OK** — batch04–12: **448 IDs generic delegate debt**.
5. **Orchestrator STOPPED** — Batch13 غير مغلق — **لا Batch14+** حتى gate Phase 1 يُدمج.
