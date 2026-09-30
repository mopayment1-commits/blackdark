# الجولة 21 — وثيقة CI E-TEST ومجموعة التحقق الهندسي

**السلطة:** البرنامج **§3.2** (فئة E-TEST) و **§8.3 V-2**

## وثيقة CI

- `governance/launch57/LAUNCH57_CI_ASSURANCE_MANIFEST.json`
- البوابة: `python scripts/verify_launch57_ci_assurance_manifest.py`
- Workflow: `.github/workflows/launch57-cisa-assurance.yml`

تسجيل رابط تشغيل CI يتم **بشريًا** (حقل `qa_ci_green_run_url` في سجل §8.3 V-2).

## مجموعة محلية للمراجع

```bash
python scripts/run_launch57_engineering_verification_suite.py
# اختياري: LAUNCH57_SKIP_PYTEST=1 للبوابات فقط
```

## مزامنة المخرجات

`verify_launch57_generated_artifacts_fresh.py` يتحقق أيضًا من `phase` و`remediation_sha` في فهرس البوابات.
