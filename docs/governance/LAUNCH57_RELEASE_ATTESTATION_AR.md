# صياغة الإصدار المسموحة — §8.2

**السلطة:** `docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md` — **§8.2 Release attestation (allowed wording)**  
**السجل:** `governance/launch57/LAUNCH57_RELEASE_ATTESTATION_82.json`  
**البوابة:** `python scripts/verify_launch57_release_attestation_82.py`

## النص المسموح (إنجليزي — حرفي من البرنامج)

> BLACKDARK Launch-57 has been remediated against the August 2024 CISA Secure by Demand procurement guidance checklist areas, with evidence indexed at `governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json`. This is not CISA certification.

## شروط الاستخدام (من البرنامج)

- **§8.1:** يُستخدم هذا النص فقط عندما تكون الحالة `CLOSED` لجميع FINDING-01…19 في الفهرس.
- **§1.2:** ممنوع «CISA certified»، «CISA approved»، أو ادعاءات شهادة كاملة قبل بوابات الإغلاق.
- حتى ذلك الحين: `cisa_certification_claimed` يبقى `false` في API والمخرجات الحاكمة.

## بوابة §8.1 (صادقة)

```bash
python scripts/verify_launch57_program_closure_81.py
```

يتوقع `program_complete_81: false` وخروجًا `2` طالما توجد حالات غير `CLOSED` بالضبط.

## فئات الأدلة (§3.2)

السجل: `governance/launch57/LAUNCH57_EVIDENCE_CLASS_REGISTER.json`  
البوابة: `python scripts/verify_launch57_evidence_class_register.py`
