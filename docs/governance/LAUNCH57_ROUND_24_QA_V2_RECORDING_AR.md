# الجولة 24 — §8.3 V-2 تسجيل روابط CI + بوابة حزمة المراجع

**السلطة:** البرنامج **§8.3 V-2**، `LAUNCH57_QA_V2_CI_RECORDING.json`

## بوابات المستودع

- `python scripts/verify_launch57_ci_reviewer_evidence_bundle.py` — بنية `LAUNCH57_CI_REVIEWER_EVIDENCE_BUNDLE.json` (روابط `null` مقبولة للدمج الهندسي)
- `python scripts/verify_launch57_cross_workflow_assurance.py` — ربط workflows (من الجولة 23)

## تسجيل QA (E-TEST معزول — gitignored)

```bash
python scripts/record_launch57_qa_v2_ci_urls.py \
  --security-run-url 'https://github.com/<org>/<repo>/actions/runs/<id>' \
  --launch57-run-url 'https://github.com/<org>/<repo>/actions/runs/<id>' \
  --recorded-by 'QA role/id'
```

لا يُغلق FINDING ولا §8.1. اختياري: `record_launch57_independent_verification_signoff.py --step V-2`.

## صرامة اختيارية

`LAUNCH57_REQUIRE_V2_CI_URLS=1` يجعل بوابة الحزمة تفشل إذا لم تُملأ كلا الرابطين **في الملف المُلتزم** (للاستخدام بعد التسجيل اليدوي فقط — لا عناوين مزيفة).
