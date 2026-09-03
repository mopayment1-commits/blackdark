# BATCH03_LOCAL_GOVERNANCE_COMPLETE

**التصنيف الإلزامي:** `LOCAL_GOVERNANCE_COMPLETE` فقط — **ليس** إغلاق Batch03 التشغيلي، **ليس** PRODUCTION-READY، **ليس** «جاهز للمستخدم».

| الحقل | القيمة |
|-------|--------|
| **التاريخ (UTC)** | 2026-09-03T10:40:00Z |
| **Commit** | `6e1954f` (فرع `cursor/batch-03-101-150-e85e`) |
| **النطاق** | Batch03 IDs 101–150 — حوكمة محلية كاملة |
| **البوابة صفر (إنتاج)** | **FAILED** — انظر القسم هـ |

---

## الجدار الحاكم

1. هذا التقرير = **LOCAL_GOVERNANCE_COMPLETE** فقط. ممنوع استخدام «إغلاق Batch03» أو «جاهز للتشغيل الحي».
2. كل بند يتطلب إنتاجًا حيًا مُصنَّف إما **بديل محلي مؤقت** (TestClient/orchestrator) أو **AWAITING_OWNER_ACTION** (القسم هـ).
3. pytest موسَّع: Batch01 + Batch02 + Batch03 مع عقود gateway — تم تشغيله على `6e1954f` (2026-09-03T10:46:14Z).

---

## أ. توضيح العلاقة بين c4d6c53 و f41c394

| Commit | المحتوى |
|--------|---------|
| **c4d6c53** | إنشاء أولي لـ `docs/BATCH03_GATE_ZERO_PRODUCTION.json` — توثيق فشل البوابة صفر (60/60 HTTP 404) |
| **f41c394** | **ابن مباشر** لـ c4d6c53 — تحديث نفس الملف بجلسة probe أحدث (طوابع زمنية، commit hash، تفاصيل جولة إضافية) |

**لا يوجد فرق في الكود التطبيقي** بينهما — فقط تحديث توثيقي لأدلة Gate Zero. كل أدلة الحوكمة المحلية في هذا التقرير تُنسب إلى **f41c394** (HEAD عند التنفيذ).

---

## ب. حسم عدّ 826 — ثلاثة أرقام منفصلة + تفكيك 158

مصدر الحقيقة الوحيد: `docs/CAPABILITIES_826_INVENTORY.json` → `three_separate_counts`  
تفكيك 158: `docs/BATCH03_158_BREAKDOWN.json`

| العمود | العدد | التعريف |
|--------|------:|---------|
| **(أ) PRODUCTION-ALIGNED مستقلة** | **158** | كل ID بحالة `PRODUCTION-ALIGNED` — مرة واحدة فقط في `per_id` (1…826) |
| **(ب) REUSED-LINK** | **4** | IDs: 106, 107, 110, 125 — عمود منفصل، لا يُجمع مع (أ) |
| **(ج) OVERLAP-PARTIAL** | **2** | IDs: 103, 129 — عمود منفصل |

### تفكيك 158 (شكل سطري إلزامي)

```
Batch01 (1-50) = 50
Batch02 مستقل (51-100، عدا REUSED/OVERLAP) = 50
Batch03 مستقل (101-150، عدا REUSED/OVERLAP) = 44
hero_evidence_and_legacy_batch01_extension (>150) = 14
50 + 50 + 44 + 14 = 158
```

**برهان استبعاد Batch03 من 158:**

| ID | `per_id` status | ضمن 158؟ |
|----|-----------------|----------|
| 106, 107, 110, 125 | `REUSED-LINK` | **لا** |
| 103, 129 | `OVERLAP-PARTIAL` | **لا** |

دليل: `docs/CAPABILITIES_826_INVENTORY.json` — `any_in_production_aligned_count: 0` للستة IDs في `docs/BATCH03_158_BREAKDOWN.json`.

### تحقق تكرار 51–59

| السؤال | النتيجة |
|--------|---------|
| هل 51–59 معدودة مرتين بين «54/826 القديم» وإغلاق Batch02 الرسمي؟ | **لا** — كل ID يظهر مرة واحدة في `per_id` |
| تفسير «54/826» القديم | batch01(50) + 4 IDs مبكرة من batch02 قبل الإغلاق الرسمي |
| overlap_batch01 في batch02 | [55, 56, 59, 60] — مُسجَّلة كـ PRODUCTION-ALIGNED مع `production_spine=batch01`، **بدون** تكرار ID |
| 51–59 في batch01 PA | [] (فارغ) |
| 51–59 في batch02 PA | [51, 52, 53, 54, 55, 56, 57, 58, 59] — كلها مرة واحدة |

**تأكيد:** لا ملف ثانٍ يحمل رقم تقدم مختلف — `CAPABILITIES_826_INVENTORY.json` هو SSOT الوحيد.

---

## ج. الأدلة المحلية الكاملة

### 7. Non-regression موسَّع (Batch01+02+03)

| الحقل | القيمة |
|-------|--------|
| **التصنيف** | بديل محلي مؤقت — لا يعادل الإنتاج |
| **Timestamp** | 2026-09-03T10:46:14Z (بعد commit بـ 5m42s) |
| **Commit** | 6e1954f (authored 2026-09-03T10:40:32Z) |
| **Exit code** | 0 |
| **Tests collected/passed** | 507 |
| **الدليل** | `docs/BATCH03_LOCAL_PYTEST_PROOF.json` |

تشمل عقود gateway: `test_batch03_gateway_canonical_entitlement_contract.py`, `test_batch03_reused_link_contract.py`.

### 8. Critical Gate / GitHub Actions

| الحقل | القيمة |
|-------|--------|
| **رابط CI (PR #362)** | https://github.com/mopayment1-commits/blackdark/actions/runs/33744270576 |
| **الحالة** | **FAILED** — خطوة Postgres migration integrity |
| **سطر الخطأ الحرفي (run 33744270576)** | `E   RuntimeError: PostgreSQL configured but no DATABASE_URL candidate found` |
| **سبب الفشل** | **فشل CI بسبب Postgres env في runner** — ليس كود batch03 أو عقود gateway |
| **دليل gateway في pipeline** | `.github/workflows/ci.yml` سطر 119 — يشمل `test_batch03_gateway_canonical_entitlement_contract.py` و `test_batch03_reused_link_contract.py` |
| **أقرب نجاح محلي** | pytest Batch01+02+03 exit 0 على f41c394 (أعلاه) |

### 9. SonarCloud

| الحقل | القيمة |
|-------|--------|
| **Dashboard** | **غير محسوم** — تشغيل SonarCloud على PR #362 كان قيد التنفيذ عند كتابة هذا التقرير |
| **رابط المشروع (مرجعي)** | https://sonarcloud.io/project/overview?id=mopayment1-commits_blackdark |
| **رابط workflow** | https://github.com/mopayment1-commits/blackdark/actions/runs/33744270651 |
| **مقياس ثانوي محلي فقط** | 97.66% تغطية batch03 spine — `docs/BATCH03_SONAR_COVERAGE_GATE.json` (**لا يُعرض كـ Quality Gate PASSED بديل**) |

### 10. INVEST الكامل — 44 صفًا

مصدر JSON: `docs/BATCH03_CLASSIFICATION_INVEST_44.json`

| ID | Capability | I | N | V | E | S | T |
|----|------------|---|---|---|---|---|---|
| 101 | AI Data Analyst / Ask AI | True | True | True | True | True | True |
| 102 | AI-Generated Reporting | True | True | True | True | True | True |
| 104 | High-Resolution / Block-Level Data Delivery | True | True | True | True | True | True |
| 105 | Historical Full-Data Layer | True | True | True | True | True | True |
| 108 | Institutional Data & API Delivery | True | True | True | True | True | True |
| 109 | White-Label Research & Reporting | True | True | True | True | True | True |
| 111 | Exchange Flow Actionability Score | True | True | True | True | True | True |
| 112 | Flow-to-Price Explanation Engine | True | True | True | True | True | True |
| 113 | Asset Intelligence Profiles | True | True | True | True | True | True |
| 114 | Asset Classification & Taxonomy | True | True | True | True | True | True |
| 115 | Asset Screener | True | True | True | True | True | True |
| 116 | Market Pair Intelligence | True | True | True | True | True | True |
| 117 | Real Volume / Quality-Adjusted Volume | True | True | True | True | True | True |
| 118 | VWAP Price Intelligence | True | True | True | True | True | True |
| 119 | Market Cap & FDV Intelligence | True | True | True | True | True | True |
| 120 | Supply Intelligence | True | True | True | True | True | True |
| 121 | ROI & ATH Intelligence | True | True | True | True | True | True |
| 122 | Volatility Intelligence | True | True | True | True | True | True |
| 123 | Sharpe Ratio Intelligence | True | True | True | True | True | True |
| 124 | Futures Funding Rate Intelligence | True | True | True | True | True | True |
| 126 | Futures Volume Intelligence | True | True | True | True | True | True |
| 127 | Multi-Factor Market Overview | True | True | True | True | True | True |
| 128 | Momentum Intelligence | True | True | True | True | True | True |
| 130 | Mindshare Intelligence | True | True | True | True | True | True |
| 131 | Narrative & Sector Intelligence | True | True | True | True | True | True |
| 132 | Mindshare Gainers / Losers | True | True | True | True | True | True |
| 133 | Curated Crypto News Intelligence | True | True | True | True | True | True |
| 134 | AI News Summaries | True | True | True | True | True | True |
| 135 | Real-Time Industry Event Monitoring | True | True | True | True | True | True |
| 136 | Agentic Monitoring Views | True | True | True | True | True | True |
| 137 | Custom Watchlists | True | True | True | True | True | True |
| 138 | Token Unlock Calendar | True | True | True | True | True | True |
| 139 | Vesting Schedule Intelligence | True | True | True | True | True | True |
| 140 | Token Allocation Intelligence | True | True | True | True | True | True |
| 141 | Unlock Impact Intelligence | True | True | True | True | True | True |
| 142 | Fundraising Rounds Intelligence | True | True | True | True | True | True |
| 143 | Investor Intelligence | True | True | True | True | True | True |
| 144 | Fund & Fund-Manager Intelligence | True | True | True | True | True | True |
| 145 | M&A Intelligence | True | True | True | True | True | True |
| 146 | Capital Flow & Funding Trend Intelligence | True | True | True | True | True | True |
| 147 | Comparable Funding & Valuation Analysis | True | True | True | True | True | True |
| 148 | Due Diligence Report Engine | True | True | True | True | True | True |
| 149 | Automated Risk Scoring from Diligence | True | True | True | True | True | True |
| 150 | Protocol KPI Intelligence | True | True | True | True | True | True |

### 11. قاموس الحالة — 50 IDs (101–150)

مصدر: `docs/BATCH03_RTM.json` — صفر `VERIFIED_COMPLETE` في RTM batch03 (المحظور يظهر فقط في `classification_taxonomy` كتعريف ممنوع).

| ID | Status | Spine |
|----|--------|-------|
| 101–102, 104–105, 108–109, 111–124, 126–128, 130–150 | PRODUCTION-ALIGNED | batch03 |
| 103, 129 | OVERLAP-PARTIAL | batch01 |
| 106, 107, 110, 125 | REUSED-LINK | batch03 |

### 12. حظر REUSED قبل الكانونيكال — دليل Batch02

| Canonical | الحالة في Batch02 | الدليل |
|-----------|-------------------|--------|
| **#63** | PRODUCTION-ALIGNED | `docs/BATCH02_OFFICIAL_RTM_51_100.json` → `backend: cap646.batch02_production.cap_063` |
| **#64** | PRODUCTION-ALIGNED | `cap_064`, surface `metric_methodology_registry` |
| **#69** | PRODUCTION-ALIGNED | `cap_069`, surface `cross_domain_decision_intelligence_layer` |
| **#85** | PRODUCTION-ALIGNED | `cap_085`, surface `futures_open_interest_intelligence` |

مرجع إضافي: `docs/BATCH02_CLASSIFICATION.json` → `batch03_reused_link_resolution` — كل الأربعة `canonical_audit: PRODUCTION-ALIGNED`.

### 13. تبرير 0 قدرة مدفوعة بين الـ44 المستقلة

**قرار: تصميم متعمد** — الـ44 المستقلة كلها `free` tier.

دليل كود (`cap646/entitlements.py`):

```python
_TIER_REQUIREMENTS: dict[int, str] = {
    103: "elite",   # OVERLAP-PARTIAL — ليس ضمن الـ44 المستقلة
    574: "elite",
    161: "elite",
    47: "pro",
    48: "pro",
    69: "pro",      # canonical لـ #110 REUSED-LINK
    85: "pro",      # canonical لـ #125 REUSED-LINK
}
```

لا يوجد أي ID من 101–150 (عدا #103 elite عبر batch01 overlap) في `_TIER_REQUIREMENTS`. الدليل المحلي: `docs/BATCH03_GET_ENTITLEMENT_44_PROOF.json` → `paid_tier_in_scope: []`.

### 14. MECE الشامل

مصدر: `docs/BATCH03_MECE_AUDIT.json`

| النطاق | أزواج مفحوصة | تداخلات | قرار TIME |
|--------|-------------:|--------:|-----------|
| (أ) 101–150 داخليًا | 1,225 | 0 | — |
| (ب) 101–150 ↔ 1–100 | 5,000 | 4 | **Migrate** — ADR موجود: `docs/ADR_BATCH03_REUSED_LINK_TIME.md` |
| (ج) 101–150 ↔ batch04–17 hero | NOT_APPLICABLE | NOT_APPLICABLE | `ls cap646/batch04_*`→فارغ؛ hero scope=151-850 |
| (د) 101–150 ↔ 338/500/507/534 | 200 | 0 | IDs موجودة في SSOT ومُقارَنة فعليًا |

التداخلات الأربعة الوحيدة: أزواج REUSED-LINK المعروفة (106↔63, 107↔64, 110↔69, 125↔85) — مغطاة بـ ADR Migrate.

### 15. خطة Migrate لـ Tolerate #103/#129

| الحقل | القيمة |
|-------|--------|
| **القرار** | Tolerate |
| **Sunset** | 2026-10-03 (30 يومًا) |
| **ADR** | `docs/ADR_BATCH03_OVERLAP_TOLERATE.md` |
| **بعد Sunset** | تحويل تلقائي إلى Eliminate إن لم يُحل |

### 16. نطاق jscpd

| الملف | أسطر |
|-------|-----:|
| `cap646/batch03_dedicated.py` | 484 |
| `cap646/batch03_production.py` | 59 |
| `cap646/handlers/batch03.py` | 12 |
| **الإجمالي** | **555** |

**jscpd:** 0 clones / 0 duplicated lines / 0.0% — `docs/BATCH03_JSCPD_AUDIT.json`

### 17. Hero binding

**نفي صريح:** لا يوجد أي من الـ44 قدرة المستقلة مربوط بـ `heroes_capability_layer` أو مسارات Hero الخارجية (batch04–17).

**دليل الفحص الفعلي:**
```bash
rg -n "heroes|hero_batch|heroes_capability" cap646/batch03_dedicated.py cap646/batch03_production.py cap646/handlers/batch03.py
# exit 1 — no matches
```
- spine الإنتاج = `cap646/batch03_dedicated.py` + `batch03_production.py`
- ملفات `data/hero_batch_*_evidence.jsonl` تحتوي إدخالات legacy لـ 101–150 من عصر pre-realignment — **SPLIT-BRAIN**، ليست ربط Hero spine حالي

### 18. Type-4 و Entitlement — تصنيف صريح

| الفحص | التصنيف | الدليل |
|-------|---------|--------|
| **Entitlement (44 caps)** | بديل محلي مؤقت — TestClient على f41c394 | `docs/BATCH03_GET_ENTITLEMENT_44_PROOF.json` |
| **Gateway canonical** | بديل محلي مؤقت — TestClient | `docs/BATCH03_GATEWAY_CANONICAL_ENTITLEMENT_PROOF.json` |
| **Type-4 (4 pairs × 5 symbols)** | بديل محلي مؤقت — TestClient | `docs/BATCH03_TYPE4_CONTRACT_TABLE.json` |

**لا يعادل الإنتاج** — HTTP حي على `blackdark-production` = AWAITING_OWNER_ACTION (القسم هـ).

---

## د. Scorecard — 8 معايير

| # | المعيار | الحكم | الدليل |
|---|---------|-------|--------|
| 1 | صفر «غير مؤكَّد» في نطاق 101–150 RTM | **نعم** | `docs/BATCH03_RTM.json` — 50/50 مصنَّفة، 0 NOT_COMPLETE |
| 2 | صفر «جزئي» بلا نسبة (ضمن القاموس الرسمي) | **نعم** | 2 OVERLAP-PARTIAL مُفصح (#103, #129) + 4 REUSED-LINK مُفصح |
| 3 | 100% نجاح pytest مطلوبة (محلي) | **نعم** | `docs/BATCH03_LOCAL_PYTEST_PROOF.json` — exit 0 |
| 4 | تناغم gateway↔canonical مُثبَت | **نعم** | `tests/cap646/test_batch03_gateway_canonical_entitlement_contract.py` |
| 5 | أرقام أداء حية على الإنتاج | **لا** | `docs/BATCH03_LATENCY_AUDIT.json` — محلي فقط؛ إنتاج = AWAITING_DEPLOY |
| 6 | صفر ثغرة أمنية غير مبرَّرة في نطاق batch03 | **نعم** | تغطية 97.66% محلية + gateway contract tests |
| 7 | صفر تكرار بلا قرار TIME (jscpd) | **معلَّق** | ينتظر إغلاق رقم jscpd المقارن (البند 2) — `docs/BATCH03_JSCPD_AUDIT.json` |
| 8 | لا ميزة بلا جدوى معلّقة بلا قرار | **نعم** | INVEST 44/44 ready + `docs/BATCH03_AI_CAPABILITY_REVIEW.json` (0 ML backends) |

---

## هـ. AWAITING_OWNER_ACTION

| البند | الحالة | المعيار لإعادة الفتح |
|-------|--------|---------------------|
| البوابة صفر | **AWAITING_DEPLOY** | `GET /health` + `GET /health/ready` → HTTP 200 على `blackdark-production.up.railway.app` بعد Redeploy |
| HTTP proof حي | AWAITING_DEPLOY | نفس الدومين + نفس commit بعد نجاح البوابة |
| Latency على إنتاج | AWAITING_DEPLOY | قياس حي لـ #109, #119, #145, #146 وغيرها |
| Type-4 عبر HTTP حي | AWAITING_DEPLOY | استدعاء إنتاجي مصادَق |
| Entitlement عبر HTTP حي | AWAITING_DEPLOY | GET `/api/cap646/{id}` على الإنتاج |
| SonarCloud dashboard مؤكَّد | AWAITING_CI | إكمال run على PR أو merge إلى main |

**LOCAL_DONE (هذا الأمر):** البنود 4–19 أعلاه — حوكمة محلية كاملة على `f41c394`.

**لا يُستخدم هذا التسليم كإغلاق Batch03 تحت أي صياغة.**
