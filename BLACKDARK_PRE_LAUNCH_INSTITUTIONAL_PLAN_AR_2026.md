# خطة الإكمال المؤسسي قبل الإطلاق الحي — BLACKDARK 2026

**التاريخ:** 11 سبتمبر 2026  
**النطاق:** 826 قدرة · 12 ملفًا حاكمًا · بوابات G1–G10  
**الهدف الذي طلبته:** كل قدرة وميزة **مبنية ومكتملة** وتحقق غرضها التصميمي — **قبل** الرفع على Railway أو أي بيئة حية

---

## 1. تعريف «جاهز قبل الإطلاق» (وليس «جاهز للإطلاق الحي»)

| الحالة | المعنى | هل نرفع Railway؟ |
|--------|--------|------------------|
| **Runtime PASS** | `execute_capability` يرجع `success=True` | لا يكفي وحده |
| **PASS_ENGINEERING** | كود + اختبارات + سجل صادق | مطلوب قبل الإطلاق |
| **PASS_LIVE** | دليل إنتاج فعلي (متصفح، webhooks، PG) | **بعد** Railway staging |
| **ASSURANCE_READY** | pentest + تراخيص + SOC2 إن لزم | قبل عملاء مؤسسيين |

**قاعدة v6:** لا `PASS_LIVE` من اختبارات محلية فقط.  
**قاعدة المالك:** لا Railway حتى `PRE_LAUNCH_GATE_ASSESSMENT.json` → `pre_launch_ready: true`.

---

## 2. حالة البوابات G1–G10 (صادقة — سبتمبر 2026)

| البوابة | الحالة | ما ينقص |
|---------|--------|---------|
| **G1** Truth Baseline | **PARTIAL** | السجل الرئيسي: ~114 PRODUCTION-ALIGNED في inventory مقابل 716 MOCK/STUB في master |
| **G2** Deduplication | **PARTIAL** | 49 REUSED-LINK — تم إصلاح توجيه duplicate (مثال cap 206→86) |
| **G3** Split-Brain | **PARTIAL** | 58 ID — pdf يوجّه لـ cap646؛ لم يُغلق المانيفست بالكامل |
| **G4** Governance Full | **PARTIAL** | DTS/DAT/RESTORE spine بدأ — ليس DTS-060 + DATA-100 كاملين |
| **G5** Batch Closure | **PASS*** | 826/826 runtime — *يُرفض rescue_tier في التحقق الصارم |
| **G6** UI/E2E | **FAIL** | لا Playwright لمسارات تسجيل/دفع/قرار |
| **G7** CI Green | **PARTIAL** | 2811 اختبار — CI يشغّل subset فقط |
| **G8** Production Infra | **FAIL** | PostgreSQL/Redis/webhooks secrets غير مُعدّة للإنتاج |
| **G9** External Assurance | **FAIL** | pentest · تراخيص · SOC2 — خارجي |
| **G10** Launch Pack | **PARTIAL** | data room جزئي · discovery freeze غير مُجمّد |

**تشغيل التقييم:** `python scripts/pre_launch_gate_assessor.py` → `PRE_LAUNCH_GATE_ASSESSMENT.json`

---

## 3. الـ 12 ملفًا الحاكم — خريطة الإكمال

| BGS | الملف | الحزمة | MVP اليوم | المطلوب قبل الإطلاق |
|-----|-------|--------|-----------|---------------------|
| BGS-001 | Capability Standard v6 | `cap646/` | batch01/02 قوي | 826 goal-specific (لا keyword rescue) |
| BGS-002 | Data/Storage v4 | `blackdark/data/` | جزئي | DSR + trace/replay كامل |
| BGS-003 | Temporal Intelligence | `feed_lag_scanner`… | scattered | PIT + leakage firewall |
| BGS-004 | Adaptive UX v4 | `trust_pulse`… | تصميم | Six Heroes router كامل |
| BGS-005 | Billing BILL-001→061 | `billing_service` | checkout MVP | webhooks durable + BILL-061 |
| BGS-006 | Identity ID-001→072 | `identity_service` | auth MVP | passkeys + ID-072 gate |
| BGS-007 | Timezone TZ-001→036 | partial UTC | جزئي | IANA + جدولة |
| BGS-008 | Failure ERR-001→050 | `failure_corpus` | rescue | RFC9457 + 5-layer UX |
| BGS-009 | Decision Truth DTS | `decision_truth/` | MVP 12/60 | DTS spine → 60/60 |
| BGS-010 | Data Gov DAT/RESTORE | `data_governance/` | MVP 5/18 DAT | DAT + RESTORE-011 |
| BGS-011 | Financial Security FDS | `security_posture` | principles | FDS-C1→C6 evidence |
| BGS-012 | Anonymous Visitor AV | `product_honesty_api` | جزئي | AV-01→30 |

---

## 4. خطة التنفيذ قبل Railway (ترتيب إلزامي)

### المرحلة A — صدق السجل (أسبوع 1)
1. إصلاح `full_completion_bootstrap.py` — DONE = production_aligned + batch verify (تم)
2. تجميد discovery + محاذاة SHA (`DISCOVERY_FREEZE.json`)
3. تحديث `CAPABILITY_MASTER_REGISTER` من inventory الحقيقي

### المرحلة B — عمق الحوكمة (أسبوع 2–4)
4. `decision_truth/requirements.py` → DTS-001..060 مع اختبار لكل ID
5. `data_governance/` → DAT-001..018 + RESTORE-001..011 (بدأ)
6. `governance/billing_requirements.py` → BILL spine
7. `governance/identity_requirements.py` → ID spine
8. `governance/failure_requirements.py` → ERR spine

### المرحلة C — جودة القدرات (أسبوع 4–8)
9. إزالة `keyword_fallback` من مسار الإغلاق — bindings حقيقية لكل batch
10. إغلاق P1/P2/P3 بالاختبارات
11. MOCK_OR_STUB → IMPLEMENTED مع منطق أعمال حقيقي (307 ID)

### المرحلة D — ما قبل Railway (أسبوع 8–10)
12. PostgreSQL migration + `tests/test_postgres_migration_integrity.py`
13. Stripe/Lemon webhook secrets + اختبارات HTTP موقّعة
14. Playwright E2E: signup → pay → decision → dashboard
15. `pre_launch_ready: true` في التقييم

### المرحلة E — Railway staging فقط (بعد A–D)
16. رفع staging — **ليس prod**
17. Live shadow + PASS_LIVE evidence
18. G9 خارجي ثم G10 موافقة مالك

---

## 5. ما لا يُنفَّذ بالذكاء الاصطناعي وحده

- حساب Stripe/Lemon إنتاجي
- تراخيص Bloomberg/Kaiko/…
- Pentest مستقل
- موافقة المالك على الإطلاق للعملاء

---

## 6. أوامر المراقبة اليومية

```bash
python scripts/pre_launch_gate_assessor.py
python scripts/batch_closure_verify.py
python scripts/war_room_24h_orchestrator.py
python scripts/full_completion_bootstrap.py
```

---

**الخلاصة للمالك:** طلبك صحيح وممكن — لكنه **مشروع إكمال مؤسسي** وليس «نشر على Railway».  
الخطوة التالية: إغلاق G1 + G4 + G6 + G8 محليًا، ثم staging، ثم PASS_LIVE، ثم prod.
