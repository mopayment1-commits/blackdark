# CLOSURE-MANDATE-VERIFY — تقرير تصحيحي (3 بنود)

**Audit ID:** `CLOSURE_MANDATE_VERIFY`  
**Commit (baseline):** `4f928ced2ce340a0b1e6fd451b822d2b768f5f90`  
**Branch:** `cursor/closure-mandate-verify-e85e`  
**Checksum المحدَّث:** `d3702d7f17518687` (82 صف قفل + 11 بند = 93 قسمًا)

---

## القسم 1 — سلامة دليل gate-full (Evidence Provenance)

### 1.1 الطوابع الزمنية للتشغيلين السابقين (تعارض مُثبت)

| التشغيل | الأمر الفعلي | الطابع الزمني (UTC) | commit عند التشغيل |
|---|---|---|---|
| **(أ) gate-full** | `python -m pytest tests/cap646/test_institutional_gate.py::test_institutional_gate_full -q --tb=no` | **2026-09-02 00:15:11** (mtime `GATE_FULL_LAST_EVIDENCE.txt`) | `4f928ce` (نفس الشجرة — قبل الالتزام بـ 2 دقيقة) |
| **(ب) orchestrator** | `python scripts/run_closure_mandate_last.py --skip-gate-full` | **2026-09-01 23:50:09** (`CLOSURE_MANDATE_LAST_AUDIT.json` `generated_at`) | pre-commit working tree → لاحقًا `4f928ce` عند الالتزام **00:17:37** |

**الفارق الزمني:** ~25 دقيقة بين (ب) و(أ) — **جلستان منفصلتان**.  
**تغيّر commit بينهما:** لا على الشجرة النهائية (كلاهما أُدرج في `4f928ce`)، لكن **سلسلة الحيازة مكسورة**: التقرير عرض EXIT:0 من (أ) بينما الأوركستريتور في (ب) لم يُشغّل gate في نفس الجلسة.

**الحكم (IEEE 1028 / SLSA):** دليل EXIT:0 السابق **غير قابل للتحقق كجزء من تشغيل الأوركستريتور** — مرفوض كإثبات مُقترن بتقرير `--skip-gate-full`.

### 1.2 إعادة التشغيل المطلوبة (هذه الجلسة — مُحقَّق)

| الحقل | القيمة |
|---|---|
| **الأمر** | `/workspace/.venv/bin/python -m pytest tests/cap646/test_institutional_gate.py::test_institutional_gate_full -q --tb=no` |
| **commit_hash** | `4f928ced2ce340a0b1e6fd451b822d2b768f5f90` |
| **started_at_utc** | `2026-09-02T00:27:55.786556+00:00` |
| **finished_at_utc** | `2026-09-02T00:46:07.618854+00:00` |
| **elapsed_seconds** | 1091.8 |
| **exit_code** | **0** |

**سلسلة الحيازة (SLSA):** `docs/GATE_FULL_PROVENANCE.json` + `docs/GATE_FULL_LAST_EVIDENCE.txt` — نفس الجلسة، نفس commit، طابع زمني مُسجَّل.

### 1.3 إزالة `--skip-gate-full`

**مطبَّق:** `scripts/run_closure_mandate_last.py` — أي استخدام لـ `--skip-gate-full` يُرجع **exit code 2** ورسالة خطأ صريحة. لا تسليم صامت.

**بديل مُعتمد:** `scripts/run_gate_full_provenance.py` — gate-full مع attestation مستقل عند الحاجة.

---

## القسم 2 — التكرار الجديد (batch01_dedicated intra-module)

### 2.1 Root Cause — Five Whys

| # | لماذا؟ |
|---|---|
| 1 | لماذا ظهرت 3 clones بعد إغلاق القسم صفر؟ → لأن بند 9 (jscpd) استخدم نطاقًا أوسع من نطاق القفل |
| 2 | لماذا لم تُدرج في جدول 79 صفًا؟ → `build_lock_table()` لم يفحص jscpd intra-module لـ `batch01_dedicated.py` |
| 3 | هل سببها commit `4f928ce`؟ → **لا** — `batch01_dedicated.py` **لم يُعدَّل** في ذلك الالتزام |
| 4 | هل `dedicated_common.py` أدخلها؟ → **لا** — الاستخراج طال batch02/03 فقط |
| 5 | **السبب الجذري** | **عيب نطاق/ترتيب عملية**: القسم صفر أُغلق على R0801 + clones عابرة للملفات؛ jscpd intra-module batch01 أُبلغ لاحقًا في التحقق الختامي دون إعادة فتح القفل |

### 2.2 تصنيف الثلاثة — **تم الإزالة بالكود (Eliminate)**

| # | المواقع الأصلية | Roy & Cordy | TIME | الحالة |
|---|---|---|---|---|
| 1 | `#7↔#9` holder_analytics | **Type 3** (gapped) | **Eliminate** | `holder_analytics_bundle()` + `holder_analytics_footer()` |
| 2 | `#8↔#9` metrics extraction | **Type 3** (gapped) | **Eliminate** | `holder_analytics_locked()` + `holder_analytics_footer(extra=...)` |
| 3 | `#15↔#44` exchange_netflow | **Type 3** (gapped) | **Eliminate** | `exchange_netflow_probe()` + `exchange_netflow_footer(flow_payload_key=...)` |

**إجابة السؤال التصحيحي (1):** نعم — تم تعديل الكود فعليًا (Extract Function + Parameterize Function)، وليس توثيق Invest فقط.

| الدالة المشتركة | المسار | السطور |
|---|---|---|
| `holder_analytics_bundle` | `cap646/dedicated_common.py` | **74–80** |
| `holder_analytics_footer` | `cap646/dedicated_common.py` | **83–103** |
| `holder_analytics_locked` | `cap646/dedicated_common.py` | **106–110** |
| `exchange_netflow_probe` | `cap646/dedicated_common.py` | **113–119** |
| `exchange_netflow_footer` | `cap646/dedicated_common.py` | **122–142** |

Handlers المُحدَّثة في `cap646/batch01_dedicated.py`: `_cap007_holder_distribution`, `_cap008_top_holders_concentration`, `_cap009_distribution_score`, `_cap015_exchange_flow_intelligence`, `_cap044_exchange_balance_netflow`.

### 2.3 jscpd بعد الإصلاح (السؤال 2)

```text
npx jscpd cap646/batch01_dedicated.py --min-lines 5 --min-tokens 50
→ Found 0 clones. (1413 lines, 8539 tokens, 0 duplicated)
```

الأثر الكامل: `/opt/cursor/artifacts/jscpd_batch01_dedicated_after_refactor.txt`

### 2.4 جدول القفل المحدَّث

- **قبل:** 79 صفًا — checksum `993af4355bd3e6c6`
- **بعد Invest (مرفوض):** 82 صفًا — checksum `d3702d7f17518687`
- **بعد Eliminate (نهائي):** **82 صفًا** — TIME=Eliminate للثلاثة — checksum مُحدَّث في `docs/DUPLICATION_LOCK_TABLE_1_100.json`
- **SSOT:** `docs/DUPLICATION_LOCK_TABLE_1_100.json`

---

## القسم 3 — تصحيح رقم batch04–17

### 3.1 التصحيح

| البيان | القيمة الصحيحة |
|---|---|
| عدد قدرات batch04–batch17 | **676** (ليس 700) |
| تحقق MECE | 100 × 676 = **67,600** زوج ✓ |

### 3.2 مصدر الرقم الخاطئ "700"

**تقدير سريع غير مُتحقَّق:** `14 batches × 50 = 700`  
**لم يُراعِ:** `batch17` يحتوي **26** قدرة فقط (IDs 801–826)، وليس 50.

| Batch | Count |
|---|---:|
| batch04–batch16 | 50 each (13×50 = 650) |
| batch17 | 26 |
| **Σ** | **676** |

**ملفات مُصحَّحة:** `docs/CLOSURE_MANDATE_LAST_REPORT.md`, `scripts/run_closure_mandate_last.py` (`total_hero_capabilities`), `docs/CLOSURE_MANDATE_LAST_AUDIT.json` (عند إعادة التوليد).

---

## البند 9 — الإغلاق

يبقى معلقًا على إجراء المالك فقط:
1. SONAR_TOKEN في CI  
2. دمج main  
3. توقيع HMAC  
4. countersignature على `docs/ACCEPTED_RISK_REGISTRY.json` (خصوصًا B110×3)
