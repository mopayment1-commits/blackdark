# الجولة 17 — L57-P7-WP5 دخان الإنتاج و§8.3 V-2/V-3

**السلطة:** `LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md` — Phase 7 **L57-P7-WP5**، **§8.3** V-2 و V-3

## L57-P7-WP5 (دخان إنتاج)

```bash
export LAUNCH57_PROD_URL=https://<prod>
python scripts/verify_launch57_p7_wp5_production_smoke.py
python scripts/record_launch57_p7_wp5_prod_smoke.py
```

الفحوص: رؤوس أمان على 401، `security.txt`، وصول مسار SSO authorize (بدون حظر anonymous)، وتصدير سجلات اختياري مع `LAUNCH57_OPS_BEARER_TOKEN`.

## §8.3 V-2 (QA — جزء مستودع)

`python scripts/verify_launch57_qa_ci_bundle.py` — workflows + اختبار الرفض؛ رابط CI يُسجَّل بشريًا.

## §8.3 V-3 (Ops — حزمة)

`python scripts/verify_launch57_ops_v3_bundle.py` — يشغّل P7-WP5 عند تعيين `LAUNCH57_PROD_URL`.

**لا** يغلق FINDING-18/19/01 ولا يعلن شهادة CISA.
