# الإغلاق المؤسسي — Batch 01 + Batch 02 (مُعلَّق)

**التاريخ:** 2026-09-01  
**الحالة:** `PENDING_CLOSURE` (بعد CLOSURE-REJECT-02)  
**النطاق:** IDs 1–100 (الدفعتان الرسميتان 01 + 02)

> **شرط سابق للإغلاق:** الموافقة الصريحة المكتوبة من المالك شرط *سابق* لأي إعلان `INSTITUTIONAL_CLOSED`.  
> **الدمج على `main` لا يمنح صفة الإغلاق المؤسسي.**

---

## الحكم التنفيذي (مُعلَّق)

| الدفعة | النطاق | PRODUCTION-ALIGNED (RTM) | الإغلاق |
|--------|--------|-------------------------:|---------|
| **Batch 01** | 1–50 | **50/50** | ⏸ PENDING_CLOSURE |
| **Batch 02** | 51–100 | **50/50** (46 مستقل + 4 OVERLAP_BATCH01) | ⏸ PENDING_CLOSURE |
| **تراكمي** | 1–100 | **100/100 وظيفيًا** | مكتمل وظيفيًا — **جاهزية التشغيل الحي غير مُقيَّمة بعد** |

---

## تقارير سابقة أُبطِلت (ادّعاء إغلاق خاطئ)

| التقرير / الادّعاء | الخطأ | التصحيح |
|-------------------|-------|---------|
| `docs/INSTITUTIONAL_CLOSURE_FINAL.json` (قبل REJECT-02) | `INSTITUTIONAL_CLOSED` + `all_verified: true` | → `PENDING_CLOSURE` |
| `docs/INSTITUTIONAL_CLOSURE_BATCH01_BATCH02.md` (نسخة سابقة) | "جاهز للتشغيل الحي" | → حُذف الادّعاء |
| PR #349 body / merge commit `9798ab8` | "INSTITUTIONAL_CLOSED" في عنوان الدمج | الإغلاق **مرفوض** — الدمج ≠ إغلاق |
| رد الوكيل السابق (2026-09-01) | "المنصة جاهزة للمستخدمين" | **مرفوض** — النطاق 100/826 فقط |
| `scripts/institutional_closure_final_gate.py` | يوحي ببوابة مؤسسية مستقلة | أُعيد تسميته → `run_batch_verification_orchestrator.py` |

---

## البوابات المطلوبة (غير مكتملة)

| البوابة | الحالة | المرجع |
|---------|--------|--------|
| `critical` (ci.yml) | ✅ PASS على main | run 33512245483 |
| `gate-full` (cap978-institutional-gate.yml) | ❌ FAILURE | run 33512905843 |
| SonarCloud QG | ❌ FAILED | run 33512905952 |
| موافقة المالك | ⏸ معلّقة | CLOSURE-REJECT-02 |

---

## المنسّق المحلي (ليس بوابة CI)

```bash
python scripts/run_batch_verification_orchestrator.py
```

**النتيجة:** `docs/BATCH_VERIFICATION_ORCHESTRATOR_RESULT.json`

---

## Batch 03 (101–150)

**محظور.** `batch03_prep` لا يُحتسب ولا يُغلق.  
أزواج LINK-ELIGIBLE (#106/#107/#110/#125) غير محتسبة في تقدم الإغلاق.

---

## التقرير الكامل

راجع `docs/CLOSURE_REJECT_02_REPORT.md` للإجابة المرقّمة على البنود 1–28.
