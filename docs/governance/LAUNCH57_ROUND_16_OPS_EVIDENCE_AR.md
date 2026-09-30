# الجولة 16 — أدلة تشغيلية متبقية (مؤسسي)

**السلطة:** `LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md` — §6 FINDING-11 / FINDING-14، §8.3 V-1

## FINDING-11 (SBOM / NTIA)

- تحليل الفجوات: `governance/launch57/LAUNCH57_NTIA_SBOM_GAP_ANALYSIS.json`
- البوابة: `python scripts/verify_launch57_sbom_ntia_scope.py`
- إغلاق FINDING-11 في الفهرس يتطلب **أحد**: artifact حاوية Syft **أو** `LAUNCH57_SBOM_SEC_LEAD_APPROVAL_ID` + نجاح البوابة (`transition_launch57_finding_status.py --finding FINDING-11 --apply`)

## FINDING-14 (security.txt إنتاج)

```bash
export LAUNCH57_PROD_URL=https://<prod>
python scripts/record_launch57_security_txt_prod_verification.py
python scripts/transition_launch57_finding_status.py --finding FINDING-14 --prod-url "$LAUNCH57_PROD_URL" --apply
```

تسجيل E-RUN في `governance/launch57/evidence/FINDING-14/` (gitignored) — **لا** يغلق الفهرس تلقائيًا.

## V-1 (Security Lead)

```bash
python scripts/verify_launch57_security_lead_inventory_rerun.py
```

حزمة بوابات المستودع؛ التوقيع البشري عبر `record_launch57_independent_verification_signoff.py`.
