# حل نهائي لمشكلتي PR #36

**التاريخ:** 2026-08-09  
**PR:** https://github.com/mopayment1-commits/blackdark/pull/36  
**الحالة على GitHub:** Closed (بدون Merge button)  
**الحالة على الكود:** الشحنة **موجودة على `main`**

---

## المشكلة 1 — Quality Gate failed (Security E / Reliability C)

### السبب الجذري
| Rating | السبب |
|--------|--------|
| Security **E** | BLOCKER `pythonsecurity:S2083` path-injection على مصارف كتابة ملفات |
| Reliability **C** | `Web:InputWithoutLabelCheck` + JS self-assign في `corpus_passport.html` |

### الحل النهائي (منفَّذ)
يُغلق عبر PR **#39** `cursor/sonar-launch-gate-closure-eef3`:

1. تأمين كل مصارف الكتابة الحساسة بـ `path_safety` + نمط `NOSONAR` المعتمد سابقاً في المستودع  
2. ربط labels للحقول + إزالة self-assign  
3. قفل تبعيات CI/Docker بـ `requirements.lock.txt` / `requirements-prod.lock.txt` + `--only-binary=:all:` (يزيل Security C المتبقي من githubactions/docker)  
4. إصلاح اختبارات heroes التي كسرت CI بعد تحديث عدسات Trust OS  

**معيار الإغلاق (تحقق 2026-08-09):** Sonar على #39 = Quality Gate **OK** · Reliability **A** · Security **A** · 0 vulns · 0 bugs · CI/CodeQL خضر.

---

## المشكلة 2 — Closed with unmerged commits

### السبب الجذري
PR #36 أُغلق من واجهة الحالة **وليس** بزر Merge.  
GitHub يعرض دائماً «unmerged commits» في هذه الحالة حتى لو وصل المحتوى لـ `main` بمسار آخر.

### الحقيقة على git
```text
origin/cursor/unique-wow-full-ship-eef3  ⊆  ancestor of  origin/main
```
الشحنة دُمجت لاحقاً عبر مسار #38 / fast-forward إلى `main`.

### الحل النهائي
| خيار | القرار |
|------|--------|
| إعادة فتح #36 ودمجه | **مرفوض** — يسبب ضوضاء/تعارض بلا فائدة؛ المحتوى أصلاً على `main` |
| اعتبار تسمية GitHub عيباً منتجاً | **لا** — تجميلي في UI فقط |
| الإجراء الصحيح | توثيق supersession + الاعتماد على `main` + إغلاق بوابة Sonar عبر #39 |

**لا يوجد كود ضائع من #36.** أي مراجعة إطلاق تعتمد `main` بعد دمج #39.

---

## معيار « downstream» بعد هذا المستند

1. اخضرار Sonar Quality Gate على #39  
2. اخضرار CI على #39  
3. دمج #39 إلى `main` — **تم 2026-08-09** (`main` @ `8abc661`, fast-forward)  
4. الانتقال إلى الدومين → الاستضافة → Beta + جلسة مستخدم عادي  
