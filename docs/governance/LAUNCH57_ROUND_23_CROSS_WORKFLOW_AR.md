# الجولة 23 — ضمان CI عبر-workflows + حزمة أدلة المراجع (V-2)

**السلطة:** البرنامج **§8.3 V-2**، `LAUNCH57_PR_MERGE_CHECKLIST.md`، `LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json`

## ما أُضيف (هندسة فقط)

- `LAUNCH57_CROSS_WORKFLOW_ASSURANCE.json` — تعريف institutional لربط `security.yml` و`launch57-cisa-assurance.yml` باختبار `tests/test_cisa_launch57_remediation.py`
- `python scripts/verify_launch57_cross_workflow_assurance.py` — بوابة E-TEST (لا تسجّل عناوين CI تلقائياً)
- `python scripts/generate_launch57_ci_reviewer_evidence_bundle.py` — قالب `LAUNCH57_CI_REVIEWER_EVIDENCE_BUNDLE.json` لحقول URL الفارغة حتى يعبئها QA

## ما لم يُغلق

- **§8.1** و**V-2 البشري** (`qa_ci_green_run_url`) يتطلبان تشغيل CI أخضر على SHA الإصلاح وتسجيل الرابط — لا يُختلق في المستودع.
- FINDING-01 / 18 / 19 تبقى مفتوحة كما في الفهرس.
