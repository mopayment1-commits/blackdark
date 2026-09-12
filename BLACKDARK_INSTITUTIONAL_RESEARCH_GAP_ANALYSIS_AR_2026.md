# البحث المؤسسي وتحليل الفجوات — BLACKDARK 2026

**التاريخ:** 11 سبتمبر 2026  
**المنهجية:** معايير دولية موثّقة + مواصفات المشروع الـ11 + أدلة المستودع الحية  
**النطاق:** كل ما يُنفَّذ آليًا — **مستثنى:** النشر على Railway، pentest خارجي، تراخيح بشرية، موافقة المالك

---

## 1. الخلاصة التنفيذية

| السؤال | الجواب |
|--------|--------|
| هل تحقق الهدف الأعلى (كفاءة + سلامة + اكتمال كل جزء)؟ | **لا — بعد** |
| درجة النضج المؤسسي التقريبية (من 100) | **~38** (انظر `INSTITUTIONAL_READINESS_MATRIX.json`) |
| هل الـ11 ملفًا حاكمًا مُنفَّذة حرفيًا؟ | **لا (~18% PASS_ENGINEERING صارم)** |
| هل 826 قدرة مكتملة مؤسسيًا؟ | **لا (114 PRODUCTION-ALIGNED / 826)** |
| هل الأساس آمن للبناء؟ | **نعم جزئيًا** — WF حرجة مُصلَحة، secrets نظيفة، monitoring جاهز |

**الهدف النهائي المكتمل** يتطلب إغلاق **5 طبقات** (أدناه) — ثلاث منها بدأت، اثنتان لم تُغلق.

---

## 2. الإطار المرجعي العلمي (مصادر موثّقة)

### 2.1 NIST SSDF — SP 800-218 الإصدار 1.1

المصدر: [NIST SSDF v1.1](https://www.nist.gov/publications/secure-software-development-framework-ssdf-version-11-recommendations-mitigating-risk)

أربع مجموعات ممارسات:
- **PO** — Prepare Organization (متطلبات أمنية، toolchain، بوابات CI)
- **PS** — Protect Software (سلامة الكود، provenance، SBOM)
- **PW** — Produce Well-Secured Software (secure coding، اختبار ديناميكي)
- **RV** — Respond to Vulnerabilities (تتبع ثغرات، incident response)

**حالة BLACKDARK:** PO=PARTIAL، PS=PARTIAL، PW=PARTIAL، RV=PARTIAL

### 2.2 OWASP ASVS 4.0.3 — المستوى 2

المصدر: [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/) — **المستوى الموصى به لتطبيقات fintech حساسة**

محاور رئيسية: V2 Authentication، V4 Access Control، V7 Logging، V9 TLS، V13 API

**حالة BLACKDARK:**
- ✅ WF-015/016/017 (انتحال هوية، عزل tenant) — مُصلَحة + pytest
- ✅ عدم تسريب secrets في logs
- ⚠️ MFA/WebAuthn غير مكتمل (ID spec)
- ⚠️ DAST/penetration خارج النطاق

### 2.3 ISO/IEC 25010:2023 — نموذج جودة المنتج

المصدر: [ISO 25010:2023](https://www.iso.org/standard/78176.html)

9 خصائص — الأهم للمشروع:

| الخاصية | التعريف | حالة BLACKDARK |
|---------|---------|----------------|
| **Functional suitability** | يحقق الوظيفة المحددة | **FAIL** (826 غير goal-specific) |
| **Reliability** | يعمل بدون انقطاع | **PARTIAL** (health + monitoring) |
| **Security** | يحمي من التهديدات | **PARTIAL** (WF + secrets) |
| **Maintainability** | قابل للتعديل والاختبار | **PARTIAL** (2800+ test، CI جزئي) |
| **Performance efficiency** | يتحمل الحمل | **PARTIAL** (rate limits تحتاج ترقية APIs) |

### 2.4 معيار المشروع v6 (الملف الحاكم المحلي)

تعريفات ثلاثية: `PASS_ENGINEERING` ≠ `PASS_LIVE` ≠ `ASSURANCE_READY`

**لا يُقبل ادعاء اكتمال** بدون evidence حي لكل قدرة — وهذا غير متحقق اليوم.

---

## 3. ما أُنجز (دليل حي — ليس ادّعاء)

| المجال | الدليل | الحالة |
|--------|--------|--------|
| Runtime 826 | `BATCH_CLOSURE_VERIFY_REPORT.json` | 826/826 success (بعضها rescue) |
| أمان WF-015 | `SECURITY_WORKFLOW_REGISTER.json` + pytest | REMEDIATED |
| Secrets | `SECRETS_HYGIENE_REPORT.json` | clean: true |
| مراقبة | `ops/monitoring_alerting.py` | Telegram/webhook |
| قانوني | `/terms` `/privacy` `/disclaimer` | موجود |
| DTS/DIG MVP | `decision_truth/` `data_governance/` | 12/60 DTS، 5/18 DAT |
| RESTORE | `data_governance/restore.py` | 10/11 PASS |
| تقييم بوابات | `PRE_LAUNCH_GATE_ASSESSMENT.json` | pre_launch_ready: false |

---

## 4. الفجوات الحرجة (ما ينقص في النموذج)

### طبقة A — صدق القدرات (الأهم)

| الفجوة | الأثر | المعيار |
|--------|-------|---------|
| 712 قدرة ليست PRODUCTION-ALIGNED | ادعاء كاذب للمستثمر/المستخدم | v6 §PASS_ENGINEERING |
| keyword_fallback في batches 04-17 | نجاح وهمي | engineering_audit Type A |
| 307 MOCK_OR_STUB في master register | غرف فارغة | ISO functional suitability |
| split-brain 58 ID | مسار فحص ≠ إنتاج | G3 |

### طبقة B — الحوكمة (11 ملف)

| الملف | النقص الرئيسي |
|-------|---------------|
| DTS | 48/60 requirement IDs بدون تنفيذ+اختبار |
| DIG/DAT | ingest L1-L5، DATA-100، vendor licensing |
| BILL | webhooks durable، BILL-061 live gate |
| ID | passkeys، ID-072، SCIM حي |
| ERR | RFC9457، 5-layer degraded UX |
| FDS | KMS/HSM evidence |
| Temporal | PIT reconstruction |
| Adaptive UX | Six Heroes كامل |
| AV | AV-01→30 |
| TZ | IANA + DST |
| Storage v4 | trace/replay كامل |

### طبقة C — الجودة والاختبار

| الفجوة | المرجع |
|--------|--------|
| لا Playwright E2E | ASVS + G6 |
| CI يشغّل subset فقط (~20 فشل معروف) | NIST PO.4 |
| لا fuzz/DAST منهجي | NIST PW.5 |
| discovery freeze غير مُجمّد | G10 |

### طبقة D — التشغيل (بدون Railway)

| الفجوة | ملاحظة |
|--------|--------|
| PostgreSQL path غير مُفعَّل محليًا | BLK-002 — الكود موجود |
| CoinGecko/LLM free tier | يكسر فوق ~50-100 مستخدم |
| Pentest/SOC2 | خارجي — مُستثنى |

### طبقة E — المراقبة (بعد النشر)

| موجود | ينقص |
|--------|------|
| self-probe + Telegram | UptimeRobot خارجي مُوصى |
| latency thresholds | APM (Datadog/OpenTelemetry) اختياري |

---

## 5. خارطة الإكمال — ما يُنفَّذ بجانب ما عملناه

### المرحلة 0 — قياس صادق (أسبوع 1)
```bash
python scripts/institutional_readiness_matrix.py
python scripts/engineering_audit_826.py
python scripts/pre_launch_gate_assessor.py
```

### المرحلة 1 — إغلاق Type A (أسبوع 2-6)
- batch04→17: bindings حقيقية بدل rescue
- تحديث `CAPABILITY_MASTER_REGISTER` من inventory
- إغلاق split-brain manifest

### المرحلة 2 — حوكمة كاملة (أسبوع 6-12)
- `decision_truth/requirements.py` → DTS-060 كل ID + pytest
- `data_governance/` → DAT-018 + DATA spine
- `governance/billing_requirements.py` → BILL-061
- `governance/identity_requirements.py` → ID-072
- `governance/failure_requirements.py` → ERR-050

### المرحلة 3 — جودة مؤسسية (أسبوع 12-16)
- Playwright: signup → pay → decision → dashboard
- CI كامل أخضر (2811)
- SBOM + provenance gate

### المرحلة 4 — PASS_ENGINEERING claim (بوابة نهائية)
يُقبل الادعاء فقط عند:
1. `type_a_zero: true` في ENGINEERING_AUDIT_826
2. `institutional_maturity_score_100 >= 85`
3. كل domain في MATRIX = PASS أو PARTIAL موثّق فقط لخارجي
4. `pre_launch_ready: true` (بدون Railway)

---

## 6. معيار «الهدف تحقق نهائيًا» (قابل للقياس)

```
FINAL_GOAL_ACHIEVED = (
    Type_A == 0
    AND governing_specs_PASS_ENGINEERING >= 95%
    AND inventory_PRODUCTION_ALIGNED == 826
    AND ISO25010_functional_suitability == PASS
    AND NIST_SSDF_all_groups >= PARTIAL
    AND OWASP_ASVS_L2_critical == PASS
    AND secrets_hygiene == clean
    AND security_WF_critical == REMEDIATED
    AND monitoring_configured == true
    AND legal_pages == present
)
```

**الوضع الحالي:** `FINAL_GOAL_ACHIEVED = false`

---

## 7. المراجع

1. NIST (2022). *Secure Software Development Framework (SSDF) Version 1.1*, SP 800-218. https://www.nist.gov/publications/secure-software-development-framework-ssdf-version-11
2. OWASP (2023). *Application Security Verification Standard 4.0.3*. https://owasp.org/www-project-application-security-verification-standard/
3. ISO/IEC (2023). *ISO/IEC 25010:2023* — Systems and software Quality Requirements and Evaluation. https://www.iso.org/standard/78176.html
4. BLACKDARK (2026). *Institutional Capability Standard v6* — `governing-sources-population/`
5. BLACKDARK (2026). *PRE_LAUNCH_GATE_ASSESSMENT.json* — أدلة المستودع

---

## 8. الخلاصة للمالك

المشروع **ليس في أعلى درجات الكفاءة والسلامة بعد** — لكنه **ليس فارغًا**: نواة قوية (batch01/02، WF أمنية، secrets، monitoring، قانوني، حوكمة MVP).

**الفجوة الحقيقية:** الفرق بين «runtime يمرّ» و«كل جزء يحقق غرضه التصميمي بمعيار مؤسسي».

**ما يُنفَّذ تاليًا (آليًا):** إغلاق Type A → DTS/DAT/BILL/ID spines → E2E → CI أخضر — **بدون انتظار Railway**.

**تشغيل المصفوفة:**
```bash
python scripts/institutional_readiness_matrix.py
# → INSTITUTIONAL_READINESS_MATRIX.json
```
