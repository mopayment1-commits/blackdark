# BLACKDARK — CURSOR EXECUTION MANDATE 2026

نفّذ هذه الحزمة حرفيًا. أنت **لا تحدد نطاق التدقيق**؛ ملفات YAML هي الـSSOT.

## الملفات الحاكمة
- `BLACKDARK_AUDIT_REQUIREMENTS_2026.yaml`
- `BLACKDARK_AUDIT_PROCEDURES_2026.yaml`
- `BLACKDARK_AUDIT_STATE_2026.yaml`
- `blackdark_audit_completion_gate.py`

## 1) PRE-FLIGHT إلزامي قبل أي فحص
شغّل:
```bash
python blackdark_audit_completion_gate.py --preflight
```
يجب أن تكون النتيجة:
- requirements = 354
- procedures = 354
- mapped_requirements = 354
- structural_errors = []
- PREFLIGHT_GATE = PASS

إذا فشل: ممنوع بدء الفحص. أصلح فقط Mapping التدقيق.

## 2) التنفيذ
نفّذ **كل Procedure ID** في ملف الإجراءات، بالترتيب أو على batches محفوظة، لكن بدون إسقاط أي Procedure.

لكل Procedure:
1. حدد population/denominator الحقيقي.
2. نفذ `required_method`.
3. اجمع `minimum_evidence_strength` أو أقوى.
4. سجل في STATE:
   - status
   - evidence_ids
   - evidence_strength
   - command/tool
   - baseline SHA
   - environment/access level
   - coverage_numerator
   - coverage_denominator
   - finding_ids
   - limitations
   - validation_components حيث يلزم
5. لا تنتقل لحالة نهائية قبل وجود دليل.

## 3) الحالات المسموحة فقط
PASS / FAIL / PARTIAL / BLOCKED / NOT_APPLICABLE

`NOT_VERIFIED` **ليست حالة إغلاق**.

BLOCKED لا يجوز إلا بمانع خارجي حقيقي، ويجب تسجيل:
blocker_id + blocker_reason + required_external_evidence + required_access_level.

## 4) منع الاختصار
- Discovery ≠ Audit
- Static review ≠ Runtime verification
- Test file ≠ Test execution
- Page probe ≠ UI complete
- Missing decorator ≠ unauthenticated vulnerability
- Pytest pass ≠ Model validation
- Report file created ≠ Wave/Domain closed
- No production access ≠ Stop whole audit

## 5) قواعد خاصة
**Financial:** لا PASS دون independent recomputation.
**Models:** لا PASS دون conceptual soundness + implementation verification + boundary testing + sensitivity + stress، وما ينطبق من challenger/outcomes/backtest/OOS.
**Authorization:** لا PASS من static inspection؛ نفذ behavioral positive/negative tests حيث آمن.
**APIs:** صنف واختبر السلوك الفعلي لكل material exposed route.
**UI:** اختبر material controls end-to-end.
**DB:** نفذ clean DB/migrations/CRUD/rollback/precision checks في بيئة آمنة.
**Tests:** شغّل الاختبارات فعليًا وسجل النتائج.
**Performance:** لا ادعاء scalability دون قياس.
**Resilience:** نفذ failure testing الآمن حيث ممكن.
**Production-only:** نفذ L1/L2 المتاح ثم BLOCK فقط الجزء الذي يحتاج L3/L5.
**No remediation:** لا تصلح أي defect أثناء التدقيق.

## 6) عشر مراجعات إلزامية بعد اكتمال الإجراءات
PASS-01 Universe completeness
PASS-02 Evidence sufficiency
PASS-03 Financial/model red team
PASS-04 Data/lineage red team
PASS-05 Security/authorization red team
PASS-06 Runtime/failure semantics red team
PASS-07 Product/user-reality red team
PASS-08 Resilience/operations red team
PASS-09 Acquisition/IP/documentation red team
PASS-10 Contradiction/arithmetic/closure review

كل PASS يحتاج Evidence IDs ثم يُسجل `COMPLETE`.

## 7) Final Reconciliation
طابق Requirements ↔ Procedures ↔ Results ↔ Evidence ↔ Findings ↔ Coverage.
لا يسمح بأي unmapped أو unexplained gap.

## 8) FINAL GATE
شغّل:
```bash
python blackdark_audit_completion_gate.py
```

**ممنوع منعًا باتًا** إنشاء أو تسمية أي تقرير FINAL / VERIFIED / COMPLETE إذا:
`AUDIT_COMPLETION_GATE != PASS`

إذا FAIL: استمر في الإجراءات الناقصة أو سجّل Blockers الحقيقية ثم أعد تشغيل البوابة.

## 9) التقرير النهائي
فقط بعد Gate PASS أنشئ:
`BLACKDARK_INSTITUTIONAL_DUE_DILIGENCE_FINAL_VERIFIED_2026.md`

ويجب أن يُبنى من السجلات، لا من الذاكرة، ويحتوي:
الحكم المؤسسي، جميع strengths/defects، P0-P3، capabilities، financial/model validation، data lineage، AI، security/authz، DB، APIs، UI، journeys، billing، tests/CI/CD، performance/resilience، observability/DR، privacy/vendor risk، IP/data rights/acquisition، blockers، exact numerator/denominator، نتائج الـ10 Passes، ومخرجات Final Gate.

## 10) التوقف
لا تطلب موافقتي بين الإجراءات.
توقف فقط عند:
1. `AUDIT_COMPLETION_GATE = PASS` وإصدار التقرير النهائي؛ أو
2. عطل تقني يمنع **كل** استمرار آمن، مع حفظ state والدليل.

ابدأ الآن بـPre-flight ثم نفّذ حتى النهاية.
