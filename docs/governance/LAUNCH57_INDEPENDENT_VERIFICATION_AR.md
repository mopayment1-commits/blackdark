# التحقق المستقل — برنامج Launch-57 CISA (§8.3)

**السلطة:** `docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md` — القسم **§8.3 Independent verification (required)**  
**السجل الآلي:** `governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json`  
**البوابة:** `python scripts/verify_launch57_independent_verification.py`

## خطوات البرنامج (حرفيًا من §8.3)

| الخطوة | المنفّذ | الطريقة |
|--------|---------|---------|
| **V-1** | Security Lead | إعادة تشغيل قائمة الجرد الكاملة مقابل SHA الإصلاح |
| **V-2** | QA | CI أمني أخضر + اختبارات رؤوس الأمان على مسارات الرفض |
| **V-3** | Ops | دخان إنتاج: security.txt، SSO authorize، نافذة تصدير السجلات |
| **V-4** | Legal | مراجعة مواءمة التسعير / SSO / السجلات / VDP |

## ما يغطيه المستودع (بدون تخمين)

- **V-1 (جزء آلي):** بوابات `verify_launch57_finding_inventory_lock`، `verify_launch57_normative_traceability`، `verify_launch57_repo_evidence`، `verify_launch57_generated_artifacts_fresh`.
- **V-2 (جزء آلي):** وجود workflows `launch57-cisa-assurance` و`security.yml` واختبار `test_anonymous_denial_includes_security_headers`.
- **V-3:** سكربتات التشغيل موثّقة؛ الدخان الحي يتطلب `LAUNCH57_PROD_URL` وتوقيع Ops.
- **V-4:** وجود مستندات المراجعة؛ **PASS قانوني** يتطلب `LAUNCH57_LEGAL_REVIEW_ID` (لا يُختلق في CI).

## ما لا يُعتبر إغلاقًا

- إكمال §8.3 **لا** يغلق FINDING-01 / 18 / 19 ولا يمنح شهادة CISA (§8.1–§8.2).
- `program_closure_verification_complete` يبقى `false` حتى اكتمال الفهرس والأدلة حسب §3.

## أوامر

```bash
python scripts/verify_launch57_independent_verification.py
python scripts/verify_launch57_merge_readiness.py
```
