# المعيار المؤسسي الشامل لبناء القدرات والمميزات حتى الاستخدام الحي
## النسخة الخامسة — Deep Point-by-Point Institutional Validation — 6 سبتمبر 2026

> **Integration update — 7 سبتمبر 2026:** تم دمج متطلبات **BLACKDARK Completion & Real-Capability Standard — النسخة المنقحة النهائية** داخل هذا المرجع على أساس delta-only، مع بقاء v5 هو المرجع الأعلى، ومنع إنشاء SSOT موازٍ أو تكرار متطلبات موجودة أصلًا.

> **تحديث v5:** مراجعة مستقلة نقطةً بنقطة لجميع أقسام v4، مع إعادة التحقق من حداثة وسلطة المراجع حتى 6 سبتمبر 2026، وتصحيح التصنيفات التي قد توحي خطأً بأن إرشادًا أو benchmark هو معيار ملزم. v5 يحتفظ بجوهر v4 لكنه يضيف سجل صلاحية للمراجع، وحدود الانطباق التنظيمي، ومصفوفة مراجعة 0–135، ويحدّث DORA إلى نموذج المقاييس الخمسة الحالي.

> **الغرض:** مرجع تنفيذي واحد يُستخدم لبناء أو استكمال أو دمج أو إصلاح أي قدرة/ميزة من لحظة تعريف الهدف، مرورًا بالتصميم والتنفيذ والاختبار والأمان والأداء والتشغيل، وحتى استخدامها فعليًا من المستخدم وتحقيقها للهدف المصممة من أجله دون قصور جوهري.
>
> **يشمل أيضًا:** منع التكرار، اكتشافه، العلاج الجذري، القالب الخماسي، الربط بالأبطال الستة، جودة البيانات، AI/ML، الأداء، الاعتمادية، الأمن، الخصوصية، التشغيل، المراقبة، الأدلة، الاسترجاع والتراجع، ومعايير الإغلاق.
>
> **قاعدة حاكمة:** لا يكفي أن يوجد كود، أو أن تعمل دالة، أو أن ينجح اختبار واحد، أو أن ترجع الواجهة `success=true`. القدرة لا تُغلق إلا عندما يمكن إثبات أنها تحقق الهدف الصحيح للمستخدم، في المسار الصحيح، بالبيانات الصحيحة، وبالأداء والأمان والاعتمادية المطلوبة، مع دليل قابل لإعادة التحقق.

---

# 0. تصنيف قوة المرجع — لمنع الخلط

كل قاعدة في هذا المرجع يجب فهمها تحت أحد الأنواع التالية:

| الرمز | النوع | المعنى |
|---|---|---|
| **[STD]** | معيار/مواصفة رسمية | قاعدة أو إطار مستند إلى معيار دولي/رسمي منشور |
| **[GUIDE]** | إرشاد مؤسسي موثّق | ممارسة منشورة من جهة هندسية موثوقة مثل Google SRE / NIST / OWASP / AWS / W3C |
| **[PRACTICE]** | ممارسة صناعية/علمية | منهج معروف مهنيًا أو أكاديميًا ويُستخدم عند انطباقه |
| **[POLICY]** | سياسة المشروع | قرار داخلي ملزم للمشروع، قد يكون مستمدًا من المعايير لكنه ليس نصًا حرفيًا منها |
| **[WEB STANDARD]** | معيار ويب رسمي | W3C Recommendation أو مواصفة ويب رسمية؛ ليست ISO لكنها معيار منشور رسميًا |
| **[INDUSTRY SPEC]** | مواصفة صناعية | مواصفة منشورة ومتفق عليها صناعيًا مثل SLSA؛ لا تُعامل كشهادة ISO |
| **[ASSURANCE CRITERIA]** | معايير/ضوابط Assurance | مثل AICPA TSC؛ تستخدم للتقييم/الـattestation ولا تعني وجود تقرير SOC |
| **[SUPERVISORY BENCHMARK]** | مرجع رقابي قطاعي | مثل BCBS/Federal Reserve؛ يستخدم كbenchmark عند ملاءمة السياق ولا يعني الخضوع التنظيمي |

**قاعدة إلزامية:** لا تُنسب سياسة المشروع إلى ISO أو NIST أو Google وكأنها نص حرفي ما لم يكن المصدر يفرضها صراحة.

---

# 1. الطبقة المرجعية المعتمدة

## 1.1 دورة حياة البرمجيات
- **[STD] ISO/IEC/IEEE 12207:2026 — Software life cycle processes**
- المرجع الحالي في 2026، وقد حل محل ISO/IEC/IEEE 12207:2017.
- يغطي التطوير والتشغيل والصيانة والتقاعد ويمكن تطبيق عملياته تكراريًا وتدريجيًا.
- **مهم:** المعيار لا يفرض منهج تطوير واحدًا أو قالبًا واحدًا للتنفيذ؛ لذلك التصنيفات والقوالب أدناه هي سياسات مشروع مبنية على الإطار وليست نصًا حرفيًا منه.

## 1.2 جودة المنتج
- **[STD] ISO/IEC 25010:2023 — Product quality model**
- يستخدم لتحديد وقياس وتقييم جودة المنتج، ومعايير القبول، وأهداف الاختبار.
- الخصائص المستخدمة هنا تشمل، حسب الانطباق: Functional Suitability، Performance Efficiency، Compatibility، Interaction Capability، Reliability، Security، Maintainability، Flexibility، Safety.

## 1.3 جودة الاستخدام الفعلي
- **[STD] ISO/IEC 25019:2023 — Quality-in-use model**
- ضروري لأن نجاح الكود لا يعني نجاح المستخدم.
- الإغلاق النهائي يجب أن يتحقق من أن القدرة فعليًا تؤدي إلى النتيجة المطلوبة داخل سياق الاستخدام.

## 1.4 هندسة المتطلبات
- **[STD] ISO/IEC/IEEE 29148:2018** — الإصدار المنشور الحالي والمُؤكد، مع **Edition 3 DIS قيد التطوير في 2026**.
- يضبط المتطلبات، تتبعها، ومخرجاتها.
- كل قدرة يجب أن تكون قابلة للتحقق وغير غامضة ومتصلة بهدف واضح.
- **قاعدة Currency:** لا تُعامل نسخة DIS المستقبلية كمرجع حاكم حتى نشرها كـInternational Standard.

## 1.5 الاختبار
- **[STD] ISO/IEC/IEEE 29119-2:2021**
- إطار عمليات اختبار قابل للتطبيق عبر نماذج دورة الحياة.
- يستخدم هنا لبناء test process قابل للتدقيق من الوحدة إلى النظام وE2E.

## 1.6 وصف المعمارية
- **[STD] ISO/IEC/IEEE 42010:2022**
- يستخدم لوصف البنية، العلاقات، وجهات النظر، والاعتماديات.
- **تنبيه:** لا يفرض قالب ADR محددًا؛ استخدام ADR في هذا المشروع **[POLICY]** وسيلة توثيق مساعدة.

## 1.7 جودة البيانات
- **[STD] ISO/IEC 25012:2008 — Data quality model**
- ما يزال معيارًا جاريًا ومؤكدًا.
- يستخدم لتحديد متطلبات جودة البيانات وتقييمها، خصوصًا في البيانات المالية والمجمعة.

## 1.8 أمن التطبيقات
- **[GUIDE] OWASP ASVS 5.0.0**
- أساس للتحقق من الضوابط الأمنية التقنية لتطبيقات الويب.
- **[GUIDE] OWASP API Security Top 10 2023**
- يستخدم لمسارات API الحساسة.
- **[GUIDE] OWASP Threat Modeling**
- يستخدم قبل التنفيذ وعند تغييرات التصميم والاعتماديات.

## 1.9 Secure SDLC / DevSecOps
- **[GUIDE] NIST SP 800-218 SSDF v1.1**
- يوفر ممارسات أمنية عبر SDLC: الإعداد، حماية البرمجيات، إنتاج برمجيات آمنة، والاستجابة للثغرات.
- يوجد Draft لـ SSDF v1.2؛ حتى يصبح نهائيًا لا يُعامل كمرجع نهائي حاكم.

## 1.10 أمن المعلومات والخصوصية
- **[STD] ISO/IEC 27001:2022** لإدارة مخاطر أمن المعلومات.
- **[STD] ISO/IEC 27701:2025** لإدارة معلومات الخصوصية إذا كانت القدرة تتعامل مع PII.
- لا يعني استخدام هذه الضوابط أن المشروع "معتمد ISO" ما لم توجد شهادة فعلية.

## 1.11 جاهزية الإنتاج والاعتمادية
- **[GUIDE] Google SRE — Production Readiness Review**
- **[GUIDE] Google SRE — SLI/SLO/Error Budgets**
- يستخدم لتحديد الاعتمادية من منظور المستخدم، لا مجرد uptime للخادم.

## 1.12 الرصد والملاحظة
- **[GUIDE] OpenTelemetry**
- يدعم Traces وMetrics وLogs وBaggage.
- يستخدم كمرجع لنموذج observability، وليس إلزامًا بأداة بعينها.

## 1.13 الوصول Accessibility
- **[WEB STANDARD] W3C WCAG 2.2**
- لواجهات المستخدم العامة عند الانطباق.
- الهدف المؤسسي المقترح: **WCAG 2.2 AA** حيث تنطبق متطلبات الويب.

## 1.14 أنظمة AI
- **[STD] ISO/IEC 42001:2023 — AI Management System**
- **[STD] ISO/IEC 25059:2023 — AI quality model** وهو الإصدار المنشور الحالي؛ حالته الرسمية في 2026 **International Standard to be revised**. لا يُفترض إصدار بديل أو محتواه قبل نشره رسميًا.
- **[GUIDE] NIST AI RMF 1.0** — Govern / Map / Measure / Manage؛ وهو قيد المراجعة في 2026.
- لا يُقال "مطابق للإصدار القادم" قبل نشره رسميًا.

## 1.15 الأنظمة المركبة والدرجات
- **[GUIDE/PRACTICE] OECD/JRC Handbook on Constructing Composite Indicators**
- يستخدم عند بناء مؤشر مركب أو Hero Score يحتاج normalization / weighting / sensitivity analysis.

## 1.16 تحديث الأنظمة القائمة
- **[PRACTICE] Strangler Fig**
- مفيد عندما يكون هناك legacy/monolith أو انتقال تدريجي ويكون الانطباق مناسبًا.
- **ليس قاعدة عامة لكل Brownfield**.

---

# 2. تعريف النجاح الحقيقي للقدرة

## 2.1 تعريف القدرة المكتملة

تُعتبر القدرة **PASS_ENGINEERING** فقط إذا ثبت جميع ما يلي بحسب الانطباق:

1. **Functional Completeness** — نفذت كل الوظائف المطلوبة داخل النطاق.
2. **Functional Correctness** — الناتج صحيح بالنسبة للمرجع/القواعد المحددة.
3. **Functional Appropriateness** — الناتج يخدم فعلًا هدف المستخدم.
4. **Requirements Traceability** — المتطلب مرتبط بالكود والاختبارات والدليل.
5. **Integration Correctness** — المسارات والاعتماديات متصلة فعليًا.
6. **Regression Safety** — لم تُكسر الوظائف القائمة ذات الصلة.
7. **Security Gate** — لا توجد مخاطر مانعة للإصدار وفق سياسة الأمن.
8. **Performance Gate** — تحقق SLO المناسب في بيئة ممثلة.
9. **Reliability Gate** — حالات الفشل المتوقعة والتعافي مدروسة ومختبرة.
10. **Observability Gate** — يمكن اكتشاف الفشل وتشخيصه.
11. **Data Quality Gate** — عند الاعتماد على البيانات، جودتها وصلاحيتها مثبتة.
12. **User Path Gate** — المستخدم أو المستهلك API يستطيع الوصول إلى النتيجة الصحيحة.
13. **Evidence Gate** — كل PASS له دليل قابل لإعادة التحقق.

## 2.2 تعريف الجاهزية الحية

لا تستخدم حالة **PASS_LIVE** إلا إذا ثبتت في **البيئة الحية/الإنتاجية الفعلية** وعلى المسار الحقيقي المقصود:

- النشر الفعلي ناجح.
- مسار المستخدم/المستهلك الحقيقي يعمل.
- بيانات واعتماديات الإنتاج المطلوبة متاحة.
- Authorization/Entitlements تعمل على المسار الحي عند الانطباق.
- SLI/SLO أو مؤشرات التشغيل المناسبة مقاسة من البيئة الحية.
- Logging/metrics/traces أو البديل المؤسسي متاح حسب الانطباق.
- خطط rollback/recovery متاحة ومناسبة للمخاطر.
- لا يوجد blocker خارجي يمنع الادعاء الحي.
- نتائج smoke/E2E الحية المطلوبة ناجحة.

البيئة الممثلة أو staging يمكن أن تدعم `PASS_ENGINEERING` وOperational Readiness، لكنها **لا ترقّي الدليل إلى PASS_LIVE** دون تحقق حي فعلي.

**ممنوع:** `tests passed` أو staging success ⇒ `PASS_LIVE`.

---

# 3. حالات التصنيف قبل البناء — Pre-Build State Classification

هذه **[POLICY]** سياسة تنفيذ للمشروع لمنع التدمير والتكرار والعمل العشوائي.

| الحالة | التعريف | التصرف |
|---|---|---|
| **GREENFIELD** | لا يوجد تنفيذ حقيقي | بناء من المتطلب |
| **EXISTING_VERIFIED** | يوجد تنفيذ ويحقق المتطلب كاملًا بدليل | إعادة استخدام؛ لا إعادة بناء |
| **PARTIAL_CANONICAL** | تنفيذ صحيح جزئيًا ويمكن استكماله | إكمال التنفيذ الحالي |
| **LEGACY/BROWNFIELD** | تنفيذ قائم يحتاج إصلاح/تحديث أو يملك دينًا تقنيًا | تقييم مخاطر + تعديل تدريجي غالبًا |
| **STUB_TEMPLATE** | هيكل/placeholder بلا سلوك حقيقي | NOT_COMPLETE ثم تنفيذ حقيقي |
| **DUPLICATE_ALIAS** | نفس القدرة مكررة أو alias | ربط بالـcanonical وحماية العقود |
| **CONFLICTING_IMPLEMENTATIONS** | أكثر من مصدر حقيقة أو منطق مختلف لنفس المفهوم | حل جذري قبل الإغلاق |
| **EXTERNAL_BLOCKED** | التنفيذ المحلي ممكن لكن الدليل الحي يعتمد على طرف خارجي | استكمال المحلي + وسم blocker بدقة |

### 3.1 قواعد قبل أي تغيير
يجب على Cursor/المطور:
- البحث عن التنفيذ الحالي.
- البحث عن callers/routes/templates/API consumers.
- البحث عن tests الحالية.
- البحث عن DB/data contracts.
- البحث عن duplicate implementations.
- تحديد مصدر الحقيقة canonical.
- تحديد المخاطر قبل الحذف أو إعادة البناء.
- عدم تعديل ملفات خارج النطاق دون سبب مثبت.

---

# 4. قرار Build / Extend / Refactor / Replace / Reuse

## 4.1 REUSE
يُختار إذا كان التنفيذ:
- يحقق المتطلب.
- له contract صالح.
- قابل للصيانة.
- لا توجد مشكلة أمن/بيانات/اعتمادية مانعة.

## 4.2 EXTEND
الافتراضي للتنفيذ الجزئي الصحيح.

## 4.3 REFACTOR
إذا كان السلوك صحيحًا لكن البنية تمنع تحقيق المتطلب أو الاختبار/الصيانة.

## 4.4 INCREMENTAL REPLACEMENT
عند legacy كبير أو شديد الاقتران عندما يكون التغيير التدريجي أقل مخاطرة.
يمكن استخدام Strangler Fig **حيث ينطبق**.

## 4.5 FULL REBUILD
لا يُتخذ بالانطباع. يجب توثيق:
- coupling.
- عدد consumers المتأثرين.
- test coverage.
- migration complexity.
- data compatibility.
- regression risk.
- security risk.
- maintenance cost.
- estimated change surface.
- rollback feasibility.

**[POLICY] ممنوع Big-Bang Rewrite بلا Impact Analysis وسبب موثق.**

---

# 5. دورة حياة القدرة من الفكرة إلى المستخدم

## المرحلة 1 — Intent
لكل قدرة:
- الهدف.
- المستخدم/المستهلك.
- المشكلة التي تحلها.
- النتيجة المراد الوصول إليها.
- ما لا يدخل في النطاق.
- الأثر عند الخطأ.

## المرحلة 2 — Requirements
تحديد:
- inputs.
- outputs.
- invariants.
- error behavior.
- permissions.
- freshness.
- performance class.
- privacy/data constraints.
- dependencies.
- acceptance criteria.

## المرحلة 3 — Architecture & Impact
تحديد:
- module/function/service.
- API/route.
- frontend entry.
- DB/data path.
- upstream/downstream.
- shared libraries.
- canonical owner.
- blast radius.
- threat model.
- rollback.

## المرحلة 4 — Implementation
- كود فعلي.
- لا placeholders مخفية.
- لا hardcoded نجاح.
- لا mock في مسار production.
- لا fallback يعطي مخرجًا مضللًا.
- لا swallowed exceptions تخفي الفشل.

## المرحلة 5 — Verification
- unit.
- contract.
- integration.
- negative tests.
- boundary tests.
- deterministic expected outputs حيث ينطبق.
- property/invariant tests حيث لا يصلح exact value.

## المرحلة 6 — Validation
هل النتيجة الفعلية تحقق حاجة المستخدم؟
لا يكفي أن تطابق schema.

## المرحلة 7 — User/E2E
- UI/API path.
- permissions.
- loading.
- errors.
- empty state.
- degraded state.
- mobile/accessibility إن انطبق.

## المرحلة 8 — Performance & Reliability
- SLO.
- load.
- concurrency.
- failure behavior.
- timeouts/retries.
- rate limits.
- fallback safety.

## المرحلة 9 — Security/Privacy
- authn.
- authz.
- entitlement.
- input validation.
- secrets.
- sensitive data.
- abuse.
- auditability.

## المرحلة 10 — Deploy
- migrations.
- feature flags/canary إن لزم.
- config/secrets.
- smoke tests.
- rollback path.

## المرحلة 11 — Operate
- telemetry.
- SLI/SLO.
- alerts.
- incident visibility.
- data freshness health.

## المرحلة 12 — Evidence & Close
لا PASS دون دليل.

---

# 6. Expected Output — الصيغة الصحيحة

**[POLICY]** كل قدرة لها Oracle أو معيار تحقق، لكن ليس بالضرورة رقمًا واحدًا.

أنواع Expected Output المقبولة:

1. **Exact value** — عندما تكون العملية حتمية.
2. **Tolerance range** — حسابات عددية/مالية.
3. **Schema/contract** — API.
4. **Invariant** — مثل total ≥ 0 أو conservation rule.
5. **State transition** — حالة A → B بشروط.
6. **Classification set** — قيمة من enum محدد.
7. **Monotonic/relational property** — علاقة متوقعة.
8. **Golden dataset** — مدخلات ثابتة مع نتائج معروفة.
9. **Rubric** — AI غير الحتمي.
10. **Statistical acceptance** — نماذج احتمالية.

### ممنوع
- `success=true` وحده.
- HTTP 200 وحده.
- "لا يوجد exception" وحده.
- وجود DOM element وحده.
- snapshot شكلي بلا تحقق من المعنى.

---

# 7. القالب الخماسي — النسخة المؤسسية المطوّرة

القالب الخماسي يبقى واجهة الإغلاق العليا، لكن كل عمود يحتوي Gates داخلية.

| # | العمود | المطلوب |
|---|---|---|
| 1 | **الهدف الداخلي** | Completeness + Correctness + Appropriateness + traceability |
| 2 | **النتيجة الخارجية** | Acceptance Criteria + Expected/Actual + data quality |
| 3 | **مسار المستخدم/الاستهلاك** | E2E + UI/API + permissions + context of use + accessibility حيث ينطبق |
| 4 | **الأمان والجودة التشغيلية** | Security + reliability + performance + maintainability + privacy + observability |
| 5 | **الجاهزية والإثبات** | deployment status + evidence + independent verification + blockers + rollback |

## 7.1 إضافة إلزامية: Evidence Fields
كل عمود يجب أن يحتوي:
- `status`
- `evidence`
- `evidence_location`
- `verification_method`
- `environment`
- `commit/version`
- `timestamp`
- `blocker_if_any`

**No evidence = No PASS.**

---

# 8. مصفوفة التتبع RTM

لكل قدرة يجب وجود سجل:

`Requirement → Acceptance Criterion → Code → Test → Runtime Route → Data Source → Evidence → Status`

وعند القدرة التي تظهر للمستخدم:
`... → UI/API Consumer → User Outcome`

وعند AI:
`... → Model Version → Feature/Data Version → Evaluation Baseline`

الحد الأدنى العملي لسجل القدرة، مع السماح بإعادة استخدام أي Artifact حاكم يؤدي الوظيفة نفسها، هو:
- `capability_id` / `official_batch`؛
- `canonical_requirement_or_objective`؛
- `state_classification`؛
- `canonical_decision`؛
- `engineering_status`؛
- `canonical_implementation` و`binding/module/function` حسب الانطباق؛
- `input/data_source`؛
- `semantic_acceptance_or_oracle`؛
- `actual_consumer_path`؛
- `tested_source_sha`؛
- `evidence_reference`؛
- `live_status`؛
- `assurance_status`؛
- `notes/exceptions` عند الحاجة.

**[POLICY]** لا يجوز أن يكون الـoracle أو expected result مجرد إعادة استدعاء لنفس منطق الإنتاج محل الاختبار بطريقة self-fulfilling عندما يكون مرجع مستقل/ثابت/محك خارجي ممكنًا وماديًا لصحة القدرة.

---

# 9. التكرار — الاكتشاف الشامل

لا يقتصر duplicate على تشابه الاسم.

## 9.1 Functional Duplicate
اختبر:
- الهدف.
- inputs.
- output contract.
- business/user value.
- consumer.
- time horizon.
- data source.
- confidence semantics.

## 9.2 Logic Duplicate
نفس المنطق في موضعين.

## 9.3 Data Duplicate
نفس الحقيقة مخزنة/مشتقة بأكثر من مصدر دون حوكمة.

## 9.4 Route/API Duplicate
أكثر من endpoint يؤدي نفس الوظيفة بلا contract مبرر.

## 9.5 UI Duplicate
واجهتان تقدمان نفس الوظيفة بلا اختلاف استخدام حقيقي.

## 9.6 Calculation Duplicate
نفس المؤشر بمعادلتين مختلفتين — خطر Source-of-Truth.

## 9.7 Model Duplicate
نماذج/قواعد متعددة لنفس القرار دون policy واضحة.

## 9.8 Semantic Duplicate
أسماء مختلفة لكن القيمة الفعلية واحدة.

---

# 10. الحكم على التكرار

| النتيجة | المعنى |
|---|---|
| **DISTINCT** | قيمة أو عقد أو استخدام مختلف جوهريًا |
| **PARTIAL_OVERLAP** | جزء مشترك لكن توجد مسؤوليات مختلفة |
| **DUPLICATE_CONFIRMED** | نفس الحاجة/المخرج/القيمة فعليًا |
| **CONFLICTING_DUPLICATE** | تكرار مع نتائج مختلفة — أخطر حالة |
| **ALIAS** | اسم/ID مختلف لنفس canonical implementation |

**ممنوع الحذف بمجرد تشابه الاسم.**

---

# 11. العلاج الجذري للتكرار

## 11.1 قبل العلاج — Impact Analysis
افحص:
- callers.
- routes.
- UI.
- tests.
- database.
- scheduled jobs.
- API consumers.
- integrations.
- entitlements/billing.
- analytics.
- audit logs.
- docs.
- backwards compatibility.

## 11.2 العلاج حسب الحالة

### A. Canonicalization
تحديد مصدر حقيقة واحد.

### B. Alias
الإبقاء على identifiers العامة مع توجيهها إلى canonical.

### C. Extract Shared Core
فصل المنطق المشترك، مع الحفاظ على contracts المختلفة.

### D. Parameterization
عندما الاختلاف مجرد parameters.

### E. Merge
عندما لا توجد قيمة مستقلة حقيقية.

### F. Deprecate
للعقود العامة:
- warning.
- migration path.
- sunset policy.
- consumer inventory.

### G. Eliminate
فقط بعد إثبات عدم وجود consumer أو بعد migration.

### H. Resolve Conflicting Truth
عندما نتيجتان لنفس المؤشر مختلفتان:
1. تحديد المرجع الصحيح.
2. توثيق formula/data lineage.
3. golden test.
4. تحويل كل consumers للـcanonical.
5. منع الحساب البديل.

---

# 12. شروط إغلاق مشكلة التكرار

لا تعتبر المشكلة محلولة إلا إذا:
- يوجد canonical واحد.
- لا توجد نتائج متعارضة.
- تم تحويل كل callers.
- اختبارات regression ناجحة.
- لا يوجد broken public contract.
- تم تحديث RTM.
- تم تحديث docs.
- تم تحديث telemetry.
- حُذف القديم أو وُسم deprecated بخطة.
- تم منع عودة duplicate عبر architecture/code guard حيث يمكن.

---

# 13. الأبطال الستة — Hero Aggregation Standard

**[BLACKDARK PRODUCT POLICY]** الأبطال الستة هم **Primary User Decision Surfaces** للقدرات التي تخص تجربة القرار، مع السماح بالأسطح الداعمة اللازمة مثل APIs وB2B feeds وexports وresearch workspaces وsettings وdeveloper/admin/operational surfaces عندما تكون لها وظيفة مستقلة ومبررة ولا تخلق product fragmentation أو مصدر حقيقة موازٍ.

## 13.1 الخريطة الإلزامية
لكل Hero:
`Hero → feeding capabilities → module.function → data lineage → transformations → decision rule → user explanation`

## 13.2 ليس كل input وزنًا
كل قدرة مغذية تُصنف:
- additive score.
- confidence modifier.
- veto.
- gating condition.
- regime filter.
- risk cap.
- data-quality gate.
- contextual modifier.

**ممنوع فرض weighted average تلقائيًا.**

## 13.3 Normalization
وثّق:
- لماذا التطبيع مطلوب.
- الطريقة.
- domain/range.
- outlier behavior.
- missing values.
- sign/direction.
- clipping.
- time normalization.

لا تستخدم log transform أو z-score أو min-max لمجرد أنها شائعة.

## 13.4 Weighting
- rationale.
- calibration source.
- stability.
- update policy.
- version.

Equal weights مسموحة إذا كانت **قرارًا موثقًا ومختبرًا** وليست افتراضًا.

## 13.5 Independence / Correlation
لا تعد إشارتين مستقلتين لمجرد أنهما دالتان مختلفتان.
افحص:
- common data sources.
- shared features.
- derivation lineage.
- correlation over representative regimes.
- duplicated information content.

## 13.6 Sensitivity Analysis
لكل Hero:
- remove-one-factor.
- perturb weight.
- perturb input.
- missing signal.
- contradictory signals.
- stale signal.
- extreme signal.

سجل:
- هل القرار ينقلب؟
- هل confidence يتغير؟
- هل يوجد single-point dominance؟

## 13.7 Explainability
المستخدم يجب أن يستطيع فهم:
- ما الاتجاه النهائي؟
- ما العوامل الرئيسية؟
- ما العوامل المعارضة؟
- ما درجة الثقة؟
- ما freshness؟
- هل هناك بيانات ناقصة؟

---

# 14. جودة البيانات — Data Quality Gate

أي قدرة مالية/تحليلية لا يمكن أن تكون صحيحة إذا كانت بياناتها غير صحيحة.

## 14.1 خصائص إلزامية حسب الانطباق
- accuracy.
- completeness.
- consistency.
- credibility.
- currentness/freshness.
- precision.
- traceability.
- availability.
- uniqueness.
- validity.

## 14.2 Data Contract
لكل source:
- schema.
- types.
- units.
- timezone.
- timestamps.
- missing behavior.
- precision.
- update frequency.
- freshness threshold.
- provenance.
- licensing/usage constraints عند الحاجة.

## 14.3 Freshness
يجب عدم عرض بيانات stale كأنها live.
الحالات المقترحة:
- LIVE.
- DELAYED.
- STALE.
- UNAVAILABLE.
- PARTIAL.

## 14.4 Timestamp Integrity
للبيانات المالية:
- event time ≠ ingestion time.
- timezone موحد.
- clock assumptions موثقة.
- ordering.
- late events.
- duplicate events.

## 14.5 Numerical Integrity
- Decimal/precision حيث المال.
- rounding policy.
- unit conversions.
- overflow/underflow.
- NaN/Infinity.
- division by zero.
- negative/unknown distinction.

---

# 15. الاختبارات المالية/الكمية

عند الإشارات أو backtests:
- منع lookahead bias.
- منع leakage.
- فحص survivorship bias حيث ينطبق.
- فحص selection bias.
- timestamp alignment.
- out-of-sample/holdout حيث ينطبق.
- fees/slippage assumptions إذا كانت النتيجة تعتمد عليها.
- corporate/market data revisions إذا كانت ذات صلة.
- regime coverage.

**ممنوع استخدام معلومة لم تكن متاحة فعليًا عند وقت القرار التاريخي.**

---

# 16. AI / ML / Generative AI

## 16.1 تصنيف صريح
كل قدرة تحمل "AI" تُصنف:
- RULE_BASED.
- STATISTICAL_MODEL.
- ML_MODEL.
- LLM/GENERATIVE.
- HYBRID.

لا AI-washing.

## 16.2 Model Registry Minimum
- model/version.
- code version.
- feature version.
- training/evaluation data snapshot reference.
- configuration.
- prompt/template version للـLLM.
- deployment date.
- rollback target.

## 16.3 Evaluation
- baseline.
- target metrics.
- slice evaluation.
- edge cases.
- robustness.
- confidence/calibration حيث ينطبق.
- harmful/invalid output tests بحسب النوع.

## 16.4 Deterministic vs Stochastic
للـAI الاحتمالي، Expected Output لا يشترط تطابق النص.
يمكن استخدام:
- schema.
- rubric.
- factual constraints.
- prohibited claims.
- grounded evidence requirement.
- score thresholds.
- repeated-run stability range.

## 16.5 Drift
افصل:
- data drift.
- feature drift.
- prediction/output drift.
- concept drift.
- performance degradation.

PSI/KS/JS أدوات ممكنة، وليست إثباتًا وحيدًا للصحة.

## 16.6 AI Monitoring
- distribution shifts.
- error rate.
- abstention/fallback.
- confidence.
- latency/cost.
- quality sample audits.
- model/version attribution.

## 16.7 Human/Operational Controls
بحسب خطورة القرار:
- explainability.
- override/abstain.
- escalation.
- audit trail.
- rollback.

---

# 17. الأمن — Security Gate

## 17.1 Threat Model قبل البناء أو التغيير الجوهري
أسئلة إلزامية:
1. ماذا نبني؟
2. ماذا يمكن أن يحدث بشكل خاطئ/ضار؟
3. كيف سنمنعه أو نخففه؟
4. كيف نثبت أن الحماية تعمل؟

## 17.2 Authentication / Authorization
- no implicit trust.
- server-side authorization.
- object-level authorization.
- function-level authorization.
- tenant isolation.
- entitlement قبل إرجاع البيانات/تنفيذ الفعل.

## 17.3 Input/Output
- validation.
- injection prevention.
- encoding.
- file handling.
- SSRF considerations.
- deserialization risk.
- outbound data controls.

## 17.4 Secrets
- لا secrets في الكود/الـlogs.
- rotation path.
- least privilege.
- environment separation.

## 17.5 API
- auth.
- rate limiting.
- object authorization.
- resource consumption.
- inventory.
- versioning.
- safe error responses.

## 17.6 Supply Chain
- dependencies inventory.
- known critical vulnerabilities.
- pinned/controlled versions حسب المشروع.
- provenance/SBOM حيث مستوى المخاطر يتطلب.

## 17.7 Security Release Policy — سياسة مشروع
- **Critical:** blocker.
- **High:** blocker افتراضيًا؛ الاستثناء يحتاج risk acceptance موثق.
- **Medium/Low:** tracked وعلاج حسب الخطر والسياق.
- لا يقال "ASVS compliant" دون تحديد scope/version/evidence.

---

# 18. الخصوصية والبيانات الحساسة

عند PII أو بيانات مستخدم حساسة:
- data classification.
- purpose limitation.
- minimum necessary data.
- retention.
- deletion.
- access audit.
- encryption in transit/at rest حسب السياق.
- masking في logs.
- export/subject rights حسب النظام القانوني المنطبق.
- عدم استخدام بيانات production في test بلا حماية مناسبة.

---

# 19. الأداء — Performance Standard

## 19.1 لا تستخدم Average فقط
القياس على:
- p50.
- p90/p95.
- p99 حيث يلزم.
- error rate.
- throughput.
- concurrency.
- saturation.

## 19.2 الفئات الزمنية — سياسة المشروع
الأرقام التالية **targets ابتدائية داخلية [POLICY] وليست حدودًا مفروضة من ISO/IEC 25010 أو Google SRE أو أي معيار دولي**:

| الفئة | هدف أولي |
|---|---|
| قراءة/تفاعل مباشر خفيف | **p95 ≤ 500 ms** إن كان معماريًا واقعيًا |
| تحليل/حساب متوسط | **p95 ≤ 2 s** |
| AI/تفسير/توصية ثقيلة | **p95 ≤ 5 s** أو UX async/progress إذا تجاوزها التصميم عمدًا |

ويجب تخصيصها حسب:
- قيمة المستخدم.
- حجم البيانات.
- التكلفة.
- dependency latency.
- context of use.

## 19.3 SLO
لكل مسار حرج:
- SLI definition.
- SLO target.
- measurement window.
- error budget.
- data source.
- owner.
- review cadence.

## 19.4 Load
اختبر:
- expected load.
- peak.
- burst.
- sustained load.
- concurrency.
- rate limit.
- queue behavior.
- resource ceiling.

## 19.5 Cold vs Warm
إذا كانت المنصة serverless أو model startup:
- cold-start منفصل.
- warm latency منفصل.

---

# 20. الاعتمادية والمرونة

## 20.1 Dependency Failure Matrix
لكل dependency:
- timeout.
- connection failure.
- 4xx.
- 429.
- 5xx.
- malformed payload.
- stale payload.
- partial payload.
- schema change.

## 20.2 الاستجابة الصحيحة
تحديد صريح:
- retry أو لا.
- backoff.
- circuit breaker حيث ينطبق.
- fallback.
- cache.
- fail-open / fail-closed.
- user message.

## 20.3 لا fallback مضلل
إذا كانت البيانات قديمة أو ناقصة لا تُعرض كأنها حقيقة حية.

## 20.4 Idempotency
لعمليات write/financial/state transitions حيث يلزم:
- idempotency key أو equivalent.
- duplicate request behavior.
- retry safety.

## 20.5 Concurrency
اختبر race conditions عند:
- counters.
- balances.
- subscriptions.
- jobs.
- state transitions.

---

# 21. Observability — بوابة مستقلة

لا تعتبر capability production-ready إذا تعطلها لا يمكن اكتشافه.

الحد الأدنى حسب الانطباق:
- structured logs.
- correlation/request ID.
- metrics.
- traces للمسارات الموزعة.
- error reporting.
- health/readiness.
- dependency latency/error.
- data freshness.
- model version في AI telemetry.

## 21.1 Logs
يجب ألا تحتوي:
- passwords.
- raw secrets.
- sensitive tokens.
- PII غير ضروري.

## 21.2 Alerts
الـalert يجب أن يرتبط بأثر مستخدم أو SLO قدر الإمكان، لا مجرد ارتفاع metric بلا معنى.

---

# 22. UX / Interaction / Accessibility

القدرة لا تحقق هدفها إذا كانت صحيحة داخليًا لكن المستخدم لا يستطيع فهمها أو استخدامها.

اختبر:
- discoverability.
- labels.
- loading state.
- empty state.
- error state.
- retry.
- stale-data indication.
- confidence/explanation.
- responsive behavior.
- keyboard/focus.
- WCAG 2.2 AA حيث ينطبق.
- localization formatting: أرقام/تواريخ/عملات إن كانت المنصة متعددة اللغات.

---

# 23. API / Contract Quality

- schema واضح.
- versioning.
- backwards compatibility.
- status/error semantics.
- pagination.
- rate limits.
- freshness metadata عند البيانات.
- source/provenance metadata حيث يلزم.
- idempotency للعمليات المناسبة.
- contract tests.
- consumer impact قبل breaking change.

---

# 24. قاعدة البيانات والمهاجرات

أي قدرة تغير schema تحتاج:
- migration plan.
- compatibility مع البيانات الحالية.
- defaults/nullability.
- indexes.
- migration performance.
- locking impact.
- backward/forward compatibility.
- rollback أو roll-forward strategy.
- test on representative data.

**ممنوع اعتبار نجاح migration على DB فارغة دليلًا كافيًا للإنتاج.**

---

# 25. Deployment / Release Safety

بحسب الخطر:
- feature flag.
- canary.
- staged rollout.
- smoke test.
- rollback.
- release note.
- migration sequencing.
- configuration validation.
- secret readiness.

---

# 26. Regression Gate

بعد كل تعديل:
1. focused tests.
2. related module tests.
3. integration/contract tests.
4. regression suite المناسبة.
5. full suite حيث feasible أو عند التغيير عالي التأثير.

إذا فشلت اختبارات قديمة:
- لا تُحذف لتخضير CI.
- حدد هل الاختبار قديم أم التغيير خاطئ.
- وثق القرار.

---

# 27. Maintainability Gate

- no unnecessary duplication.
- clear ownership.
- modular boundaries.
- complexity ليست مفرطة.
- dead code removed/deprecated بأمان.
- naming consistent.
- docs/comments للمنطق غير البديهي.
- configuration خارج الكود عند الحاجة.
- tests maintainable.

---

# 28. Operational Readiness

قبل `PASS_LIVE`:
- deployment known.
- health checks.
- monitoring.
- alerts.
- runbook للمسارات الحرجة.
- owner/escalation.
- backup/restore حيث توجد بيانات مهمة.
- rollback.
- dependency status.
- capacity.
- known limitations.
- external blockers = 0 أو معلنة تمنع Live.

---

# 29. نموذج الحالة والإغلاق متعدد الأبعاد

لا يُستخدم قاموس واحد يخلط حالة التنفيذ الأصلية بالقرار الكانونيكال أو الإغلاق الهندسي أو الحالة الحية أو الضمان. يجب تسجيل الأبعاد التالية بصورة مستقلة، وفق القواميس الحاكمة في الأقسام 3 و104 و88 وما يرتبط بها:

1. **State Classification** — حالة التنفيذ/البنية الأصلية والحالية.
2. **Canonical Decision** — reuse / keep distinct / merge / alias / deprecate / eliminate / resolve truth حسب الانطباق.
3. **Engineering Status** — مثل `PASS_ENGINEERING`, `PARTIAL`, `FAIL`, `NOT_APPLICABLE`.
4. **Live Status** — مثل `PASS_LIVE`, `AWAITING_DEPLOY`, `BLOCKED_EXTERNAL`, `NOT_CLAIMED`.
5. **Assurance Status** — مثل `PENDING_INDEPENDENT_ASSURANCE`, `ASSURANCE_READY` أو الحالة الحاكمة المقابلة في قسم الضمان.
6. **External Dependency Status** — عند الحاجة: لا يوجد / مزود مدفوع / مراجعة قانونية / تصديق بشري / بيئة إنتاجية أو اعتماد خارجي آخر.

### قاعدة
لا تستخدم `PASS_LIVE` مع:
- deploy غير مثبت؛
- secret مفقود؛
- source غير متاح؛
- test حقيقي غير منفذ؛
- blocker خارجي؛
- route/consumer path مادي غير مجرب.

لا يجوز أن يحل label محلي أو tracking label محل أي بُعد حاكم من الأبعاد أعلاه.

---

# 30. Evidence Standard

## 30.1 دليل مقبول
- test name + result.
- command + exit code.
- API request/response sanitized.
- DB query/result.
- UI/E2E test.
- metric snapshot.
- deployment/release identifier.
- commit SHA.
- log/trace reference.
- security scan result.
- migration result.

## 30.2 دليل غير كافٍ
- "راجعت الكود".
- "يبدو صحيحًا".
- "الدالة موجودة".
- "المسار موجود".
- "test file موجود".
- "success=true" بلا تحقق semantic.

---

# 31. Git / Change Evidence

كل إغلاق دفعة يجب أن يسجل:
- commit SHA.
- changed files.
- migrations.
- tests executed.
- passed/failed/skipped.
- security checks.
- deployment state.
- dirty working tree status.
- unresolved blockers.

---

# 32. Independent Verification

Google SRE PRR مفهوم تنظيمي وليس شرطًا أن توجد لجنة بشرية لكل قدرة.

**سياسة المشروع البديلة عند العمل بفريق صغير:**
- implementer evidence.
- automated tests.
- second independent review عندما تكون القدرة حرجة أو قبل الإغلاق الحي.
- user/external verification فقط عندما يتطلب الأمر credential/account/provider/action لا يمكن للوكيل تنفيذه.

---

# 33. قواعد خاصة بالعمل مع Cursor / Coding Agent

1. **لا تغيّر خارج النطاق دون سبب.**
2. **لا تحذف كودًا موجودًا قبل impact analysis.**
3. **لا تختلق دليلًا أو test execution.**
4. **لا تعتبر code presence تنفيذًا مكتملًا.**
5. **لا تعتبر mock دليل production.**
6. **لا تجعل fallback العام يمر كنجاح.**
7. **لا تغيّر expected tests فقط لكي تمرر تنفيذًا خاطئًا.**
8. **لا تعلن LIVE إذا البيئة غير متاحة.**
9. **لا تسأل المستخدم عن معلومة يمكن استنتاجها آليًا من repo.**
10. **إذا احتاجت خطوة خارجية فعلًا، أغلق كل الممكن محليًا وحدد خطوة المستخدم الوحيدة المتبقية.**
11. **لا تُعد تنفيذ قدرة موجودة صحيحة.**
12. **لا تنشئ duplicate جديدًا إذا يوجد canonical صالح.**
13. **لا تقبل TODO/placeholder داخل مسار production دون وسم NOT_COMPLETE.**
14. **لا تعتبر generic router/handler عيبًا بحد ذاته؛ الممنوع أن يكون بديلًا عن semantic implementation حقيقي أو أن يجعل قدرات مختلفة مجرد أسماء/metadata فوق سلوك واحد.**
15. **لا تشترط unique code لكل capability؛ اسمح بـshared core/primitives/adapters عندما يكون reuse صحيحًا معماريًا، مع إثبات semantic correctness والتميّز أو العلاقة الكانونيكال لكل قدرة.**
16. **لا تقبل aggregate PASS يخفي ID غير مثبت دلاليًا أو consumer path مادي غير مختبر.**

---

# 34. Definition of Done — البوابة النهائية

يُغلق كل عنصر عند انطباق البنود التالية:

### A. Requirement
- الهدف واضح.
- scope واضح.
- acceptance واضح.
- risk واضح.

### B. Architecture
- location/owner واضح.
- dependencies معروفة.
- impact معروف.
- canonical source معروف.

### C. Implementation
- السلوك كامل.
- لا stub.
- لا duplicate غير محسوم.

### D. Correctness
- expected vs actual.
- negative/boundary.
- financial precision عند الحاجة.

### E. Data
- quality.
- freshness.
- provenance.
- timestamps.

### F. Integration
- backend/runtime.
- API.
- frontend/consumer.

### G. UX
- user can complete intended task.
- errors/degraded states واضحة.
- accessibility حيث ينطبق.

### H. Security
- threat model.
- authn/authz.
- input.
- secrets.
- vulnerabilities.

### I. Reliability
- dependency failure.
- retry/timeout.
- fallback.
- idempotency/concurrency حيث يلزم.

### J. Performance
- p95/p99 المناسب.
- concurrency/load.
- SLO.

### K. Observability
- logs/metrics/traces.
- alerts/health.

### L. Release
- migration.
- deploy.
- rollback.

### M. Regression
- existing behavior protected.

### N. Evidence
- all PASS claims evidenced.

### O. User Outcome
- النتيجة تحقق الهدف النهائي الفعلي للقدرة.

---

# 35. نموذج تقرير الإغلاق لكل قدرة

```text
Capability:
Classification:
Objective:
User/Consumer:
Risk Class:

Requirement:
Acceptance Criteria:
Expected Output Type:
Expected Output:

Canonical Implementation:
Files/Functions:
Runtime Route:
UI/API Entry:
Data Sources:
Dependencies:

Duplicate Check:
Canonical Decision:
Impact Analysis:

Five-Gate Closure:
1) Internal Objective:
   Status:
   Evidence:

2) External Result:
   Status:
   Evidence:

3) User/API Path:
   Status:
   Evidence:

4) Security & Operational Quality:
   Status:
   Evidence:

5) Readiness & Evidence:
   Status:
   Evidence:

Data Quality:
Security:
Performance:
Reliability:
Observability:
Regression:
Deployment:
Rollback:
AI Controls (if applicable):
Hero Mapping (if applicable):

Commit:
Tests:
Environment:
External Blockers:

FINAL STATUS:
PASS_ENGINEERING / PASS_LIVE / PARTIAL / FAIL / BLOCKED_EXTERNAL / ...
```

---

# 36. نموذج Hero Closure

```text
Hero:
Purpose:
User Decision Supported:

Feeding Capabilities:
- capability → function → source → freshness → role

Aggregation Roles:
- score / gate / veto / confidence / risk cap / context

Normalization:
Weighting/Rules:
Missing-data Policy:
Conflicting-signal Policy:
Correlation/Independence Check:
Sensitivity Results:
Explainability Output:
Latency SLO:
Reliability:
Security:
User Path:
Evidence:
Version:
FINAL STATUS:
```

---

# 37. معيار الأداء المقترح — النسخة المنقحة

بدل استخدام رقم واحد:
- Class A interactive: p50 + p95 + p99.
- Class B analysis: p50 + p95 + error rate.
- Class C AI: p50 + p95 + timeout/fallback + cost guard.
- background jobs: completion SLO وليس browser latency.

### Target أولي
- direct lightweight: p95 ≤ 500 ms.
- standard analysis: p95 ≤ 2 s.
- AI response: p95 ≤ 5 s إن كانت synchronous؛ وإلا تصميم async/progress.
- targets تُراجع من telemetry الفعلية وتجربة المستخدم.

هذه **سياسة أداء داخلية** وليست ادعاء أنها حدود معيار دولي.

---

# 38. مستويات المخاطر

| المستوى | أمثلة | تشدد البوابات |
|---|---|---|
| L1 | عرض معلومات غير حساسة | أساسي |
| L2 | تحليل/توصية للمستخدم | بيانات + تفسير + reliability أعلى |
| L3 | حساب مالي/portfolio/permissions | security + precision + audit |
| L4 | مؤسسي/مالي حساس/تنفيذ state-changing | أعلى مستوى + independent verification + rollback + audit |

---

# 39. قواعد عدم تضخيم الإغلاق

- alias لا يحسب كتنفيذ مستقل جديد.
- duplicate المدمج لا يضاعف الإنجاز.
- test واحد يغطي عنصرين فقط إذا كان traceability صريحًا.
- shared core يمكن إعادة استخدامه لكن كل capability تحتاج validation لهدفها الخاص.
- نفس endpoint لا يثبت كل consumer path.
- نفس model لا يثبت كل use-case.

---

# 40. ما الذي يعني "تحقيق الهدف كاملًا دون قصور"؟

لا يعني الكمال النظري المطلق أو استحالة ظهور عيب مستقبلًا.
يعني وجود **دليل كافٍ ومحدد وقابل لإعادة التحقق** بأن:
- النطاق المتفق عليه كامل.
- الحالات المهمة مغطاة.
- النتائج صحيحة.
- المستخدم يستطيع الاستفادة.
- المخاطر المعروفة عولجت.
- الفشل لا يتحول إلى نجاح مضلل.
- القياس التشغيلي موجود.
- أي limitation متبقية معلنة وليست مخفية.

---

# 41. مراجعة دورية بعد الإطلاق

القدرة لا تتوقف عن التقييم بعد PASS_LIVE.

راقب:
- SLO.
- error budget.
- incidents.
- data freshness.
- source/schema changes.
- model drift.
- security vulnerabilities.
- dependency versions.
- user failure points.
- performance regression.

عند تغير افتراض جوهري:
- reopen verification.
- لا تعتمد على PASS تاريخي.

---

# 42. ترتيب التنفيذ الإلزامي المقترح

1. Inventory.
2. Classification.
3. Duplicate/canonical analysis.
4. Requirements.
5. Impact/threat analysis.
6. Architecture.
7. Implementation.
8. Unit/contract.
9. Integration.
10. Data validation.
11. E2E/user outcome.
12. Security.
13. Reliability/failure.
14. Performance/load.
15. Observability.
16. Regression.
17. Deploy/migration.
18. Live smoke.
19. Evidence.
20. Independent/final review.
21. Close.

---

# 43. Master Rule Set — نسخة قصيرة لإلزام Cursor

```text
For every capability/feature, do not code first.

1) Inspect the repository and classify the current state:
GREENFIELD / EXISTING_VERIFIED / PARTIAL_CANONICAL / LEGACY_BROWNFIELD /
STUB_TEMPLATE / DUPLICATE_ALIAS / CONFLICTING_IMPLEMENTATIONS / EXTERNAL_BLOCKED.

2) Identify the canonical implementation and perform duplicate + impact analysis
before creating, deleting, merging, rewriting, or migrating anything.

3) Define objective, user, inputs, outputs, acceptance criteria, expected-output
oracle, data/freshness rules, dependencies, security requirements, performance
class, reliability behavior and runtime/user path.

4) Reuse correct existing behavior. Extend partial canonical behavior by default.
Never perform a broad rewrite without evidence-based impact analysis.

5) Implement the smallest correct production change. No placeholder, fake success,
silent fallback, production mock, or hidden TODO may receive PASS.

6) Verify correctness with unit + contract + integration + negative/boundary tests,
and compare actual results to a meaningful oracle. HTTP 200 or success=true is
not semantic proof.

7) Verify data quality, timestamps, freshness, provenance and numerical precision
where applicable.

8) Verify the real UI/API/user path, authorization/entitlements, errors, empty/
degraded states and accessibility where applicable.

9) Apply security threat modeling + OWASP ASVS/API controls + secure-SDLC checks.
No critical security issue may pass release.

10) Verify dependency failure modes, timeouts, retries, stale/partial data,
idempotency/concurrency where applicable.

11) Measure latency using percentiles, not average only; define SLI/SLO and perform
representative load/concurrency testing for critical paths.

12) Ensure production observability: structured logs, metrics, traces where useful,
health/freshness signals and actionable alerting.

13) Verify migrations, deployment configuration, rollback/roll-forward and
regression safety.

14) For AI/ML: declare whether it is truly model-based; version model/data/features/
prompts, evaluate probabilistic quality correctly, monitor drift/performance and
support rollback/abstention as appropriate.

15) For Hero aggregation: map all feeding capabilities, distinguish score/gate/veto/
confidence roles, document normalization/weights, test correlation, missing data,
conflicting signals and sensitivity; expose meaningful explanation.

16) Close using the five-gate template, but every PASS must include evidence,
environment and commit/version.

17) Use:
PASS_ENGINEERING only for verified engineering completion.
PASS_LIVE only after live/deployed validation.
No evidence = no PASS.
No production validation = no PASS_LIVE.
```

---

# 44. مصادر رسمية/موثقة

> الروابط أدناه مراجع تعريفية رسمية أو موثوقة. لا يُفهم وجودها على أنه شهادة امتثال للمشروع.

1. ISO/IEC/IEEE 12207:2026  
   https://www.iso.org/standard/90219.html

2. ISO/IEC 25010:2023  
   https://www.iso.org/standard/78176.html

3. ISO/IEC 25019:2023  
   https://www.iso.org/standard/78177.html

4. ISO/IEC/IEEE 29148:2018  
   https://www.iso.org/standard/72089.html

5. ISO/IEC/IEEE 29119-2:2021  
   https://www.iso.org/standard/79428.html

6. ISO/IEC/IEEE 42010:2022  
   https://www.iso.org/standard/74393.html

7. ISO/IEC 25012:2008  
   https://www.iso.org/standard/35736.html

8. ISO/IEC 27001:2022  
   https://www.iso.org/standard/27001

9. ISO/IEC 27701:2025  
   https://www.iso.org/standard/27701

10. ISO/IEC 42001:2023  
    https://www.iso.org/standard/42001

11. ISO/IEC 25059:2023  
    https://www.iso.org/standard/80655.html

12. NIST SSDF  
    https://csrc.nist.gov/projects/ssdf

13. NIST AI RMF  
    https://www.nist.gov/itl/ai-risk-management-framework

14. OWASP ASVS  
    https://owasp.org/www-project-application-security-verification-standard/

15. OWASP Threat Modeling  
    https://owasp.org/www-project-threat-modeling/

16. OWASP API Security  
    https://owasp.org/www-project-api-security/

17. Google SRE — Implementing SLOs  
    https://sre.google/workbook/implementing-slos/

18. Google SRE — Production Readiness Review  
    https://sre.google/sre-book/evolving-sre-engagement-model/

19. OpenTelemetry Signals  
    https://opentelemetry.io/docs/concepts/signals/

20. WCAG 2.2  
    https://www.w3.org/TR/WCAG22/

21. AWS Strangler Fig Pattern  
    https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html

22. OECD Handbook on Constructing Composite Indicators  
    https://www.oecd.org/en/publications/handbook-on-constructing-composite-indicators-methodology-and-user-guide_9789264043466-en.html

---

# 45. القرار المؤسسي النهائي

هذا المرجع يعتمد المبدأ التالي:

> **القدرة ليست "كودًا"، بل سلسلة قيمة كاملة تبدأ بمتطلب صحيح وتنتهي بنتيجة صحيحة ومفيدة وآمنة وموثوقة وقابلة للرصد تصل إلى المستخدم في البيئة المستهدفة.**

والمعيار النهائي للإغلاق هو:

**RIGHT REQUIREMENT  
→ RIGHT CANONICAL DESIGN  
→ RIGHT IMPLEMENTATION  
→ RIGHT DATA  
→ RIGHT RESULT  
→ RIGHT USER PATH  
→ RIGHT SECURITY  
→ RIGHT PERFORMANCE  
→ RIGHT RELIABILITY  
→ RIGHT OBSERVABILITY  
→ RIGHT DEPLOYMENT  
→ REPRODUCIBLE EVIDENCE**

وأي حلقة ناقصة تُمنع معها تسمية **PASS_LIVE**.

---

# 46. طبقة الفحص المؤسسي الصارم — Institutional Assurance Layer

> **حاكمية هذه الطبقة:** هذه الطبقة لا تلغي أي Gate سابق؛ بل تضيف فوقه مستوى Assurance مناسبًا للجنة تدقيق/استحواذ/مخاطر/أمن/هندسة مؤسسية. عند التعارض، يُطبق الشرط الأكثر تحفظًا ما لم يوجد قرار Risk Acceptance موثق ومصرّح به.

## 46.1 الفرق بين "جاهز للإنتاج" و"قابل للدفاع أمام لجنة فحص"

القدرة قد تعمل في الإنتاج لكنها لا تزال غير قابلة للدفاع المؤسسي إذا:
- لا يمكن إعادة إنتاج دليل صحتها.
- لا يوجد مالك واضح للمتطلب أو الخطر.
- لا توجد سلسلة تتبع من المتطلب إلى الكود إلى الاختبار إلى الإصدار.
- الدليل أنشأه نفس المنفذ بلا أي تحقق مستقل للقدرات عالية الخطورة.
- لا يوجد سجل استثناءات أو قبول مخاطر.
- لا توجد خطة استمرارية أو استعادة.
- لا توجد أدلة على فشل الاعتماديات وسلوك النظام عند الفشل.
- لا توجد حوكمة للموردين والمكونات الخارجية.
- لا يمكن إثبات مصدر artifact الذي نُشر.
- لا يوجد سجل تغييرات موثوق.
- لا توجد ضوابط تمنع إعادة ظهور العيب أو التكرار.

**[POLICY] الحالة الأعلى الجديدة: `ASSURANCE_READY`**
لا تُمنح إلا بعد PASS_LIVE + استيفاء طبقة الأدلة والحوكمة والاستقلال والمخاطر أدناه.

---

# 47. نموذج Stage-Gate المؤسسي

كل قدرة تمر بالبوابات التالية:

| Gate | الاسم | شرط الخروج |
|---|---|---|
| **G0** | Intake & Materiality | الهدف، المالك، الأهمية، المستخدم، أثر الفشل |
| **G1** | Requirements Assurance | متطلبات قابلة للتحقق + RTM + acceptance oracle |
| **G2** | Architecture & Risk | تصميم + impact + threat/data/model/vendor risk |
| **G3** | Build Integrity | تنفيذ + source/build provenance + code review |
| **G4** | Verification & Validation | tests + expected/actual + regression + user outcome |
| **G5** | Operational Readiness | SLO + observability + runbook + capacity + recovery |
| **G6** | Live Validation | deployment + smoke + live-path + real dependencies |
| **G7** | Independent Assurance | evidence review + exceptions + residual risk + sign-off |

### قاعدة
لا يجوز القفز من G3 إلى G6 بسبب نجاح CI، ولا من G6 إلى G7 دون Evidence Pack قابل للتدقيق.

---

# 48. Materiality / Criticality Classification

قبل مستوى الاختبارات يجب تحديد **أهمية القدرة**:

| المستوى | وصف | مثال | مستوى Assurance |
|---|---|---|---|
| **M0** | داخلي/غير مؤثر | أداة مساعدة | أساسي |
| **M1** | عرض معلومات منخفض الخطر | UI غير حساس | متوسط |
| **M2** | قرار/تحليل للمستخدم | إشارات وتحليلات | مرتفع |
| **M3** | مالي/أمني/صلاحيات/مؤسسي | portfolio, entitlements, billing | شديد |
| **M4** | قد يسبب خسارة/اختراق/قرار مؤسسي مادي | state-changing أو model critical | أقصى |

كلما ارتفعت Materiality ترتفع:
- قوة الاختبار.
- استقلال التحقق.
- الحاجة إلى rollback.
- متطلبات logging/audit.
- مدة الاحتفاظ بالدليل.
- rigor في model/data validation.
- شدة security review.
- شدة load/recovery tests.

---

# 49. Enterprise Risk Management Gate

**[STD/GUIDE] ISO 31000:2018** يظل إصدار ISO المنشور الحالي في سبتمبر 2026 رغم وجود مراجعة قيد التطوير.  
**[GUIDE] NIST CSF 2.0** يدعم حوكمة وإدارة مخاطر الأمن على مستوى المؤسسة.

لكل قدرة M2+:
- `risk_id`
- threat/opportunity
- cause
- event
- consequence
- likelihood
- impact
- inherent risk
- controls
- control owner
- residual risk
- treatment
- target date
- acceptance authority

### ممنوع
- قبول خطر بصيغة "مقبول" بلا مالك.
- إغلاق `High/Critical residual risk` بلا سلطة قبول محددة.
- إخفاء blocker داخل ملاحظة اختبار.

---

# 50. Exception & Risk Acceptance Governance

أي انحراف عن معيار حاكم يحتاج سجل استثناء:

```text
Exception_ID:
Requirement:
Reason:
Scope:
Risk:
Compensating Controls:
Owner:
Approver:
Start Date:
Expiry Date:
Review Date:
Exit Plan:
Evidence:
```

### قواعد صارمة
- كل استثناء له **Expiry**.
- لا استثناء دائم بلا مراجعة.
- لا يعتمد المنفذ استثناءه بنفسه في M3/M4.
- انتهاء الاستثناء يعيد الحالة تلقائيًا إلى `NOT_ASSURED` حتى التجديد الرسمي أو العلاج، ولا يؤدي بذاته إلى حذف القدرة أو `Eliminate`.
- الـWaiver يقبل مخاطرة مؤقتة فقط؛ لا يرقّي evidence class، ولا يحول defect إلى PASS، ولا يجعل اختبارًا محليًا دليل إنتاج حي.
- مدة الاستثناء وموعد مراجعته **Risk-Based** ومتناسبان مع materiality والتأثير، وليس هناك حد زمني عالمي ثابت مفروض على جميع الحالات.

---

# 51. Segregation of Duties / Four-Eyes

للقدرات M3/M4، افصل قدر الإمكان بين:
- implementer
- code reviewer
- production deploy approver
- security/risk reviewer
- model validator عند النماذج المادية

**[POLICY]** في الفريق الصغير لا يشترط خمسة أشخاص، لكن يجب تحقيق **effective challenge**:
- مراجعة مستقلة عن لحظة التنفيذ.
- أدلة قابلة لإعادة التشغيل.
- عدم السماح للمنفذ بتغيير acceptance criteria بعد رؤية الفشل دون توثيق.

---

# 52. Evidence Assurance — جودة الدليل

## 52.1 درجات الدليل

| الدرجة | الدليل | القوة |
|---|---|---|
| **E0** | ادعاء نصي | غير مقبول |
| **E1** | قراءة كود/لقطة يدوية | ضعيف |
| **E2** | اختبار آلي قابل للإعادة | جيد |
| **E3** | اختبار + بيئة + commit + artifact + output محفوظ | قوي |
| **E4** | تحقق مستقل/حي + سلسلة مصدر + timestamp + immutable reference | مؤسسي |

### الحد الأدنى
- M0/M1: E2
- M2: E3
- M3/M4: E3 للـengineering وE4 للـcritical/live claims حيث يمكن

## 52.2 Chain of Custody
للأدلة الحساسة:
- من أنشأها؟
- متى؟
- على أي commit/build؟
- في أي environment؟
- ما input؟
- ما output؟
- هل تم تعديل الملف لاحقًا؟
- أين المرجع الثابت؟

---

# 53. Control Mapping / Control Matrix

أنشئ مصفوفة Controls لا مجرد قائمة معايير:

`Control_ID → Risk → Requirement → Implementation → Test → Evidence → Owner → Frequency → Status`

تصنيف controls:
- Preventive
- Detective
- Corrective
- Recovery
- Compensating

### اللجنة يجب أن ترى الفرق بين:
- **Control Design Effectiveness**
- **Control Operating Effectiveness**

وجود control في الكود لا يثبت أنه يعمل باستمرار.

---

# 54. Change Management & Configuration Governance

أي تغيير M2+ يسجل:
- change_id
- reason
- affected capabilities
- risk
- approver
- rollback
- deployment window
- migrations
- test evidence
- post-deploy verification

## 54.1 Configuration
يجب:
- فصل config عن code حيث يلزم.
- منع drift غير المرصود بين البيئات.
- version critical configuration.
- audit تغييرات production config.
- validate required env vars/secrets قبل التشغيل.
- fail explicitly عند غياب critical config.

---

# 55. Asset / Dependency Inventory

اللجنة المؤسسية تحتاج معرفة **ماذا تملك وماذا تعتمد عليه**.

لكل capability M2+:
- internal modules
- services
- DBs
- queues
- external APIs
- cloud services
- models
- datasets
- libraries/packages
- secrets/keys
- domains/endpoints
- scheduled jobs

يجب وجود owner + criticality + version/lifecycle حيث ينطبق.

---

# 56. Software Supply Chain Assurance

**[GUIDE/PRACTICE] SLSA v1.2** هو الإصدار المعتمد الحالي في 2026 ويغطي Source وBuild tracks.

للإصدارات الحرجة:
- source control protected.
- review policy.
- reproducible/controlled build process حيث feasible.
- provenance للـartifact.
- artifact identity/hash.
- dependency inventory/SBOM حيث مناسب.
- signed/verified provenance حيث البنية تدعم.
- CI credentials least privilege.
- no untrusted arbitrary code in privileged release path.
- dependency update governance.

### هدف مؤسسي مقترح
- **M3/M4:** استهداف خصائص SLSA Build L2 على الأقل حيث البيئة تسمح، مع خطة رفع المستوى عند الحاجة.
- لا تدّعِ `SLSA compliant` دون قياس رسمي للمتطلبات المطلوبة.

---

# 57. Supplier / Third-Party Risk

استنادًا إلى **ISO/IEC 27036-2:2022** و**27036-3:2023**:

لكل مورد/مزود/API خارجي:
- service owner.
- data shared.
- access privileges.
- SLA/SLO.
- outage behavior.
- security expectations.
- breach/incident notification path.
- exit/substitution plan.
- concentration risk.
- portability.
- contract/licensing constraints.
- dependency version/status.

### اختبار
لا يكفي أن المورد يعمل الآن؛ يجب اختبار أثر:
- outage.
- throttling.
- schema change.
- degraded response.
- termination/unavailability.

**[BLACKDARK POLICY]** لا يُنشأ اشتراك أو شراء مدفوع تلقائيًا لأي مزود/مصدر بيانات. إذا كانت قدرة تعتمد على مزود مدفوع، يُغلق كل ما يمكن هندسيًا محليًا، ويُسجل الاعتماد الخارجي والحالة المناسبة بوضوح، ولا يُدعى `PASS_LIVE` قبل توفر الاعتماد الفعلي والدليل المطلوب.

---

# 58. Cloud Security Assurance

عند استخدام Cloud:
- **ISO/IEC 27017:2026** كمرجع cloud-control guidance.
- shared responsibility matrix.
- cloud IAM.
- environment isolation.
- network exposure.
- encryption/key responsibility.
- logging responsibility.
- backup responsibility.
- provider outage risk.
- region/data residency حسب الحاجة.

عند PII في public cloud:
- **ISO/IEC 27018:2025** حيث ينطبق دور المعالجة السحابية.

---

# 59. Vulnerability Management

لكل مكوّن production:
- inventory.
- scan cadence.
- severity.
- exploitability/context.
- owner.
- remediation SLA.
- exception process.
- retest.

### سياسة افتراضية
- Critical exploitable: release blocker / emergency treatment.
- High: blocker افتراضيًا للـM3/M4 أو risk acceptance رسمي.
- Medium/Low: tracked وفق السياق.

يجب إثبات **الإغلاق وإعادة الاختبار**، لا مجرد إنشاء ticket.

---

# 60. Incident Response & Lessons Learned

**[GUIDE] NIST SP 800-61 Rev.3 (2025)** و**[STD] ISO/IEC 27035-1:2023**.

لكل مسار حرج:
- incident severity model.
- detection source.
- escalation.
- containment.
- eradication.
- recovery.
- communication.
- evidence preservation.
- post-incident review.

### Postmortem
يجب أن ينتج:
- root cause.
- contributing factors.
- customer impact.
- detection gap.
- corrective actions.
- preventive controls.
- owner/date.
- verification that action actually prevented recurrence.

---

# 61. Business Continuity / Disaster Recovery

**[STD] ISO 22301:2019 + Amd 1:2024** هو الإصدار المنشور الحالي في سبتمبر 2026، مع إصدار جديد ما يزال قيد التطوير.

لكل خدمة/قدرة حرجة:
- Business Impact Analysis (BIA).
- MTPD/maximum tolerable disruption حيث يستخدم.
- RTO.
- RPO.
- dependency recovery order.
- backup policy.
- restore procedure.
- alternate service/degraded operation.
- communications.

## 61.1 Restore Evidence
وجود backup ليس دليلًا.

يجب اختبار:
- restore.
- integrity after restore.
- time achieved vs RTO.
- data loss achieved vs RPO.
- credentials/config needed for recovery.

### M3/M4
لا ASSURANCE_READY بلا **restore test evidence** مناسب للمكونات التي تحتفظ بحالة/بيانات حرجة.

---

# 62. Service Management & Operational Discipline

**[STD] ISO/IEC 20000-1:2018** ما يزال جاريًا ومؤكدًا.

للمسارات الحية:
- service owner.
- service catalog relation.
- incident.
- problem.
- change.
- release.
- service level.
- availability.
- capacity.
- continual improvement.

الهدف: القدرة ليست feature معزولة؛ هي جزء من **خدمة قابلة للإدارة**.

---

# 63. Capacity Engineering

قبل لجنة الفحص لا يكفي Load Test واحد.

يجب تحديد:
- normal demand.
- peak demand.
- stress limit.
- break point.
- safe operating envelope.
- scaling behavior.
- queue/backpressure.
- DB connection saturation.
- third-party limits.
- recovery after overload.

## 63.1 Headroom
حدد capacity headroom للـcritical paths بدل تشغيلها دائمًا قرب saturation.

## 63.2 Soak Test
للخدمات الحرجة:
- sustained load لفترة مناسبة.
- memory leak.
- connection leak.
- queue growth.
- latency drift.
- error accumulation.

---

# 64. Resilience / Fault Injection

للقدرات M3/M4 حيث آمن:
- dependency timeout injection.
- partial failure.
- network delay.
- DB connection exhaustion simulation.
- cache unavailable.
- stale feed.
- queue delay.
- process restart.

الهدف ليس "إحداث فوضى" بل إثبات:
- containment.
- graceful degradation.
- recovery.
- no data corruption.
- correct alerts.

---

# 65. Financial / Analytical Integrity Gate

للمنتج المالي أو التحليلي:

## 65.1 Calculation Governance
- formula specification.
- units.
- precision.
- rounding.
- sign conventions.
- missing/unknown semantics.
- timestamp convention.
- source lineage.
- reference/golden cases.

## 65.2 Reconciliation
حيث يوجد أكثر من مرحلة حساب:
- input total.
- transformed total.
- output total.
- explain differences.
- tolerance.
- no silent drift.

## 65.3 Materiality Thresholds
الـtolerance لا يُختار عشوائيًا:
- business materiality.
- numeric precision.
- market data precision.
- error consequences.

## 65.4 No False Certainty
إذا البيانات أو النموذج لا يدعم دقة معينة، لا تُعرض أرقام زائفة الدقة للمستخدم.

---

# 66. Data Governance — مستوى لجنة الفحص

إضافة إلى Data Quality Gate السابق:

- data owner.
- data steward عند الحاجة.
- source contract.
- lineage.
- retention.
- classification.
- residency.
- access.
- deletion.
- reconciliation.
- quality KPIs.
- issue management.

## 66.1 Data Lineage
لأي نتيجة مادية:
`User Output → Transformation → Dataset → Source → Timestamp/Version`

## 66.2 Data Quality SLO
للمصادر الحرجة:
- freshness SLO.
- completeness SLO.
- error/invalid rate.
- missing rate.
- reconciliation breaks.

---

# 67. Audit Logging / Non-Repudiation

للعمليات الحساسة:
- who.
- what.
- when.
- target.
- before/after where appropriate.
- source/session.
- outcome.
- correlation ID.

يجب حماية audit logs من:
- تعديل غير مصرح.
- حذف غير مرصود.
- تسريب secrets/PII.

لا تستخدم application log عام كبديل دائم لـaudit trail في العمليات M3/M4.

---

# 68. Multi-Tenancy / Institutional Isolation

إذا النظام يخدم أكثر من مستخدم/مؤسسة:
- tenant context explicit.
- server-side isolation.
- query scoping.
- cache isolation.
- file/object isolation.
- background job isolation.
- telemetry separation حيث يلزم.
- admin cross-tenant access controlled/audited.
- tests لمحاولات cross-tenant access.

**Cross-tenant leakage = blocker.**

---

# 69. Model Risk Management — مستوى مالي مؤسسي

بالإضافة إلى ISO/IEC 42001 وISO/IEC 23894:2023 وNIST AI RMF:

**[GUIDE — مالي عالي الصرامة] Federal Reserve/OCC/FDIC Revised Guidance on Model Risk Management, 2026**  
يستخدم كـbenchmark قوي للنماذج المادية، دون الادعاء بأنه قانون ملزم للمشروع إن لم يكن ضمن نطاقه التنظيمي.

## 69.1 Model Inventory
لكل model:
- ID.
- owner.
- purpose.
- materiality.
- version.
- dependencies.
- data.
- limitations.
- validation status.
- monitoring status.
- retirement state.

## 69.2 Development Evidence
- conceptual soundness.
- assumptions.
- variable/feature rationale.
- alternatives considered.
- data representativeness.
- implementation verification.

## 69.3 Independent Validation
للـM3/M4 model:
- validator independent/effective challenge.
- conceptual review.
- implementation verification.
- benchmarking/challenger where useful.
- sensitivity/stress.
- outcome analysis/backtesting حيث ينطبق.
- limitations.

## 69.4 Ongoing Monitoring
- performance.
- overrides.
- drift.
- usage outside intended purpose.
- incidents.
- changes.
- revalidation triggers.

## 69.5 Vendor Models
لا تعفيك "black box vendor":
- inventory.
- intended use.
- vendor documentation.
- local performance.
- limitations.
- fallback.
- monitoring.

---

# 70. Processing Integrity / SOC 2 Readiness Cross-Check

**[ASSURANCE CRITERIA] AICPA Trust Services Criteria** تشمل:
- Security
- Availability
- Processing Integrity
- Confidentiality
- Privacy

لا يعني هذا أن المشروع حاصل على SOC 2.

لكن لجنة فحص قوية ستستفيد من سؤال:
- هل المعالجة Complete/Valid/Accurate/Timely/Authorized حسب طبيعة النظام؟
- هل controls موصوفة؟
- هل تعمل على مدى زمني، لا في لقطة واحدة فقط؟

### `SOC2_READY_EVIDENCE`
اسم داخلي مسموح فقط للدلالة على وجود evidence pack، وليس تقرير SOC 2.

---

# 71. Privacy by Design / Data Minimization

لكل بيانات شخصية:
- purpose.
- legal/contractual basis حسب النظام المنطبق.
- minimum fields.
- retention.
- access.
- disclosure.
- deletion.
- logging.
- testing data handling.
- vendor transfer.

**لا تجمع حقلًا "قد نحتاجه مستقبلًا" بلا غرض موثق.**

---

# 72. Backup / Key / Secret Recovery

اللجنة ستسأل: ماذا يحدث إذا فقدتم:
- database.
- encryption key.
- deployment credential.
- API credential.
- DNS/control-plane access.

يجب:
- inventory.
- owner.
- rotation.
- recovery path.
- emergency access governance.
- test where safe.
- no single undocumented human dependency.

---

# 73. Release Authenticity

لكل release مهم:
- source commit.
- CI run.
- artifact digest.
- build environment.
- deploy environment.
- migration version.
- config version/reference.
- approver.
- deployment timestamp.

الهدف:
**أن تستطيع اللجنة إثبات أن ما اختُبر هو نفسه ما نُشر.**

---

# 74. Environment Parity & Test Representativeness

كل evidence يسجل environment.

يجب تحديد الفروق بين:
- local
- CI
- staging
- production

أي فرق قد يغير النتيجة يحتاج:
- risk.
- compensating test.
- live verification.

لا تستخدم staging PASS لإثبات production behavior في dependency أو config مختلف دون live evidence.

---

# 75. Negative Assurance / Abuse Cases

لا تختبر happy path فقط.

لكل M2+:
- invalid input.
- malicious/oversized input.
- unauthorized user.
- wrong tenant.
- stale data.
- missing data.
- dependency failure.
- duplicate request.
- replay where relevant.
- race condition.
- extreme market/input values.
- unexpected model output.

---

# 76. Invariant & Property-Based Assurance

للمنطق المالي/الحسابي المعقد:
- عرّف invariants.
- اختبر نطاقًا واسعًا من inputs.
- لا تعتمد فقط على 3 golden examples.

أمثلة:
- قيمة لا تصبح NaN/Infinity.
- probability stays in valid range.
- totals reconcile.
- unauthorized state never transitions.
- monotonic property where domain requires it.

---

# 77. Security Adversarial Validation

للـM3/M4:
- SAST/secret scan/dependency scan.
- authz negative tests.
- API abuse tests.
- targeted DAST حيث مناسب.
- penetration test مستقل عند مستوى المخاطر/العميل/العقد الذي يتطلبه.

**تنبيه:** scan أخضر ≠ pentest ≠ certification.

---

# 78. Performance Acceptance — النسخة الأصعب

الأرقام السابقة تبقى targets أولية، لكن لجنة الفحص تحتاج:

```text
Workload:
Dataset size:
Concurrency:
Warm/Cold:
Duration:
p50:
p95:
p99:
Error rate:
Timeout rate:
Throughput:
CPU:
Memory:
DB pool:
External dependency latency:
Result:
```

### Gate
PASS لا يعتمد على latency وحدها إذا:
- errors مرتفعة.
- timeout مرتفع.
- queue تتراكم.
- data stale.
- output correctness تتدهور تحت الضغط.

---

# 79. SLO / Error Budget Governance

لكل user journey حرج:
- SLI.
- target.
- measurement.
- window.
- error budget.
- alert.
- owner.

إذا تم استهلاك error budget بشكل غير مقبول:
- أولوية reliability على feature velocity حسب سياسة المشروع.

---

# 80. Recovery Objectives Matrix

| المكوّن | Criticality | RTO | RPO | Backup | Restore Tested | Last Test | Owner |
|---|---|---:|---:|---|---|---|---|

لا تضع RTO/RPO كأرقام تجميلية؛ يجب أن تكون:
- مرتبطة بأثر الأعمال.
- قابلة للاختبار.
- متوافقة مع capabilities التابعة.

---

# 81. Documentation Assurance

لكل M2+ يجب توفر ما يلزم من:
- architecture description.
- data flow.
- API contract.
- runbook.
- failure modes.
- known limitations.
- security assumptions.
- recovery.
- model card/validation notes عند AI.
- change history.

الوثائق يجب أن تتطابق مع النظام الحالي، لا تصميم قديم.

---

# 82. Ownership / RACI

لا يوجد control أو capability "ملك النظام" بلا شخص/دور مسؤول.

للعناصر الحرجة:
- Accountable
- Responsible
- Consulted
- Informed

خصوصًا:
- data.
- model.
- service.
- security risk.
- incident.
- release.
- vendor.

---

# 83. Technical Debt Governance

Technical Debt لا يُستخدم كمقبرة للنواقص.

لكل debt:
- impact.
- risk.
- reason.
- owner.
- due date.
- dependency.
- acceptance authority.

أي debt يمنع security/correctness/user outcome لا يجوز استخدامه لتبرير PASS_LIVE.

---

# 84. Deprecation / Retirement

القدرة القديمة تحتاج:
- consumer inventory.
- replacement.
- migration.
- notices.
- telemetry of remaining use.
- sunset date.
- data/archive handling.
- removal evidence.

لا تحذف feature لأن "لا أحد يبدو أنه يستخدمها".

---

# 85. Institutional Due-Diligence Evidence Room

قبل لجنة الفحص، حضّر Evidence Room منظمًا:

```text
00_Governance/
01_Architecture/
02_Capability_Register/
03_RTM/
04_Test_Evidence/
05_Security/
06_Risk_Register/
07_Data_Governance/
08_AI_Model_Risk/
09_Performance_Capacity/
10_SRE_SLO/
11_Incidents_Postmortems/
12_BCP_DR/
13_Suppliers/
14_Release_Provenance/
15_Audit_Logs/
16_Exceptions/
17_Independent_Reviews/
18_Live_Validation/
```

### كل artifact
- owner.
- date.
- version.
- scope.
- evidence source.
- status.

---

# 86. Committee Challenge Questions

قبل إعلان الجاهزية، يجب القدرة على إجابة هذه الأسئلة بالدليل:

1. أين تعريف الهدف لكل قدرة؟
2. كيف تثبت أنها تحقق الهدف للمستخدم لا للكود فقط؟
3. أين expected oracle؟
4. أين data lineage؟
5. كيف تمنع stale/incorrect data؟
6. أين duplicate analysis والـcanonical؟
7. كيف تثبت عدم وجود conflicting source of truth؟
8. كيف اختبرت failure modes؟
9. ماذا يحدث إذا اختفى المورد الخارجي؟
10. أين p95/p99 تحت الحمل؟
11. أين capacity limit وheadroom؟
12. أين SLO وerror budget؟
13. كيف تعرف أن القدرة تعطلت؟
14. أين runbook؟
15. أين RTO/RPO؟
16. متى اختبرت restore فعليًا؟
17. كيف تثبت أن artifact المنشور هو المختبر؟
18. أين dependency/SBOM/provenance؟
19. من يمكنه الوصول ولماذا؟
20. هل tenant A يستطيع رؤية B؟
21. أين threat model؟
22. أين vulnerability exceptions؟
23. من قبل residual risk؟
24. متى ينتهي الاستثناء؟
25. أين audit trail؟
26. من راجع المنفذ؟
27. كيف تختبر regression؟
28. كيف تعالج model drift؟
29. هل model validated independently؟
30. ما حدود النموذج؟
31. أين fallback/abstain؟
32. ما خطة rollback؟
33. ماذا يحدث عند migration failure؟
34. ما الدليل الحي؟
35. ما الذي لم يكتمل ولماذا؟

إذا تعذر جواب أي سؤال جوهري:
**لا `ASSURANCE_READY`.**

---

# 87. Red-Flag Conditions — مانعات فورية للجنة

أي من الآتي يمنع الجاهزية المؤسسية حتى العلاج أو Risk Acceptance مخول:

- PASS بلا Evidence.
- Critical/High exploitable security issue غير معالج.
- unknown production artifact.
- no rollback for material irreversible change.
- cross-tenant leakage.
- silent data corruption.
- conflicting canonical calculations.
- live claim without live-path evidence.
- untested restore for critical state.
- uncontrolled production secrets.
- model M3/M4 بلا owner/version/validation.
- undocumented critical external dependency.
- expired exception.
- orphaned control بلا owner.
- known regression.
- migration can corrupt data بلا mitigation.
- inaccurate/stale financial data معروضة كـlive.
- material incident corrective action غير مغلق مع استمرار نفس الخطر.

---

# 88. Assurance Status Model

الحالات الأعلى:

- `NOT_STARTED`
- `IN_BUILD`
- `PARTIAL`
- `PASS_ENGINEERING`
- `PASS_LIVE`
- `ASSURANCE_REVIEW`
- `ASSURANCE_READY`
- `BLOCKED_EXTERNAL`
- `RISK_ACCEPTED_TEMPORARY`
- `REOPENED`
- `RETIRED`

### `ASSURANCE_READY`
يعني:
- PASS_LIVE.
- G0–G7 complete.
- evidence quality مناسب للمادية.
- لا blocker.
- residual risks مقبولة رسميًا.
- controls design + operating evidence متوفر حيث يلزم.
- recovery/security/data/model/vendor checks المناسبة مكتملة.

---

# 89. Institutional Closure Record — النسخة النهائية

```text
Capability:
Materiality:
Owner:
Business/User Objective:
Failure Impact:

State Classification:
Canonical Decision:
Duplicate Decision:

G0 Materiality: PASS/FAIL + Evidence
G1 Requirements: PASS/FAIL + Evidence
G2 Architecture & Risk: PASS/FAIL + Evidence
G3 Build Integrity: PASS/FAIL + Evidence
G4 V&V: PASS/FAIL + Evidence
G5 Operational Readiness: PASS/FAIL + Evidence
G6 Live Validation: PASS/FAIL + Evidence
G7 Independent Assurance: PASS/FAIL + Evidence

RTM:
Data Lineage:
Expected Oracle:
Security:
Privacy:
Supplier Risk:
Model Risk:
Performance:
Capacity:
SLO:
Observability:
Incident Readiness:
BCP/DR:
RTO/RPO:
Restore Test:
Rollback:
Release Provenance:
Audit Trail:
Exceptions:
Residual Risk:
Risk Acceptance:
Independent Reviewer:

Commit:
Build Artifact/Digest:
CI Run:
Deploy ID:
Environment:
Evidence Pack:

FINAL:
ASSURANCE_READY / ...
```

---

# 90. Institutional Scoring — لا يستبدل Gates

يمكن استخدام score للمقارنة فقط، وليس لتجاوز blocker:

| المجال | الوزن الإرشادي |
|---|---:|
| Functional/User Outcome | 15% |
| Data Integrity | 10% |
| Security/Privacy | 15% |
| Reliability/BCP | 12% |
| Performance/Capacity | 8% |
| Architecture/Maintainability | 8% |
| Testing/Regression | 10% |
| Observability/Operations | 7% |
| Supply Chain/Vendors | 5% |
| Governance/Evidence/Risk | 10% |

**قاعدة:** 99/100 لا يمر إذا يوجد Red Flag.

---

# 91. متطلبات اللجنة على مستوى المنتج بالكامل

بعد إغلاق القدرات منفردة، يلزم فحص **النظام ككل**:

- architectural consistency.
- integration interactions.
- shared bottlenecks.
- aggregate load.
- shared data consistency.
- shared auth/security boundaries.
- cross-feature workflows.
- global configuration.
- common failure modes.
- systemic vendor concentration.
- systemic model correlation.
- global disaster recovery.
- full product regression.
- end-to-end critical journeys.

**قاعدة:** مجموع قدرات PASS لا يساوي تلقائيًا نظامًا PASS.

---

# 92. Systemic Duplicate / Coupling Review

بعد علاج duplicate داخل القدرات، افحص على مستوى النظام:
- same calculation libraries.
- same data fetches.
- parallel caches.
- repeated API clients.
- duplicated auth logic.
- duplicated entitlement logic.
- duplicated model features.
- duplicated state machines.
- cyclic dependencies.
- hidden shared mutable state.

الهدف:
- Canonical truth.
- controlled reuse.
- no accidental coupling.
- independent deploy/test boundaries حيث يلزم.

---

# 93. Acquisition / Institutional Technical Due Diligence Pack

لو اللجنة لجنة استحواذ أو مؤسسة كبيرة، أضف:

- architecture map.
- dependency map.
- capability coverage.
- code ownership.
- licensing/IP provenance.
- third-party licenses.
- open-source inventory.
- security posture.
- incidents.
- uptime/SLO evidence.
- capacity.
- cost drivers.
- vendor lock-in.
- DR.
- data rights.
- model/data provenance.
- tech debt.
- roadmap blockers.
- key-person dependencies.
- environment/deployment reproducibility.

هذه البنود لا تعني أن كلها شرط لكل capability، لكنها شرط **لفحص المنتج المؤسسي النهائي**.

---

# 94. IP / License Provenance

لكل dependency/code/data/model مهم:
- source.
- license.
- usage rights.
- redistribution restrictions.
- attribution requirements.
- commercial-use restrictions.
- model/data terms.

**Unknown license/provenance** في أصل مادي = due-diligence finding حتى يُحسم.

---

# 95. Key-Person / Bus-Factor Risk

للأجزاء الحرجة:
- هل التشغيل يعتمد على معرفة شخص واحد؟
- هل يوجد runbook؟
- هل الأسرار مع شخص واحد؟
- هل build/deploy يمكن إعادة إنتاجه؟
- هل recovery يتطلب ذاكرة فرد؟

وجود single undocumented operator = risk يجب تسجيله.

---

# 96. Cost / Resource Sustainability

القدرة قد تكون صحيحة لكنها غير مؤسسية إذا تكلفة تشغيلها غير منضبطة.

للقدرات الثقيلة:
- cost per request/job.
- model/API cost.
- data vendor cost.
- storage growth.
- egress.
- peak cost.
- budget alert.
- runaway protection.

لا تجعل performance optimization يخفي correctness؛ ولا تجعل correctness غير محدودة التكلفة بلا قياس.

---

# 97. Continual Assurance

`ASSURANCE_READY` ليست أبدية.

إعادة فتح mandatory عند:
- material architecture change.
- critical dependency change.
- model major version.
- data source/formula change.
- security incident.
- major outage.
- failed SLO period.
- material regulation/contract change.
- expired evidence.
- restore test failure.
- major vendor change.

---

# 98. Evidence Freshness

كل نوع evidence له عمر مناسب تحدده السياسة.

أمثلة:
- source/commit evidence: صالح للنسخة نفسها.
- load test: يعاد عند تغير architecture/load profile.
- security scan: يعاد دوريًا وعند material changes.
- pentest: حسب المخاطر/العقد/التغيير.
- restore test: دوري.
- model validation: دوري وعند material change.
- vendor assessment: دوري.
- access review: دوري.

لا تعتمد على evidence تاريخي لنسخة مختلفة.

---

# 99. معيار "لا يوجد قصور جوهري"

لا يمكن مهنيًا ضمان "صفر عيب للأبد".

لكن يسمح بالحكم:
**No Known Material Deficiency**

فقط إذا:
- جميع material gates اجتازت.
- لا red flags.
- residual risks موثقة.
- limitations معلنة.
- evidence current.
- monitoring قادر على اكتشاف الانحراف بعد الإطلاق.

هذا هو التعبير المؤسسي الأكثر قابلية للدفاع من ادعاء "100% perfect".

---

# 100. Master Institutional Rule Set — المستوى الأعلى لـCursor

```text
INSTITUTIONAL ASSURANCE MODE

Treat every capability as an auditable production control/object, not merely code.

A. Never start by coding. Establish materiality, owner, current state, canonical
implementation, requirements, acceptance oracle, dependencies and risks.

B. Never duplicate a capability, calculation, data truth, authorization rule,
entitlement rule, model feature or state transition without a documented reason.

C. Any suspected duplicate requires functional/semantic/source-of-truth analysis,
consumer impact analysis and a canonical decision before modification.

D. Every material capability must pass G0-G7:
Materiality → Requirements → Architecture/Risk → Build Integrity → V&V →
Operational Readiness → Live Validation → Independent Assurance.

E. No PASS without reproducible evidence. Record commit, build, environment,
inputs, outputs, test IDs and evidence locations.

F. For material changes, preserve separation/effective challenge between
implementation and assurance. The implementer may not self-approve material
exceptions without authorized risk acceptance.

G. Control design is not control operation. Prove that critical controls actually
operate in representative/live conditions.

H. Verify data lineage, data quality, freshness, timestamps, units, precision,
reconciliation and stale/partial behavior for all material analytical outputs.

I. Verify performance with p50/p95/p99, error rate, throughput, concurrency,
saturation and soak/load evidence. Average latency alone is invalid evidence.

J. Define SLIs/SLOs and operational ownership for critical user journeys.

K. Verify dependency failures, supplier risks, exit/fallback paths and vendor
concentration.

L. Verify security using threat modeling, authorization abuse tests, vulnerability
management, supply-chain controls and production-safe validation.

M. Record source/build provenance for critical releases so the deployed artifact
can be tied back to reviewed source and CI evidence.

N. Define and test rollback, RTO, RPO, backup restore and recovery for critical
stateful services. A backup that has never been restored is not recovery evidence.

O. For models/AI, maintain inventory/version/owner/limitations; independently
validate material models, stress/sensitivity test them, monitor performance/drift
and revalidate on material changes.

P. Maintain immutable/auditable records for material state changes and access.

Q. No staging/local result may be represented as production validation when
material environment differences exist.

R. Any exception requires risk, compensating controls, owner, approver, expiry,
review and exit plan.

S. Any known material deficiency, critical security issue, cross-tenant leakage,
silent corruption, conflicting canonical result, untested critical recovery, or
unknown production artifact blocks ASSURANCE_READY.

T. PASS_ENGINEERING != PASS_LIVE != ASSURANCE_READY.

U. After individual capability closure, perform system-level testing for shared
bottlenecks, cross-feature interactions, global security, capacity, recovery and
systemic risk.

V. Never claim ISO certification, SOC report/readiness equivalence, or a SLSA level/conformance state unless the exact scoped requirements and evidence have actually been assessed. SLSA is an industry specification/level model, not an ISO-style certification scheme. Use standards as control/assurance benchmarks unless a real
certification/report exists.
```

---

# 101. مراجع الإضافات الجديدة — مصادر رسمية/موثقة

1. **ISO 31000:2018 — Risk management — Guidelines**  
   https://www.iso.org/standard/65694.html  
   (الإصدار المنشور الحالي؛ توجد مراجعة جديدة قيد التطوير في 2026.)

2. **NIST Cybersecurity Framework 2.0**  
   https://www.nist.gov/cyberframework

3. **NIST SP 800-61 Rev.3 — Incident Response (2025)**  
   https://csrc.nist.gov/pubs/sp/800/61/r3/final

4. **ISO/IEC 27035-1:2023 — Information security incident management**  
   https://www.iso.org/standard/78973.html

5. **ISO 22301:2019 + Amd 1:2024 — Business Continuity**  
   https://www.iso.org/standard/75106.html

6. **ISO/IEC 20000-1:2018 — Service Management System Requirements**  
   https://www.iso.org/standard/70636.html

7. **ISO/IEC 27005:2022 — Information Security Risk Management**  
   https://www.iso.org/standard/80585.html

8. **ISO/IEC 27017:2026 — Cloud Security Controls**  
   https://www.iso.org/standard/27017

9. **ISO/IEC 27018:2025 — Protection of PII in Public Clouds**  
   https://www.iso.org/standard/27018

10. **ISO/IEC 27036-2:2022 — Supplier Relationships Requirements**  
    https://www.iso.org/standard/82060.html

11. **ISO/IEC 27036-3:2023 — Supply Chain Security Guidance**  
    https://www.iso.org/standard/82890.html

12. **ISO/IEC 23894:2023 — AI Risk Management**  
    https://www.iso.org/standard/77304.html

13. **SLSA v1.2 — Software Supply Chain Levels for Software Artifacts**  
    https://slsa.dev/spec/v1.2/

14. **AICPA Trust Services Criteria — Security, Availability, Processing Integrity, Confidentiality, Privacy**  
    https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022

15. **Federal Reserve SR 26-2 — Revised Guidance on Model Risk Management (2026)**  
    https://www.federalreserve.gov/supervisionreg/srletters/SR2602.htm  
    **Scope note:** supervisory guidance for covered banking organizations; useful here only as a financial model-risk benchmark. The 2026 guidance explicitly excludes generative and agentic AI from its formal model scope, so GenAI/agentic controls must instead rely primarily on ISO/IEC 42001, ISO/IEC 23894, NIST AI RMF and project-specific governance.

---

# 102. القرار النهائي بعد رفع مستوى الفحص

أصبحت بنية هذا المرجع ذات **ثلاث طبقات إغلاق منفصلة**:

1. **PASS_ENGINEERING**  
   القدرة صحيحة هندسيًا ومثبتة داخل نطاق الاختبار.

2. **PASS_LIVE**  
   القدرة مثبتة على المسار الحي/الإنتاجي المناسب.

3. **ASSURANCE_READY**  
   القدرة لا تعمل فقط، بل توجد أدلة وحوكمة ومخاطر واستمرارية وتتبّع وتحكم تسمح بالدفاع عنها أمام لجنة مؤسسية صعبة.

والهدف النهائي للمنتج بعد إغلاق القدرات هو:

> **NO KNOWN MATERIAL DEFICIENCY + REPRODUCIBLE EVIDENCE + CONTROLLED RESIDUAL RISK + LIVE USER OUTCOME + SYSTEM-LEVEL ASSURANCE**

وليس مجرد:
> "كل الاختبارات خضراء".

---

# 103. طبقة تقوية الأدلة — Evidence Hardening Layer

> **الغرض:** رفع جودة الدليل من "يوجد اختبار/Artifact" إلى "يمكن للجنة مستقلة إعادة تتبع الادعاء والتحقق من أن الاختبار غطّى المسار الصحيح والنطاق الصحيح دون فجوات صامتة".

هذه الطبقة **[POLICY]** ملزمة للمشروع فوق G0–G7، لكنها لا تستبدل أي Gate ولا تغيّر الفرق بين `PASS_ENGINEERING` و`PASS_LIVE` و`ASSURANCE_READY`.

## 103.1 قاعدة الدليل الكامل لا دليل الوجود

لا يكفي وجود:
- ملف JSON.
- test باسم مناسب.
- route.
- binding.
- تقرير يقول `COMPLETE`.
- exit code = 0.

يجب أن يثبت الدليل، حسب الانطباق:

`claim → requirement → canonical implementation → actual runtime/consumer path → control path → input/data → oracle → expected/actual → test execution → environment → commit/build → evidence location → status`

وعند وجود طبقات مشتركة مثل authorization/entitlement/gateway/cache/model/provider، يجب توضيح أي طبقة شملها الاختبار وأي طبقة لم يشملها.

## 103.2 Evidence Coverage Assertion

لكل batch أو نطاق كبير يجب إنشاء **machine-verifiable coverage assertion** يثبت على الأقل:
- عدد العناصر المتوقع.
- عدد العناصر المفحوص فعليًا.
- العناصر المفقودة.
- العناصر المكررة.
- الاستثناءات.
- سبب أي `NOT_APPLICABLE`.
- hash/version للنطاق أو manifest إن وجد.

لا يجوز استخدام عبارة "تم فحص الكل" دون evidence يمكن إعادة تشغيله أو إعادة حسابه.

---

# 104. الفصل الإلزامي بين State Classification وClosure/Execution Status

## 104.1 قاموس State Classification الحاكم

يبقى القاموس الحاكم من v2:
- `GREENFIELD`
- `EXISTING_VERIFIED`
- `PARTIAL_CANONICAL`
- `LEGACY/BROWNFIELD`
- `STUB_TEMPLATE`
- `DUPLICATE_ALIAS`
- `CONFLICTING_IMPLEMENTATIONS`
- `EXTERNAL_BLOCKED`

أي تسمية أخرى مثل `VERIFIED-DEEP`, `REUSED-LINK`, `PRODUCTION-ALIGNED` أو غيرها لا تحل محل **State Classification** إلا إذا تم اعتمادها رسميًا كتعديل لهذا المرجع.

## 104.2 فصل الأبعاد

يجب عدم خلط:
- **State Classification**: ما الحالة الأصلية/الحالية للتنفيذ؟
- **Canonical Decision**: reuse / merge / alias / deprecate / eliminate / resolve truth.
- **Engineering Status**: PASS_ENGINEERING / NOT_COMPLETE / ...
- **Live Status**: PASS_LIVE / awaiting deploy / blocked external.
- **Assurance Status**: G7 / ASSURANCE_READY.
- **External Dependency Status**: مزود مدفوع / مراجعة قانونية / تصديق بشري / بيئة إنتاج أو اعتماد خارجي آخر عند الانطباق.
- **Tracking/Reporting Label**: أي label داخلي للدفعة.

مثال صحيح:

```text
State Classification: DUPLICATE_ALIAS
Canonical Decision: REUSE_EXISTING_CANONICAL
Closure Label: CLOSED_REUSED_LINK
Engineering Status: PASS_ENGINEERING
Live Status: AWAITING_G6
Assurance Status: G7_PREPARED_LOCAL
```

هذا يمنع أن يصبح label محلي بديلاً عن الحقيقة الهندسية.

---

# 105. تقوية فحص التكرار — Exhaustive Duplicate Coverage Proof

## 105.1 لا يكفي candidate review غير الموثق

عندما يُطلب فحص نطاق جديد ضد نطاق سابق كامل، يجب إثبات أن التغطية كانت **شاملة وقابلة للتحقق**.

يمكن تحقيق ذلك بإحدى طريقتين:
1. pairwise exhaustive machine comparison، أو
2. canonical index/candidate-reduction method يثبت رياضيًا/منطقيًا أن filtering لا يمكن أن يخفي duplicate مادي، مع تسجيل coverage والمستبعدات وأسبابها.

**لا يُفرض إنشاء آلاف ADRs أو narrative records إذا أمكن إثبات التغطية آليًا.**

## 105.2 طبقات الفحص المطلوبة حسب الانطباق

افحص:
- داخل الـbatch نفسه.
- ضد كل capabilities السابقة المطلوبة في scope.
- ضد shared cores / registries / canonical calculations / routes / models / data truths.
- ضد Hero inputs عند القدرات التي قد تغذي الأبطال.
- ضد entitlement/authorization/business-rule implementations إذا كان هناك احتمال ازدواج مصدر الحقيقة.

## 105.3 سجل coverage

لكل فحص يجب تسجيل:
- `scope_left`
- `scope_right`
- `expected_comparisons_or_coverage_rule`
- `executed_coverage`
- `candidate_count`
- `confirmed_duplicates`
- `shared_core_only`
- `conflicts`
- `unresolved`
- `canonical_decision`
- `evidence`

`unresolved > 0` يمنع الإغلاق المحلي للنطاق المتأثر.

## 105.4 ADR ليس إلزاميًا لكل زوج

ADR يستخدم للقرار المعماري/المادي الذي يستحق rationale طويلًا.
القرارات البسيطة المتكررة يمكن توثيقها machine-readably داخل سجل canonical/duplicate، بشرط وجود rationale قابل للتتبع.

---

# 106. Canonical Full-Path Verification — اختبار المسار الحقيقي الكامل

## 106.1 مبدأ الطبقتين

يجب التفريق بين:

### أ. Component/Logic Verification
اختبار الدالة أو binding مباشرة لإثبات صحة business logic.

### ب. Canonical Consumption-Path Verification
اختبار المسار الذي يستهلكه المستخدم/العميل فعليًا، بما يشمل ما ينطبق من:

`UI/API → gateway → authentication → authorization → entitlement → tenant controls → validation → cache/provider → canonical capability → response transformation → audit/metrics`

وجود النوع (أ) لا يغني عن النوع (ب) عندما تكون الطبقات الوسيطة مادية للنتيجة أو الأمن أو الأداء.

## 106.2 Entitlement / Authorization Evidence

إذا كان runtime الإنتاجي يفرض entitlement أو authorization قبل التنفيذ:
- يجب وجود اختبار محلي/integration عبر هذا المسار.
- يجب اختبار allowed + denied + malformed/expired/unauthorized حسب الانطباق.
- يجب ألا تعتمد جميع أدلة الأداء/الوظيفة على direct binding فقط.

يمكن استخدام direct binding للاختبارات الوحدوية والأداء الجزئي، لكن يجب تسميته صراحة `COMPONENT_PATH` وليس `FULL_CANONICAL_PATH`.

## 106.3 Full-path performance

إذا كانت طبقات gateway/auth/entitlement قابلة للتشغيل محليًا، يجب قياس overhead المحلي للمسار الكامل بصورة منفصلة عن قياس handler/core.

لا يجوز استبدال ذلك بادعاء production latency.
Production latency تظل ضمن G6 عندما تكون البيئة الحية غير متاحة.

---

# 107. Six Heroes — مصفوفة الانطباق الفردية

## 107.1 قاعدة  Capability × Hero

لكل capability في النطاق، يجب تقييم علاقتها بكل Hero على حدة عندما Six Heroes جزء من المنتج.

أنشئ مصفوفة:

`Capability × Hero1..Hero6`

وكل خلية تكون واحدة من:
- `FEED`
- `CONTEXT`
- `GATE`
- `VETO`
- `RISK_CAP`
- `DATA_QUALITY_GATE`
- `NOT_APPLICABLE`

مع:
- reason.
- evidence.
- canonical function إن وجدت.

لا يكفي aggregate statement من نوع "49 غير مرتبطة و1 context" ما لم توجد تغطية قابلة للتحقق لكل Hero.

## 107.2 عند FEED/CONTEXT المادي

طبّق خريطة v2 الكاملة:

`Hero → capability → module.function → data lineage → transformations → decision role → explanation`

وافحص:
- double counting.
- common-source correlation.
- correlated-signal inflation.
- duplicate facade/delegation.
- missing/stale behavior.
- sensitivity.
- single-point dominance.

## 107.3 N/A ليس فشلاً

لا تُجبر قدرة غير ذات صلة على الارتباط بأي Hero.
`NOT_APPLICABLE` مقبول إذا كان reason/evidence موجودًا.

---

# 108. Clean-Pass Semantics — لا PASS مع تحذير غير مفسر

## 108.1 Exit Code 0 لا يكفي

أي من الآتي داخل test/CI/regression output يحتاج triage قبل اعتبار الدليل نظيفًا:
- `RuntimeError`
- unhandled exception in teardown/background task
- `Task was destroyed but it is pending`
- event-loop closed errors
- resource leak warnings
- coroutine never awaited
- unclosed session/socket/file/database connection
- retry storm / timeout warnings
- deprecation warning من كود نملكه ويمكن إصلاحه
- scanner warning له أثر مادي

## 108.2 تصنيف التحذير

كل warning/error غير قاتل يجب أن ينتهي إلى واحد من:
- `FIXED_LOCAL`
- `UPSTREAM_VERIFIED_NON_ACTIONABLE`
- `EXPECTED_AND_ASSERTED`
- `RISK_ACCEPTED` مع owner/expiry
- `BLOCKER`

لا يجوز تركه فقط لأن exit code = 0.

## 108.3 قاعدة known_local_deficiencies

إذا كان warning قابلًا للإصلاح محليًا وله احتمال أن يخفي lifecycle/resource/security/data defect:

`known_local_deficiencies != []`

حتى يُعالج أو يُثبت خلاف ذلك.

---

# 109. Project-Wide SSOT / Progress Consistency

## 109.1 لا تترك trackers الحاكمة stale

إذا كان المشروع يملك canonical project-wide register أو progress tracker أو decision register يُستخدم فعليًا كلجنة/CI/تخطيط، فيجب بعد إغلاق كل batch:
- تحديثه أو إثبات أنه مشتق آليًا من مصدر أحدث.
- منع التناقض بين batch artifacts وproject-wide counts.
- تسجيل source head/time.

## 109.2 لا تُنشئ counter لمجرد تقرير قديم

قبل إضافة field مثل `batchXX_independent` أو `progress_*`:
- أثبت أنه جزء من schema/canonical governance الحالي.
- لا تعيد إحياء legacy counter بلا consumer أو governance purpose.

## 109.3 Consistency assertion

يجب أن يوجد فحص آلي عند وجود SSOT مركزي:

`sum/canonical status from batches == project-wide canonical register`

أو تفسير machine-readable لأي اختلاف متعمد.

---

# 110. Evidence Pack Provenance — إثبات الـCI والـQuality Gates

لكل Gate يُعتبر جزءًا من freeze أو release evidence، سجل:
- gate name.
- provider/tool.
- result.
- run/build ID.
- tested commit SHA.
- timestamp.
- artifact/log location.
- quality gate status إن كانت الأداة توفره.

مثال:

```text
SonarCloud:
  run_id: ...
  tested_head: ...
  workflow_conclusion: PASS
  quality_gate_status: PASSED
```

نجاح الـworkflow لا يُستبدل بادعاء Quality Gate إذا الأداة تميّز بين الاثنين.

ولا يُشترط استخدام SonarCloud تحديدًا؛ الشرط هو أن أي gate اعتمده المشروع رسميًا يملك evidence واضحًا وقابلًا للتتبع.

---

# 111. Cross-Batch Regression Evidence Hardening

## 111.1 Suite مجمعة مسموحة

لا يُشترط run مستقل لكل batch إذا كانت suite المجمعة:
- تحدد بوضوح tests التابعة لكل batch.
- تربطها بنفس tested commit.
- تسجل exit/result لكل subgroup.
- لا تخفي warnings/errors.
- يمكن إعادة تشغيلها.

## 111.2 متى نحتاج runs منفصلة؟

فقط إذا:
- isolation نفسه جزء من الخطر.
- environment مختلف.
- ownership/control مختلف.
- suite المجمعة تمنع attribution.
- لجنة/سياسة مشروع تفرض ذلك صراحة.

## 111.3 بعد shared-code change

أي تغيير في shared core يجب أن يشغّل regression لكل consumer/batch متأثر، سواء في run واحد أو أكثر، مع evidence mapping للتغطية.

---

# 112. Performance Evidence Hardening

بالإضافة إلى معيار الأداء في v2:

## 112.1 منهج القياس

وثّق:
- warmup.
- sample count.
- percentile algorithm.
- workload fixture.
- machine/environment characteristics.
- concurrency level.
- stability/repeatability check.
- timestamps/commit.

## 112.2 Percentile adequacy

لا تستخدم عدد عينات صغيرًا لإصدار ادعاء قوي عن p99.
إذا كان p99 informational فقط، صرّح بذلك.
Gate الأداء يجب أن يعتمد على percentile الذي حدده SLO/target فعليًا.

## 112.3 Throughput / Concurrency / Saturation

لكل critical path، قيّم الانطباق على:
- throughput.
- concurrency.
- saturation/headroom.

`NOT_APPLICABLE` مقبول فقط مع rationale تقني.

## 112.4 Component vs Full-path latency

سجل القياسين منفصلين عند الانطباق:
- `COMPONENT_LATENCY`
- `FULL_CANONICAL_PATH_LATENCY`

ولا تسمي أيًا منهما `PRODUCTION_LATENCY` إلا بعد G6 على البيئة المناسبة.

---

# 113. Anti-Bureaucracy / No-False-Standards Rule

هذه القاعدة تمنع أن تتحول طبقة Evidence Hardening إلى بيروقراطية أو pseudo-compliance.

## 113.1 لا تفرض شكلًا إذا كان الهدف مثبتًا

لا تعتبر ما يلي requirement عالميًا بحد ذاته ما لم تعتمد سياسة مشروع صريحة:
- INVEST لكل capability.
- اسم artifact ثابت بعينه.
- triple-match باسم/صيغة محددة.
- ADR لكل duplicate pair.
- عدد ثابت من CI runs.
- أداة محددة مثل Sonar.

المطلوب هو **control objective + evidence quality + traceability + reproducibility**.

## 113.2 سياسة المشروع يجب أن تُسمى سياسة مشروع

أي إضافة داخلية أقوى من ISO/NIST/OWASP/SRE توسم `[POLICY]` ولا تُنسب إليهم نصيًا.

## 113.3 التشدد يجب أن يكون Risk-Based

زد evidence rigor عندما ترتفع:
- materiality.
- user harm.
- financial impact.
- security exposure.
- model risk.
- tenant/data sensitivity.
- irreversibility.

لا تضاعف artifacts في M0/M1 دون قيمة assurance حقيقية.

---

# 114. معيار Freeze المحلي بعد Evidence Hardening

لا يجوز إعلان `FINAL_LOCAL_FREEZE` إذا بقي أي من الآتي في النطاق المحلي القابل للتنفيذ:

- state classification غير متوافق مع القاموس الحاكم أو غير مفسر.
- duplicate coverage غير مثبت.
- unresolved canonical conflict.
- semantic correctness/appropriateness لقدرة مادية غير مثبتة بمرجع/محك مناسب.
- stub/template/generic behavior ما زال يُقدَّم كقدرة مستقلة مكتملة دون إثبات دلالي.
- canonical full path قابل للاختبار محليًا ولم يُختبر.
- entitlement/auth control مادي ولم يُختبر عبر المسار الحقيقي محليًا.
- Hero applicability غير مثبتة عندما Six Heroes جزء من النطاق.
- warning/runtime error غير مفسر أو قابل للإصلاح.
- project-wide SSOT حاكم ومتعارض/stale بلا تفسير.
- performance evidence غير كافٍ للمستوى المعلن.
- gate evidence لا يرتبط بالـtested source.
- shared-code regression coverage غير مثبت.

ويظل صحيحًا:

```text
FINAL_LOCAL_FREEZE
!= PASS_LIVE
!= G7_PASS
!= ASSURANCE_READY
```

Railway/production-only evidence لا يمنع الإغلاق المحلي إذا تم إغلاق كل الممكن محليًا وتوثيق الـblocker بدقة.

---

# 115. تحديث Master Institutional Rule Set لـCursor — v3 Additions

أضف إلى Section 100 الحاكم القواعد التالية:

```text
W. Separate state classification, canonical decision, engineering status, live status
and assurance status. Do not use a local label as a substitute for the governing
state taxonomy.

X. Prove duplicate-review coverage machine-verifiably. Candidate filtering is allowed
only when its coverage and false-negative risk are defensible.

Y. Test both component logic and the canonical consumption path. If authn/authz/
entitlement/gateway/tenant controls are material and locally executable, bypass-only
tests cannot be the sole evidence of closure.

Z. For Six Heroes, maintain capability-by-hero applicability evidence. Do not force
irrelevant capabilities into Heroes, but every NOT_APPLICABLE decision must be
traceable.

AA. A green exit code does not sanitize RuntimeError, resource leak, unhandled
background exception, lifecycle warning or other material warning. Triage each one.

AB. Keep canonical project-wide trackers/registers consistent with batch closure when
they are active sources of truth; do not revive obsolete counters without evidence.

AC. Bind every formal CI/quality/security gate to run ID, tested commit, result and,
where applicable, the tool's own quality-gate status.

AD. Performance evidence must disclose methodology and distinguish component,
full-canonical-path and production measurements.

AE. Evidence hardening must not become false compliance. Do not present INVEST,
specific filenames, ADR-per-pair, fixed run counts or a specific vendor tool as an
ISO/NIST requirement unless the governing source actually requires it.

AF. Any newly discovered locally-solvable deficiency or material evidence contradiction
reopens local verification even after a previous freeze.
```

---

# 116. قرار v3 النهائي

بعد هذا التحديث يصبح المرجع مكوّنًا من أربع طبقات مترابطة:

1. **Engineering Correctness** — صحة المتطلب والتنفيذ والبيانات والنتيجة.
2. **Operational / Live Validation** — إثبات المسار الحي والاعتماديات والـSLO في البيئة المناسبة.
3. **Institutional Assurance** — المخاطر، الاستقلال، evidence pack، الاستمرارية، التحكم والحوكمة.
4. **Evidence Hardening / Adversarial Audit** — إثبات أن claims السابقة نفسها كاملة التغطية، على المسار الصحيح، بلا bypass أو warning أو tracker contradiction أو aggregate evidence يخفي فجوة.

الهدف النهائي بعد v3:

> **NO KNOWN MATERIAL DEFICIENCY + REPRODUCIBLE EVIDENCE + MACHINE-VERIFIABLE COVERAGE + CANONICAL FULL-PATH PROOF + CONTROLLED RESIDUAL RISK + LIVE USER OUTCOME + SYSTEM-LEVEL ASSURANCE**

مع الحفاظ على القاعدة:

> **لا نضيف بيروقراطية لمجرد الشكل؛ نضيف فقط Evidence/Controls تزيد القدرة الفعلية على الدفاع أمام لجنة فحص مؤسسية صعبة.**



---

# 117. Research Refresh 2026 — حوكمة صلاحية المراجع

> **[POLICY]** هذه الطبقة نتيجة مراجعة بحثية للمراجع الرسمية والممارسات المنشورة والمطبقة على نطاق واسع حتى سبتمبر 2026. لا تُحوَّل الإرشادات إلى ادعاءات امتثال أو شهادة.

## 117.1 قاعدة Currency of Authority

قبل كل مراجعة مؤسسية كبرى أو إصدار معياري جديد:
- تحقق من أن المرجع ما يزال **Published / Current** وليس withdrawn أو superseded.
- فرّق بين `FINAL/PUBLISHED` و`DRAFT/IPD/CD`.
- لا تجعل Draft مرجعًا حاكمًا إذا يوجد إصدار نهائي قائم؛ يمكن استخدامه فقط كـ`FUTURE-WATCH`.
- سجل `reference_version`, `status_checked_at`, `official_url`.

### الحالة الحاكمة في سبتمبر 2026
- **[STD] ISO/IEC/IEEE 12207:2026** هو الإصدار الحالي المنشور، وقد حل محل 2017.
- **[GUIDE] NIST SP 800-218 SSDF v1.1** هو الإصدار النهائي الحاكم؛ **SSDF v1.2** ما يزال Draft وقت إعداد v4، فلا يُعامل كمرجع نهائي.
- **[GUIDE] OWASP ASVS 5.0.0** هو الإصدار المستقر الحالي.
- **[STD] ISO/IEC 27017:2026** هو الإصدار الحالي المنشور لأمن الخدمات السحابية.
- **[STD] ISO/IEC 27018:2025** هو الإصدار الحالي المنشور لحماية PII في السحابة العامة عند انطباق دور processor.
- **[GUIDE] NIST SP 800-61 Rev.3 (2025)** هو المرجع النهائي الأحدث للاستجابة للحوادث ضمن CSF 2.0.

## 117.2 No Frozen Standard Assumption

المرجع المؤسسي نفسه subject to change control. أي تحديث كبير في معيار حاكم يفتح:
`REFERENCE_CHANGE_REVIEW`
وليس إعادة بناء تلقائية لكل شيء.

يجب تحديد:
- delta.
- affected controls.
- affected evidence.
- retrofit necessity.
- grandfathering/risk rationale إن وجد.

---

# 118. Standards-to-Gates Crosswalk — مصفوفة المصدر إلى البوابة

> **الهدف:** منع pseudo-compliance ومنع لجنة أو Agent من اختراع متطلب ثم نسبه إلى معيار عالمي.

| المصدر | النوع | ما يضيفه | البوابات الأساسية | طبيعة الاستخدام |
|---|---|---|---|---|
| ISO/IEC/IEEE 12207:2026 | STD | Software lifecycle processes | G0–G7 | هيكل دورة الحياة؛ لا يفرض methodology أو filenames |
| ISO/IEC/IEEE 29148:2018 | STD | Requirements/traceability | G0–G1/G4 | متطلبات قابلة للتحقق والتتبع |
| ISO/IEC 25010:2023 | STD | 9 product-quality characteristics | G1/G2/G4/G5 | quality requirements/evaluation |
| ISO/IEC 25019:2023 | STD | Quality-in-use/context of use | G1/G4/G6 | user outcome في سياق الاستخدام |
| ISO/IEC 25012:2008 | STD | Data quality | G1/G4/G5/G6 | data requirements/evaluation |
| ISO/IEC/IEEE 42010:2022 | STD | Architecture description | G2 | viewpoints/concerns/relations؛ لا يفرض ADR بعينه |
| NIST CSF 2.0 | GUIDE/FRAMEWORK | Govern/Identify/Protect/Detect/Respond/Recover outcomes | G0/G2/G5/G7 | cyber risk governance outcomes؛ لا يفرض implementation واحدة |
| NIST SSDF 1.1 | GUIDE | Secure software development | G2–G5 | secure SDLC + root-cause prevention |
| OWASP ASVS 5.0.0 | GUIDE | App security verification | G2/G4/G5 | technical verification controls |
| OWASP API Security 2023 | GUIDE | API-specific risks | G2/G4/G5 | authz/authn/resource/business-flow/API inventory |
| Google SRE PRR/SLO | GUIDE/APPLIED | production readiness/reliability | G2/G5/G6 | architecture, dependencies, monitoring, emergency response, capacity, change, performance |
| DORA | RESEARCH/PRACTICE | delivery/operational performance | System-level | change throughput/stability/reliability trends، لا capability PASS وحدها |
| OpenTelemetry | GUIDE | telemetry model | G5/G6 | traces/metrics/logs/context |
| SLSA v1.2 | INDUSTRY SPEC | build/source provenance | G3/G5/G7 | supply-chain assurance and attestations |
| AWS Well-Architected Reliability | GUIDE/APPLIED | resilience/recovery/game days | G2/G5/G6 | failure management, quotas, DR, recovery testing |
| ISO 22301 | STD | Business continuity | G5/G7 | BC/DR governance |
| ISO/IEC 27035-1:2023 + NIST 800-61r3 | STD + GUIDE | Incident management | G5/G6/G7 | prepare/detect/respond/recover/learn |
| ISO/IEC 27036-3:2023 | STD | Supplier/supply-chain risk | G2/G5/G7 | third-party visibility/risk |
| BCBS 239 | FINANCIAL SUPERVISORY BENCHMARK | accurate/comprehensive/timely risk data | G1/G4/G5/G7 | financial-data assurance benchmark؛ لا claim banking compliance |
| BCBS Operational Resilience | FINANCIAL SUPERVISORY BENCHMARK | critical operations/interdependencies/tolerance for disruption | G2/G5/G6/G7 | institutional resilience benchmark |
| IOSCO Financial Benchmarks | FINANCIAL BENCHMARK GUIDE | benchmark governance/quality/accountability | Conditional | فقط إذا BLACKDARK ينشر index/benchmark يؤثر في مستخدمين/عملاء |
| AICPA TSC | ASSURANCE CRITERIA | security/availability/processing integrity/confidentiality/privacy | G5/G7 | readiness cross-check؛ ليس SOC 2 report/certification |

**قاعدة:** أي control لا يستطيع reviewer ربطه بمصدر أو بسياسة مشروع معلنة يجب أن يصنّف `UNMAPPED_POLICY` ويُراجع قبل فرضه.

---

# 119. ISO/IEC 25010 Full Quality Coverage — منع التركيز الضيق

> **[STD-derived POLICY]** لا يكفي أن تكون القدرة صحيحة وأمينة وسريعة. يجب تقييم خصائص جودة المنتج التسع حسب الانطباق.

لكل capability/system component، أنشئ applicability لـ:
1. Functional Suitability
2. Performance Efficiency
3. Compatibility
4. Interaction Capability
5. Reliability
6. Security
7. Maintainability
8. Flexibility
9. Safety

الحالات:
`APPLICABLE / NOT_APPLICABLE_WITH_RATIONALE`

**Red flag:** وجود quality characteristic مادية لم تُقيّم لأنها غير موجودة في checklist محلي.

لـM3/M4 أو user-facing critical paths، يجب أن توجد `QUALITY_CHARACTERISTIC_COVERAGE` قابلة للتتبع إلى الاختبارات/الأدلة.

---

# 120. Applied Reliability Engineering — Google SRE + AWS Reliability

## 120.1 Early Reliability Engagement

> **[GUIDE/APPLIED]** Google SRE يوضح أن إشراك reliability مبكرًا يقلل تكلفة علاج مشاكل الإنتاج المتأخرة، وأن PRR يغطي architecture/dependencies، monitoring، emergency response، capacity planning، change management، availability/latency/efficiency.

لذلك في المشروع:
- لا تؤجل G5 بالكامل إلى ما بعد build.
- لكل M2+، يبدأ reliability review في G2 ويُغلق تشغيليًا في G5.
- capability design يجب أن يحدد من البداية: failure boundaries, telemetry, capacity assumptions, rollback, dependency behavior.

## 120.2 Reliability by Framework / Shared Controls

عندما يوجد control مشترك صحيح مثل:
- entitlement/auth gateway.
- retry/backoff library.
- telemetry middleware.
- rate limiting.
- provider adapter standard.
- health/readiness framework.

الأفضل **reuse + centrally verified framework** بدل إعادة تنفيذ control لكل قدرة، بشرط:
- coverage mapping.
- version/provenance.
- consumer regression.
- no bypass.

هذا يطبق مبدأ Google SRE في codifying production best practices داخل frameworks مشتركة.

## 120.3 Failure-Recovery Proof

> **[GUIDE/APPLIED]** AWS Well-Architected Reliability يشدد على اختبار scalability/performance، resiliency، game days، وDR recovery implementation.

للخدمات الحرجة:
- لا يكفي backup creation؛ اختبر recovery/restore.
- اختبر failure isolation حيث ينطبق.
- نفذ fault injection/game-day مناسبًا للمخاطر قبل ASSURANCE_READY.
- وثق quotas/constraints/headroom التي قد تمنع failover.

---

# 121. Critical Operations & Tolerance for Disruption — Financial-Grade Resilience

> **[FINANCIAL BENCHMARK]** مستوحى من BCBS Operational Resilience، ويستخدم كمعيار تشدد مؤسسي وليس ادعاء امتثال مصرفي.

حدد على مستوى المنتج:
- `CRITICAL_USER_JOURNEYS`
- `CRITICAL_OPERATIONS`
- `TOLERANCE_FOR_DISRUPTION`
- dependencies/interdependencies اللازمة لكل critical operation.

لكل critical operation ارسم:
`User outcome → service → process → code/module → data → infrastructure → provider → secret/config → human/operational dependency`

واختبر severe-but-plausible scenarios مثل:
- primary data provider outage.
- stale/malformed market data.
- Redis outage.
- PostgreSQL outage/failover.
- queue backlog.
- cloud dependency degradation.
- secret/config missing.
- partial regional/platform outage حيث البيئة تدعم الاختبار.
- model/provider unavailable.

الحكم:
- إذا تجاوز recovery الفعلي tolerance المعلن، لا `ASSURANCE_READY` دون remediation أو authorized risk acceptance.

---

# 122. Financial Data Assurance — BCBS 239 + Analytical Integrity

> **[FINANCIAL BENCHMARK]** BCBS 239 يؤكد أهمية بيانات المخاطر الدقيقة والشاملة وفي الوقت المناسب. نستخدم هذه المبادئ كbenchmark لجودة منصة مالية، لا كادعاء خضوع مصرفي.

للبيانات/المخرجات المالية المادية، يجب إثبات:
- Accuracy.
- Completeness.
- Timeliness/Freshness.
- Adaptability under stress/change.
- Lineage and reconciliation.
- ownership/source authority.
- aggregation correctness.
- controls around manual overrides.
- exception visibility.

## 122.1 Data Control Totals / Reconciliation

حيث يوجد aggregation أو multi-provider synthesis:
- source-count reconciliation.
- missing-source detection.
- duplicate record detection.
- stale-source exclusion/flagging.
- total/count/hash invariants حيث تكون مفيدة.
- explainable aggregation rules.

## 122.2 Stress-Time Data Quality

لا تختبر البيانات في normal state فقط. اختبر:
- burst volatility.
- provider lag.
- out-of-order events.
- partial market outage.
- timestamp divergence.
- extreme price/volume values.

**قاعدة:** الدقة في الظروف العادية لا تكفي إذا capability هدفها دعم قرارات في ظروف سوق مضطربة.

---

# 123. Conditional Benchmark/Index Governance — IOSCO-inspired

> **CONDITIONAL.** ينطبق فقط إذا capability تنتج Benchmark/Index/Reference Rate/Composite Market Measure يستخدمه العميل كمرجع قرار أو يُنشر خارجيًا بهذه الصفة.

عند الانطباق:
- methodology owner.
- input-data hierarchy.
- methodology transparency.
- conflicts-of-interest review.
- third-party input oversight.
- change governance.
- exceptional-market-condition procedure.
- correction/restatement policy.
- audit trail.
- methodology versioning.

لا تستخدم هذا القسم لكل indicator عادي؛ فقط عندما تكون طبيعة المخرج Benchmark/Index مادية.

---

# 124. Secure Software Production — SSDF + ASVS + API + SLSA

## 124.1 Stable vs Draft Control

NIST SSDF v1.1 هو المرجع النهائي المستخدم حاليًا. أي عناصر من Draft SSDF v1.2 توسم:
`FUTURE_WATCH_NOT_GOVERNING`
حتى تصبح Final.

## 124.2 Root-Cause Prevention

لا يكفي إصلاح vulnerability واحدة. لكل High/Critical أو defect pattern مادي:
- root cause.
- sibling search.
- preventive test/control.
- secure coding pattern update.
- regression guard.

## 124.3 API Abuse Surface

إضافة إلى authn/authz، افحص:
- object-level authorization.
- function-level authorization.
- object-property authorization.
- unrestricted resource consumption.
- sensitive business-flow abuse.
- SSRF.
- inventory/version exposure.
- unsafe consumption of third-party APIs.

## 124.4 Build Provenance

لكل release مادي:
`source commit → reviewed change → CI run → dependency lock → build artifact/digest → provenance/attestation → deployment identity`

استخدم SLSA كمرجع لرفع assurance تدريجيًا، بدون claim مستوى SLSA لم يتحقق فعليًا.

---

# 125. Software Delivery & Change Health — DORA Research Layer

> **[RESEARCH/PRACTICE]** DORA هو برنامج بحثي طويل المدى في Google Cloud على عشرات الآلاف من الممارسين، ويستخدم لقياس software delivery/operational performance. لا تستخدم مقاييسه كبديل عن correctness/security gates.

على مستوى المنتج/الفريق تتبع، حيث يتوفر production data:
- change lead time.
- deployment frequency.
- failed deployment recovery time.
- change fail rate.
- deployment rework rate.

**ملاحظة Currency 2026:** DORA يستخدم حاليًا **خمسة** مقاييس software-delivery performance مجمعة إلى Throughput وInstability؛ لا تستخدم نموذج Four Keys القديم كأنه القائمة الحالية الكاملة.

ويُقاس reliability بصورة منفصلة عبر SLOs/measurement coverage/focus/target compliance عندما ينطبق.

استخدمها للإجابة:
- هل release process سريع لكن غير مستقر؟
- هل الاختبارات/الحوكمة ترفع lead time بلا قيمة؟
- هل change failure rate يتحسن؟
- هل MTTR/restore يتدهور؟

**ممنوع:** تحويل DORA metrics إلى target رقمي ثابت من الإنترنت لكل مشروع. Baseline واتجاه التحسن والسياق أهم من تقليد رقم خارجي.

---

# 126. Cyber Risk Governance — NIST CSF 2.0 Outcome Model

> **[GUIDE/FRAMEWORK]** CSF 2.0 يحدد outcomes ولا يفرض طريقة تنفيذ واحدة.

أضف cross-check على مستوى النظام عبر الوظائف الست:
- GOVERN
- IDENTIFY
- PROTECT
- DETECT
- RESPOND
- RECOVER

لكل material system risk يجب أن يعرف reviewer:
- من يملك القرار؟
- ما الأصل/الخطر؟
- ما الوقاية؟
- كيف نكتشف الفشل؟
- ماذا نفعل عند الحادث؟
- كيف نستعيد الخدمة/البيانات؟

استخدم NIST SP 1347 Informative References عند بناء crosswalks بدل اختراع mappings غير موثقة.

---

# 127. Incident & Recovery Lifecycle — NIST 800-61r3 + ISO 27035

كل material incident path يجب أن يملك:
`prepare → detect → report → assess → respond → recover → lessons learned → corrective action verification`

بعد incident مادي أو game day:
- root cause.
- contributing factors.
- blast radius.
- evidence timeline.
- corrective actions.
- owner/due date.
- regression/prevention control.
- verify closure effectiveness.

لا يُغلق corrective action بمجرد code change؛ يجب اختبار أنه عالج السبب أو خفض الخطر إلى المستوى المقبول.

---

# 128. Cloud Shared-Responsibility Assurance — ISO 27017:2026 / 27018:2025

للخدمات السحابية:
- document customer/provider responsibility split.
- identify controls inherited from cloud provider vs controls owned by BLACKDARK.
- validate configuration controls we own.
- map cloud-specific logging, identity, networking, encryption, backup, key/secret handling.
- document portability/exit where material.

عند PII في public cloud وBLACKDARK أو المورد يقوم بدور processor:
- clarify processor/controller roles.
- data location/transfer implications where known.
- retention/deletion.
- subprocessor visibility.
- access/audit.

لا يعتبر provider certification وحده evidence أن تطبيق BLACKDARK مضبوط صحيحة.

---

# 129. Control Design vs Operating Effectiveness — Assurance Discipline

> **[ASSURANCE/POLICY]** مستلهم من AICPA Trust Services Criteria ومنطق assurance المؤسسي.

افصل دائمًا:
- `CONTROL_DESIGN_EFFECTIVE`
- `CONTROL_IMPLEMENTED`
- `CONTROL_OPERATING_EFFECTIVE`

مثال:
وجود entitlement middleware = design/implementation evidence.
تشغيل allowed/denied/tenant-abuse tests على canonical path = operating evidence محلي.
إثباته في production/live telemetry = operating evidence حي.

لا تساوِ بين:
`control exists` و `control operated effectively`.

---

# 130. Evidence Strength Ladder — قوة الدليل

لكل claim مادي صنف أقوى دليل متاح:
- **E0** Claim only — غير مقبول.
- **E1** Static presence/config/code.
- **E2** Automated deterministic local/CI execution.
- **E3** Representative integrated/system execution.
- **E4** Live/production evidence tied to deployed artifact.
- **E5** Independent/effective-challenge review of E1–E4 plus exceptions/residual risk.

قواعد:
- `PASS_ENGINEERING` يحتاج عادة E2/E3 حسب الخطر.
- `PASS_LIVE` يحتاج E4 حيث البيئة المادية مختلفة.
- `ASSURANCE_READY` يحتاج E5 للمواد الجوهرية مع اكتمال الأدلة السابقة.
- لا ترفع E2 إلى E4 بسبب نجاح test مشابه للإنتاج.

---

# 131. Committee Reperformance Standard — اللجنة تستطيع إعادة التحقق

للـM2+، Evidence Pack يجب أن يسمح لمراجع مستقل بـ:
1. تحديد requirement والـowner.
2. إيجاد canonical implementation.
3. معرفة source/data/model version.
4. إعادة تشغيل test/oracle أو رؤية execution proof.
5. مطابقة tested SHA بالـbuild/deploy identity.
6. رؤية exceptions/residual risk.
7. تحديد ما هو local وما هو live وما هو independent.

إذا كان claim لا يمكن إعادة تتبعه إلا بذاكرة المطور أو تفسير شفهي غير موثق:
`ASSURANCE_GAP`.

---

# 132. V4 Retroactive Review Rule

عند اعتماد v4 على دفعات سابقة:
- لا تعِد بناء capability صحيحة.
- اعمل `V4_DELTA_RETROFIT_AUDIT` فقط.
- افحص فقط controls الجديدة أو الأدلة التي أصبحت أقوى.
- أي finding يصنف:
  - `NO_GAP`
  - `EVIDENCE_ONLY_GAP`
  - `LOCAL_ENGINEERING_GAP`
  - `LIVE_ONLY_GAP`
  - `INDEPENDENT_ONLY_GAP`
  - `POLICY_NOT_APPLICABLE`

أصلح `LOCAL_ENGINEERING_GAP` قبل freeze الجديد.
لا تستخدم v4 لخلق churn أو rewrite غير مبرر.

---

# 133. V4 Master Additions for Cursor

```text
AG. Verify the currency and status of governing references. Do not treat a draft as
final when a current published standard exists.

AH. Maintain a standards-to-gates crosswalk. Every mandatory control must map either
to a named authoritative source or to an explicitly labeled project policy.

AI. Evaluate all nine ISO/IEC 25010:2023 product-quality characteristics for
applicability; do not reduce quality to correctness, security and latency only.

AJ. For critical operations, map end-to-end dependencies and define a tolerance for
disruption. Test severe-but-plausible failure scenarios proportionate to risk.

AK. For material financial data, prove accuracy, completeness, timeliness/freshness,
lineage, reconciliation and stress-condition behavior. Use BCBS 239 only as a
financial-grade benchmark, never as a banking-compliance claim.

AL. If a capability publishes a material benchmark/index/reference rate, apply
benchmark governance, methodology versioning, input hierarchy, change/correction and
conflict-of-interest controls. Do not apply this mechanically to ordinary indicators.

AM. Separate secure-SDLC/root-cause prevention from vulnerability scanning. A fixed
vulnerability pattern requires sibling search and a preventive regression/control.

AN. Track software-delivery/change health at system level using contextual DORA-style
metrics when production data exists; these metrics never substitute for capability
correctness/security gates.

AO. Apply NIST CSF 2.0 as an outcome cross-check across GOVERN, IDENTIFY, PROTECT,
DETECT, RESPOND and RECOVER. Do not invent implementation requirements and attribute
them to CSF.

AP. Separate control design, implementation and operating effectiveness. Control
presence alone is not proof that the control operated correctly.

AQ. Grade evidence strength. Local/CI evidence must never be represented as live
production evidence, and live evidence must remain tied to deployed artifact identity.

AR. For M2+ evidence, enable independent reperformance: requirement, canonical code,
data/model version, test/oracle, tested/build/deploy identity, exceptions and status
must be traceable without oral developer explanation.

AS. Retrofit prior batches by delta only. Do not rebuild correct behavior merely
because the governing standard became stricter; close only real engineering/evidence
or live-assurance gaps.
```

---

# 134. V4 Research References — Official / Applied / Research Sources

> وجود المرجع هنا لا يعني شهادة أو امتثال. التصنيف `[STD]/[GUIDE]/[RESEARCH]/[FINANCIAL BENCHMARK]` هو الذي يحدد كيفية استخدامه.

1. ISO/IEC/IEEE 12207:2026 — Software life cycle processes  
   https://www.iso.org/standard/90219.html
2. ISO/IEC 25010:2023 — Product quality model  
   https://www.iso.org/standard/78176.html
3. ISO/IEC 25019:2023 — Quality-in-use model  
   https://www.iso.org/standard/78177.html
4. ISO/IEC/IEEE 29148:2018 — Requirements engineering  
   https://www.iso.org/standard/72089.html
5. ISO/IEC/IEEE 42010:2022 — Architecture description  
   https://www.iso.org/standard/74393.html
6. ISO/IEC 25012:2008 — Data quality model  
   https://www.iso.org/standard/35736.html
7. ISO 31000:2018 — Risk management guidelines (current published edition; revision under development)  
   https://www.iso.org/standards/popular/iso-31000-family
8. ISO/IEC 20000-1:2018 — Service management  
   https://www.iso.org/standard/70636.html
9. ISO 22301:2019 — Business continuity  
   https://www.iso.org/standard/75106.html
10. ISO/IEC 27005:2022 — Information-security risk  
    https://www.iso.org/standard/80585.html
11. ISO/IEC 27017:2026 — Cloud security controls  
    https://www.iso.org/standard/27017
12. ISO/IEC 27018:2025 — PII in public cloud  
    https://www.iso.org/standard/27018
13. ISO/IEC 27035-1:2023 — Incident management  
    https://www.iso.org/standard/78973.html
14. ISO/IEC 27036-3:2023 — Supply-chain security  
    https://www.iso.org/standard/82890.html
15. ISO/IEC 23894:2023 — AI risk management  
    https://www.iso.org/standard/77304.html
16. NIST Cybersecurity Framework 2.0  
    https://www.nist.gov/cyberframework
17. NIST SP 1347 — CSF 2.0 Informative References Quick-Start Guide (2026)  
    https://csrc.nist.gov/pubs/sp/1347/final
18. NIST SP 800-218 — SSDF v1.1 (Final)  
    https://csrc.nist.gov/pubs/sp/800/218/final
19. NIST SP 800-218 Rev.1 / SSDF v1.2 — Draft only at v4 publication time  
    https://csrc.nist.gov/pubs/sp/800/218/r1/ipd
20. NIST SP 800-61 Rev.3 — Incident Response (2025)  
    https://csrc.nist.gov/pubs/sp/800/61/r3/final
21. NIST AI RMF 1.0  
    https://www.nist.gov/itl/ai-risk-management-framework
22. OWASP ASVS 5.0.0  
    https://owasp.org/www-project-application-security-verification-standard/
23. OWASP API Security Top 10 2023  
    https://owasp.org/API-Security/editions/2023/en/0x11-t10/
24. Google SRE — Production Readiness Review / Engagement Model  
    https://sre.google/sre-book/evolving-sre-engagement-model/
25. Google SRE Workbook — SLO-based alerting  
    https://sre.google/workbook/alerting-on-slos/
26. Google Cloud DORA research / DevOps capabilities  
    https://dora.dev/  
    https://docs.cloud.google.com/architecture/devops
27. OpenTelemetry Signals  
    https://opentelemetry.io/docs/concepts/signals/
28. SLSA v1.2 Specification  
    https://slsa.dev/spec/v1.2/
29. AWS Well-Architected — Reliability Pillar  
    https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html
30. BCBS 239 implementation themes / risk-data aggregation and reporting  
    https://www.bis.org/publications/implementation-principles-effective-risk-data-aggregation-and-risk-reporting-bcbs-239-principles
31. BCBS Principles for Operational Resilience / consolidated guidance  
    https://www.bis.org/committees/bcbs/basel-consolidated-guidelines/module/orr/20
32. IOSCO Principles for Financial Benchmarks  
    https://www.iosco.org/library/pubdocs/pdf/IOSCOPD415.pdf
33. AICPA Trust Services Criteria / SOC 2 reference criteria  
    https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022

---

# 135. القرار النهائي لـv4

أصبح المرجع بعد v4 مكوّنًا من خمس طبقات مترابطة:

1. **Engineering Correctness** — requirement/design/code/data/result correctness.
2. **Operational & Live Validation** — canonical live path, real dependencies, SLOs, resilience and user outcome.
3. **Institutional Assurance** — risk, governance, evidence, independent challenge, continuity, supplier/model/security assurance.
4. **Evidence Hardening / Adversarial Audit** — coverage, canonical-path proof, warning hygiene, SSOT consistency, provenance.
5. **Global Research & Applied-Practice Crosswalk** — current standards, outcome frameworks, financial-grade data/resilience benchmarks, and practices demonstrated at scale such as Google SRE/DORA and AWS Well-Architected.

الهدف النهائي:

> **NO KNOWN MATERIAL DEFICIENCY + REPRODUCIBLE/REPERFORMABLE EVIDENCE + CURRENT AUTHORITATIVE REFERENCES + MACHINE-VERIFIABLE COVERAGE + CANONICAL FULL-PATH PROOF + FINANCIAL-DATA INTEGRITY + CONTROLLED RESIDUAL RISK + LIVE USER OUTCOME + SYSTEM-LEVEL RESILIENCE + INDEPENDENT ASSURANCE**

مع الحفاظ على المبادئ غير القابلة للتفاوض:

- `PASS_ENGINEERING != PASS_LIVE != ASSURANCE_READY`.
- `NO EVIDENCE = NO PASS`.
- لا local/staging claim = production claim.
- لا policy داخلية تُنسب إلى ISO/NIST/Google/AWS/BCBS/IOSCO كأنها نص ملزم.
- لا إعادة بناء صحيحة لمجرد زيادة صرامة evidence؛ retrofit يكون delta/risk-based.
- لا ادعاء "صفر عيوب للأبد"؛ الحكم الدفاعي هو **NO KNOWN MATERIAL DEFICIENCY** عند استيفاء الشروط.


---

# 136. المراجعة العميقة نقطةً بنقطة — V5 Point-by-Point Validation Register

> **تاريخ المراجعة:** 6 سبتمبر 2026. تمت إعادة مراجعة جميع الأقسام الرئيسية 0–135 مقابل المصادر الرسمية/المطبقة والتمييز بين ما هو معيار ملزم، إرشاد، benchmark قطاعي، مواصفة صناعية، أو سياسة مشروع.

## 136.1 معنى حالات المراجعة

- `VALIDATED_SOURCE_ALIGNED`: المحتوى متسق في الجوهر مع المصدر/المصادر الحاكمة.
- `VALIDATED_PROJECT_POLICY`: سياسة مشروع مشروعة ومفيدة، لكنها لا تُنسب لمعيار خارجي كالتزام حرفي.
- `VALIDATED_CONDITIONAL`: صالح فقط عند انطباق نوع البيانات/المخاطر/القدرة/التنظيم المحدد.
- `CORRECTED_V5` / `CORRECTED_SCOPE_V5`: تم تصحيح صياغة أو تصنيف أو حد انطباق في v5.
- `REFRESHED_V5`: تم تحديث حداثة المرجع/الإصدار أو طريقة استخدامه.
- `STRENGTHENED_V5`: المحتوى صحيح لكن أضيفت ضوابط أقوى بعد البحث.

| القسم | العنوان | نتيجة المراجعة |
|---:|---|---|
| 0 | تصنيف قوة المرجع — لمنع الخلط | CORRECTED_V5 |
| 1 | الطبقة المرجعية المعتمدة | CORRECTED_V5 |
| 2 | تعريف النجاح الحقيقي للقدرة | VALIDATED_SOURCE_ALIGNED |
| 3 | حالات التصنيف قبل البناء — Pre-Build State Classification | VALIDATED_PROJECT_POLICY |
| 4 | قرار Build / Extend / Refactor / Replace / Reuse | VALIDATED_PROJECT_POLICY |
| 5 | دورة حياة القدرة من الفكرة إلى المستخدم | VALIDATED_SOURCE_ALIGNED |
| 6 | Expected Output — الصيغة الصحيحة | VALIDATED_PROJECT_POLICY |
| 7 | القالب الخماسي — النسخة المؤسسية المطوّرة | VALIDATED_PROJECT_POLICY |
| 8 | مصفوفة التتبع RTM | VALIDATED_SOURCE_ALIGNED |
| 9 | التكرار — الاكتشاف الشامل | VALIDATED_SOURCE_ALIGNED |
| 10 | الحكم على التكرار | VALIDATED_PROJECT_POLICY |
| 11 | العلاج الجذري للتكرار | VALIDATED_PROJECT_POLICY |
| 12 | شروط إغلاق مشكلة التكرار | VALIDATED_PROJECT_POLICY |
| 13 | الأبطال الستة — Hero Aggregation Standard | VALIDATED_PROJECT_POLICY |
| 14 | جودة البيانات — Data Quality Gate | VALIDATED_SOURCE_ALIGNED |
| 15 | الاختبارات المالية/الكمية | VALIDATED_CONDITIONAL |
| 16 | AI / ML / Generative AI | STRENGTHENED_V5 |
| 17 | الأمن — Security Gate | VALIDATED_SOURCE_ALIGNED |
| 18 | الخصوصية والبيانات الحساسة | VALIDATED_CONDITIONAL |
| 19 | الأداء — Performance Standard | CORRECTED_V5 |
| 20 | الاعتمادية والمرونة | VALIDATED_SOURCE_ALIGNED |
| 21 | Observability — بوابة مستقلة | VALIDATED_SOURCE_ALIGNED |
| 22 | UX / Interaction / Accessibility | VALIDATED_SOURCE_ALIGNED |
| 23 | API / Contract Quality | VALIDATED_CONDITIONAL |
| 24 | قاعدة البيانات والمهاجرات | VALIDATED_SOURCE_ALIGNED |
| 25 | Deployment / Release Safety | VALIDATED_SOURCE_ALIGNED |
| 26 | Regression Gate | VALIDATED_SOURCE_ALIGNED |
| 27 | Maintainability Gate | VALIDATED_SOURCE_ALIGNED |
| 28 | Operational Readiness | VALIDATED_SOURCE_ALIGNED |
| 29 | حالات الإغلاق الموحدة | VALIDATED_PROJECT_POLICY |
| 30 | Evidence Standard | VALIDATED_SOURCE_ALIGNED |
| 31 | Git / Change Evidence | VALIDATED_SOURCE_ALIGNED |
| 32 | Independent Verification | VALIDATED_SOURCE_ALIGNED |
| 33 | قواعد خاصة بالعمل مع Cursor / Coding Agent | VALIDATED_PROJECT_POLICY |
| 34 | Definition of Done — البوابة النهائية | VALIDATED_PROJECT_POLICY |
| 35 | نموذج تقرير الإغلاق لكل قدرة | VALIDATED_PROJECT_POLICY |
| 36 | نموذج Hero Closure | VALIDATED_PROJECT_POLICY |
| 37 | معيار الأداء المقترح — النسخة المنقحة | VALIDATED_PROJECT_POLICY |
| 38 | مستويات المخاطر | VALIDATED_PROJECT_POLICY |
| 39 | قواعد عدم تضخيم الإغلاق | VALIDATED_PROJECT_POLICY |
| 40 | ما الذي يعني "تحقيق الهدف كاملًا دون قصور"؟ | VALIDATED_SOURCE_ALIGNED |
| 41 | مراجعة دورية بعد الإطلاق | VALIDATED_SOURCE_ALIGNED |
| 42 | ترتيب التنفيذ الإلزامي المقترح | VALIDATED_PROJECT_POLICY |
| 43 | Master Rule Set — نسخة قصيرة لإلزام Cursor | VALIDATED_PROJECT_POLICY |
| 44 | مصادر رسمية/موثقة | REFRESHED_V5 |
| 45 | القرار المؤسسي النهائي | VALIDATED_PROJECT_POLICY |
| 46 | طبقة الفحص المؤسسي الصارم — Institutional Assurance Layer | VALIDATED_SOURCE_ALIGNED |
| 47 | نموذج Stage-Gate المؤسسي | VALIDATED_PROJECT_POLICY |
| 48 | Materiality / Criticality Classification | VALIDATED_CONDITIONAL |
| 49 | Enterprise Risk Management Gate | VALIDATED_SOURCE_ALIGNED |
| 50 | Exception & Risk Acceptance Governance | VALIDATED_PROJECT_POLICY |
| 51 | Segregation of Duties / Four-Eyes | VALIDATED_PROJECT_POLICY |
| 52 | Evidence Assurance — جودة الدليل | VALIDATED_PROJECT_POLICY |
| 53 | Control Mapping / Control Matrix | VALIDATED_PROJECT_POLICY |
| 54 | Change Management & Configuration Governance | VALIDATED_PROJECT_POLICY |
| 55 | Asset / Dependency Inventory | VALIDATED_SOURCE_ALIGNED |
| 56 | Software Supply Chain Assurance | STRENGTHENED_V5 |
| 57 | Supplier / Third-Party Risk | VALIDATED_CONDITIONAL |
| 58 | Cloud Security Assurance | VALIDATED_CONDITIONAL |
| 59 | Vulnerability Management | VALIDATED_PROJECT_POLICY |
| 60 | Incident Response & Lessons Learned | VALIDATED_SOURCE_ALIGNED |
| 61 | Business Continuity / Disaster Recovery | REFRESHED_V5 |
| 62 | Service Management & Operational Discipline | VALIDATED_SOURCE_ALIGNED |
| 63 | Capacity Engineering | VALIDATED_PROJECT_POLICY |
| 64 | Resilience / Fault Injection | VALIDATED_PROJECT_POLICY |
| 65 | Financial / Analytical Integrity Gate | VALIDATED_CONDITIONAL |
| 66 | Data Governance — مستوى لجنة الفحص | VALIDATED_CONDITIONAL |
| 67 | Audit Logging / Non-Repudiation | VALIDATED_PROJECT_POLICY |
| 68 | Multi-Tenancy / Institutional Isolation | VALIDATED_PROJECT_POLICY |
| 69 | Model Risk Management — مستوى مالي مؤسسي | CORRECTED_SCOPE_V5 |
| 70 | Processing Integrity / SOC 2 Readiness Cross-Check | CLARIFIED_V5 |
| 71 | Privacy by Design / Data Minimization | VALIDATED_CONDITIONAL |
| 72 | Backup / Key / Secret Recovery | VALIDATED_PROJECT_POLICY |
| 73 | Release Authenticity | VALIDATED_PROJECT_POLICY |
| 74 | Environment Parity & Test Representativeness | VALIDATED_PROJECT_POLICY |
| 75 | Negative Assurance / Abuse Cases | VALIDATED_PROJECT_POLICY |
| 76 | Invariant & Property-Based Assurance | VALIDATED_PROJECT_POLICY |
| 77 | Security Adversarial Validation | VALIDATED_PROJECT_POLICY |
| 78 | Performance Acceptance — النسخة الأصعب | VALIDATED_PROJECT_POLICY |
| 79 | SLO / Error Budget Governance | VALIDATED_PROJECT_POLICY |
| 80 | Recovery Objectives Matrix | VALIDATED_CONDITIONAL |
| 81 | Documentation Assurance | VALIDATED_PROJECT_POLICY |
| 82 | Ownership / RACI | VALIDATED_PROJECT_POLICY |
| 83 | Technical Debt Governance | VALIDATED_PROJECT_POLICY |
| 84 | Deprecation / Retirement | VALIDATED_PROJECT_POLICY |
| 85 | Institutional Due-Diligence Evidence Room | VALIDATED_PROJECT_POLICY |
| 86 | Committee Challenge Questions | VALIDATED_PROJECT_POLICY |
| 87 | Red-Flag Conditions — مانعات فورية للجنة | VALIDATED_PROJECT_POLICY |
| 88 | Assurance Status Model | VALIDATED_PROJECT_POLICY |
| 89 | Institutional Closure Record — النسخة النهائية | VALIDATED_PROJECT_POLICY |
| 90 | Institutional Scoring — لا يستبدل Gates | VALIDATED_PROJECT_POLICY |
| 91 | متطلبات اللجنة على مستوى المنتج بالكامل | VALIDATED_PROJECT_POLICY |
| 92 | Systemic Duplicate / Coupling Review | VALIDATED_PROJECT_POLICY |
| 93 | Acquisition / Institutional Technical Due Diligence Pack | VALIDATED_CONDITIONAL |
| 94 | IP / License Provenance | VALIDATED_CONDITIONAL |
| 95 | Key-Person / Bus-Factor Risk | VALIDATED_CONDITIONAL |
| 96 | Cost / Resource Sustainability | VALIDATED_CONDITIONAL |
| 97 | Continual Assurance | VALIDATED_PROJECT_POLICY |
| 98 | Evidence Freshness | VALIDATED_PROJECT_POLICY |
| 99 | معيار "لا يوجد قصور جوهري" | VALIDATED_PROJECT_POLICY |
| 100 | Master Institutional Rule Set — المستوى الأعلى لـCursor | VALIDATED_PROJECT_POLICY |
| 101 | مراجع الإضافات الجديدة — مصادر رسمية/موثقة | REFRESHED_V5 |
| 102 | القرار النهائي بعد رفع مستوى الفحص | VALIDATED_SOURCE_ALIGNED |
| 103 | طبقة تقوية الأدلة — Evidence Hardening Layer | VALIDATED_PROJECT_POLICY |
| 104 | الفصل الإلزامي بين State Classification وClosure/Execution Status | VALIDATED_PROJECT_POLICY |
| 105 | تقوية فحص التكرار — Exhaustive Duplicate Coverage Proof | VALIDATED_PROJECT_POLICY |
| 106 | Canonical Full-Path Verification — اختبار المسار الحقيقي الكامل | VALIDATED_PROJECT_POLICY |
| 107 | Six Heroes — مصفوفة الانطباق الفردية | VALIDATED_PROJECT_POLICY |
| 108 | Clean-Pass Semantics — لا PASS مع تحذير غير مفسر | VALIDATED_PROJECT_POLICY |
| 109 | Project-Wide SSOT / Progress Consistency | VALIDATED_PROJECT_POLICY |
| 110 | Evidence Pack Provenance — إثبات الـCI والـQuality Gates | VALIDATED_PROJECT_POLICY |
| 111 | Cross-Batch Regression Evidence Hardening | VALIDATED_PROJECT_POLICY |
| 112 | Performance Evidence Hardening | VALIDATED_PROJECT_POLICY |
| 113 | Anti-Bureaucracy / No-False-Standards Rule | VALIDATED_PROJECT_POLICY |
| 114 | معيار Freeze المحلي بعد Evidence Hardening | VALIDATED_PROJECT_POLICY |
| 115 | تحديث Master Institutional Rule Set لـCursor — v3 Additions | VALIDATED_PROJECT_POLICY |
| 116 | قرار v3 النهائي | VALIDATED_PROJECT_POLICY |
| 117 | Research Refresh 2026 — حوكمة صلاحية المراجع | REFRESHED_V5 |
| 118 | Standards-to-Gates Crosswalk — مصفوفة المصدر إلى البوابة | CORRECTED_V5 |
| 119 | ISO/IEC 25010 Full Quality Coverage — منع التركيز الضيق | VALIDATED_PROJECT_POLICY |
| 120 | Applied Reliability Engineering — Google SRE + AWS Reliability | VALIDATED_PROJECT_POLICY |
| 121 | Critical Operations & Tolerance for Disruption — Financial-Grade Resilience | VALIDATED_CONDITIONAL |
| 122 | Financial Data Assurance — BCBS 239 + Analytical Integrity | VALIDATED_CONDITIONAL |
| 123 | Conditional Benchmark/Index Governance — IOSCO-inspired | VALIDATED_CONDITIONAL |
| 124 | Secure Software Production — SSDF + ASVS + API + SLSA | REFRESHED_V5 |
| 125 | Software Delivery & Change Health — DORA Research Layer | CORRECTED_V5 |
| 126 | Cyber Risk Governance — NIST CSF 2.0 Outcome Model | VALIDATED_PROJECT_POLICY |
| 127 | Incident & Recovery Lifecycle — NIST 800-61r3 + ISO 27035 | VALIDATED_PROJECT_POLICY |
| 128 | Cloud Shared-Responsibility Assurance — ISO 27017:2026 / 27018:2025 | REFRESHED_V5 |
| 129 | Control Design vs Operating Effectiveness — Assurance Discipline | VALIDATED_PROJECT_POLICY |
| 130 | Evidence Strength Ladder — قوة الدليل | VALIDATED_PROJECT_POLICY |
| 131 | Committee Reperformance Standard — اللجنة تستطيع إعادة التحقق | VALIDATED_PROJECT_POLICY |
| 132 | V4 Retroactive Review Rule | VALIDATED_PROJECT_POLICY |
| 133 | V4 Master Additions for Cursor | VALIDATED_PROJECT_POLICY |
| 134 | V4 Research References — Official / Applied / Research Sources | REFRESHED_V5 |
| 135 | القرار النهائي لـv4 | VALIDATED_V5 |

## 136.2 قواعد ناتجة عن المراجعة الشاملة

1. **Authority beats familiarity:** المرجع الرسمي الحالي أعلى من checklist تاريخي أو ممارسة شائعة.
2. **Published beats draft:** أي DIS/CD/Draft يُراقب ولا يصبح حاكمًا قبل النشر، إلا كـfuture-watch.
3. **Scope beats prestige:** BCBS/Federal Reserve/IOSCO لا تصبح إلزامًا على BLACKDARK لمجرد قوتها؛ تستخدم كـbenchmark عندما يتطابق نطاق الخطر.
4. **Outcome + evidence beats artifact naming:** لا يفرض اسم ملف أو قالب بعينه إذا كانت النتيجة والدليل والتتبع مثبتة.
5. **Applied practice complements standards:** Google SRE/AWS/DORA تكمّل ISO/NIST في التشغيل والاعتمادية والتسليم، ولا تُنسب كمعايير ISO.
6. **Current research must be versioned:** DORA وNIST AI RMF وغيرها مصادر متطورة؛ سجّل تاريخ التحقق والإصدار.
7. **Regulated financial guidance is conditional:** SR 26-2 وBCBS/IOSCO تستخدم كـfinancial-grade challenge benchmark دون ادعاء الخضوع أو الامتثال.
8. **Generative/agentic AI scope must not be inferred:** SR 26-2 لا يغطي GenAI/agentic AI رسميًا؛ استخدم ISO/IEC 42001 + ISO/IEC 23894 + NIST AI RMF + ضوابط المشروع لهذه الفئة.
9. **Accessibility uses W3C Recommendation status:** WCAG 2.2 معيار ويب رسمي، لا ISO.
10. **SLSA is an industry specification:** يمكن إثبات level/requirements، لكن لا توصف كشهادة ISO-style.

---

# 137. سجل صلاحية المراجع — Authority Currency Register (6 Sep 2026)

- ISO/IEC/IEEE 12207:2026: **PUBLISHED / CURRENT**.
- ISO/IEC/IEEE 29148:2018: **CURRENT PUBLISHED**؛ Edition 3 DIS **UNDER DEVELOPMENT**.
- ISO/IEC 25010:2023: **PUBLISHED / CURRENT**.
- ISO/IEC 25019:2023: **PUBLISHED / CURRENT**.
- ISO/IEC 25012:2008: **PUBLISHED / CURRENT**.
- ISO/IEC/IEEE 42010:2022: **PUBLISHED / CURRENT**.
- ISO/IEC/IEEE 29119-2:2021: **PUBLISHED / CURRENT**.
- ISO/IEC 27001:2022: **PUBLISHED / CURRENT**.
- ISO/IEC 27701:2025: **PUBLISHED / CURRENT**.
- ISO/IEC 27017:2026: **PUBLISHED / CURRENT**.
- ISO/IEC 27018:2025: **PUBLISHED / CURRENT**.
- ISO/IEC 27035-1:2023: **PUBLISHED / CURRENT**.
- ISO/IEC 27036-2:2022 / 27036-3:2023: **PUBLISHED / CURRENT**.
- ISO 22301:2019 + Amd 1:2024: **CURRENT PUBLISHED**؛ Edition 3 **UNDER DEVELOPMENT**.
- ISO 31000:2018: **CURRENT PUBLISHED**؛ revision **UNDER DEVELOPMENT**.
- ISO/IEC 42001:2023: **PUBLISHED / CURRENT**.
- ISO/IEC 25059:2023: **PUBLISHED / TO BE REVISED**؛ لا تفترض replacement حتى النشر.
- ISO/IEC 23894:2023: **PUBLISHED / CURRENT**.
- NIST CSF 2.0: **CURRENT FRAMEWORK**.
- NIST SP 800-218 SSDF 1.1: **FINAL CURRENT GOVERNING VERSION USED HERE**.
- NIST SP 800-61 Rev.3: **FINAL / 2025**.
- NIST SP 1347: **FINAL / AUG 2026**.
- NIST AI RMF 1.0: **CURRENT PUBLISHED, REVISION ACTIVITY UNDERWAY**.
- OWASP ASVS 5.0.0: **LATEST STABLE**.
- OWASP API Security Top 10: **2023 CURRENT EDITION USED HERE**.
- W3C WCAG 2.2: **W3C RECOMMENDATION / WEB STANDARD**.
- SLSA v1.2: **APPROVED INDUSTRY SPECIFICATION**.
- DORA: **CURRENT 2026 measurement model uses five software-delivery metrics**; version/date metrics definitions.
- Google SRE PRR/SLO: **APPLIED ENGINEERING GUIDE**.
- AWS Well-Architected Reliability: **APPLIED CLOUD RELIABILITY GUIDE**.
- BCBS 239 / Operational Resilience: **CURRENT SUPERVISORY BENCHMARKS, CONDITIONAL USE**.
- Federal Reserve SR 26-2 (2026): **CURRENT SUPERVISORY MODEL-RISK GUIDANCE FOR COVERED BANKS; conditional benchmark only here; excludes GenAI/agentic AI from formal scope**.
- AICPA TSC: **ASSURANCE CRITERIA; no SOC 2 claim without examination/report**.

---

# 138. قرار v5 النهائي

**v5 هو المرجع الحاكم بعد المراجعة العميقة لجميع محتويات v4.**

لا يعني ذلك أن المرجع لن يتغير مستقبلًا؛ أي معيار أو framework متغير يخضع لـCurrency Review قبل استخدامه في batch جديد أو assurance نهائي.

الهدف النهائي يظل:

> **NO KNOWN MATERIAL DEFICIENCY + RIGHT REQUIREMENT + RIGHT CANONICAL IMPLEMENTATION + FULL-PATH EVIDENCE + LIVE USER OUTCOME + OPERATING-EFFECTIVE CONTROLS + SYSTEM-LEVEL RESILIENCE + CURRENT AUTHORITATIVE REFERENCES + INDEPENDENT ASSURANCE**

---

# 139. BLACKDARK Completion Scope & Execution Policy — دمج Completion & Real-Capability Standard

> **[POLICY]** هذا القسم يضيف فقط قواعد المشروع التي لم تكن مثبتة بصراحة في v5 قبل هذا الدمج. جميع متطلبات صحة القدرة، الدليل، full-path، التكرار، الأبطال الستة، الأمن، البيانات، الأداء، regression، الضمان، وAnti-Bureaucracy تبقى محكومة بالأقسام الأصلية أعلاه دون إعادة نسخها هنا.

## 139.1 النطاق الرسمي للقدرات

- النطاق الرسمي لبرنامج اكتمال BLACKDARK هو **826 قدرة**.
- القدرات **827–978 خارج نطاق برنامج الـ826 عمدًا** ولا تدخل في عداد اكتماله أو نسبته إلا بقرار حوكمة صريح يغيّر النطاق ويُحدّث الـSSOT الحاكم.
- أي Alias / Reuse / Duplicate relationship لا يخلق قدرة إضافية ولا يضاعف العد.

## 139.2 سياسة الدفعات والترقيم

لأغراض التنظيم والتتبع فقط، يعتمد البرنامج دفعات من 50 قدرة:
- `Batch01 = 1–50`
- `Batch02 = 51–100`
- `Batch03 = 101–150`
- ويستمر التسلسل بنفس القاعدة حتى اكتمال نطاق الـ826، مع دفعة أخيرة بحجمها الفعلي.

قواعد الترقيم:
- لا يُستخدم اسم Batch واحد لنطاقين مختلفين.
- يجب أن يربط أي evidence أو regression artifact بين اسم الدفعة ونطاق IDs بصورة غير ملتبسة.
- لا تُفتح دفعة تنفيذية جديدة قبل وجود إغلاق محلي مقبول للسابقة أو blocker خارجي صريح موثق لا يمكن حله محليًا.
- هذا تنظيم مشروع `[POLICY]` وليس ادعاءً بأنه requirement من ISO/IEC/IEEE.

## 139.3 Evidence Pack Functions — الوظائف لا أسماء الملفات

لكل دفعة يجب أن تكون الوظائف التالية مغطاة بأدلة قابلة لإعادة التحقق، مع إعادة استخدام الـartifacts الحاكمة الموجودة حيثما تكفي:
- scope/inventory evidence؛
- requirements traceability؛
- semantic acceptance/correctness؛
- canonical/duplicate reconciliation؛
- actual consumer-path evidence؛
- security/entitlement evidence؛
- data/provenance evidence حسب الانطباق؛
- reliability/performance evidence حسب الانطباق؛
- affected regression evidence؛
- formal quality/security gate evidence؛
- source/build/run provenance؛
- engineering/live/assurance status.

لا تُفرض أسماء ملفات ثابتة ما دام control objective والدليل والتتبع وإعادة الأداء محققة، وفق §113.

## 139.4 Current Project State منفصل عن المعيار الحاكم

الحقائق الزمنية مثل:
- PRs المدمجة؛
- HEAD الحالي؛
- الدفعات المغلقة أو المعاد فتحها؛
- blockers الحالية؛
- deployment state؛
- production evidence؛
- G6/G7/assurance state؛

يجب أن تحفظ في **Current Project State / dated status record** أو SSOT تشغيلي حاكم، ولا تُحوّل إلى قواعد دائمة داخل هذا المعيار. هذا يمنع stale historical facts من التحول إلى policy أو مصدر حقيقة منافس.

## 139.5 قاعدة الاكتمال الكلي لبرنامج الـ826

لا يعني اكتمال البرنامج وجود 826 اسمًا أو 826 route أو 826 صفًا أخضر. يعني أن كل ID داخل النطاق قد حُسم عبر الأبعاد الحاكمة، وأن كل قدرة مادية لها تنفيذ دلالي حقيقي أو علاقة canonical صحيحة مثبتة، وأن تكاملها ومسار استهلاكها وجودة بياناتها وضوابطها وأدلتها مكتملة حسب الانطباق، مع الفصل الصريح بين `PASS_ENGINEERING` و`PASS_LIVE` و`ASSURANCE_READY`.

الهدف النهائي للبرنامج هو **826 قدرة محسومة وحقيقية وقابلة للإثبات تعمل كنظام واحد**، لا تضخيم عددي ولا واجهات أو bindings شكلية.

