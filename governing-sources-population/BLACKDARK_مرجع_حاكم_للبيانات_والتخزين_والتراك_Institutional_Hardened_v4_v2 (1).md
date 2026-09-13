# BLACKDARK Domain Governing Reference — v4_v2

> **سلطة الحوكمة الحالية:** `BLACKDARK Institutional Standard v6` هو المرجع المؤسسي الأعلى للمشروع. هذه الوثيقة `v4_v2` هي المرجع التخصصي الحاكم للبيانات والتخزين والتراك، وتبقى subordinate لـ v6.
>
> **قاعدة سلامة المصدر:** النص الأصلي لـ `v4` محفوظ أدناه دون حذف أو إعادة صياغة. أي إشارة تاريخية داخله إلى `v5` تُعامل كسجل سياقي للإصدار الذي كُتبت تحته، ولا تمنح v5 سلطة حاكمة حالية. عند التطبيق المستقبلي، v6 هو الحاكم للمنهج والبوابات والحالات والأدلة.
>
> **قاعدة التعارض:** عند تعارض حقيقي: v6 يحكم المتطلبات المؤسسية العامة؛ وv4_v2 يحكم المتطلبات التخصصية للبيانات/التخزين/التراك ما لم تخالف v6؛ والملاحق المصدرية المحفوظة داخل v4 تحكم نية المصدر داخل النطاق التخصصي فقط، ولا تتجاوز v6.

---

BLACKDARK
MASTER COMPOUNDING VALUE, PLATFORM & PRE-LAUNCH ASSET SPECIFICATION
وثيقة استشارية موحّدة للبرمجة والتصميم والهندسة المؤسسية وتعظيم القيمة
مبنية حصريًا على التقارير الخمسة المقدمة، مع فصل صارم بين النص المرجعي المحفوظ وبين الصياغة الاستشارية المنظمة.
حالة الوثيقة: MASTER SPECIFICATION - SOURCE-PRESERVED - FIVE-PASS REVIEWED

# 0. ضبط الوثيقة ومبدأ عدم التحريف
هذه الوثيقة تحتوي على مستويين منفصلين منعًا لأي سهو أو تحريف: (أ) مواصفة استشارية منظمة تعيد ترتيب المتطلبات دون إسقاطها؛ (ب) ملاحق مصدرية تحفظ التقارير الخمسة كاملة بصورتها النصية المرجعية. عند أي تعارض لغوي بين الصياغة الاستشارية والنص الأصلي، يكون الملحق المرجعي هو السلطة الأعلى.
لا يتم اعتبار أي تشابه بين بندين مبررًا لحذف أحدهما من السجل المرجعي. يمكن تجميع البنود المتقاربة داخل الصياغة الاستشارية فقط، مع بقاء النصوص الأصلية محفوظة بالكامل في الملاحق.
## 0.1 شهادة المراجعة الخماسية
## 0.2 سجل سلامة المصادر
# 1. التكليف التنفيذي للاستشاري
المطلوب ليس إضافة Features شكلية أو إنشاء مستودعات بلا غرض. المطلوب تصميم وتنفيذ منظومة تجعل BLACKDARK أصلًا يتراكم في القيمة منذ مرحلة التطوير، بحيث يتحول التشغيل بمرور الزمن إلى بيانات مملوكة أو مشتقة، معرفة سوقية، سجل قرارات ونتائج، أدلة ثقة، معرفة تشغيلية، ملكية فكرية، شبكة توزيع، تكاملات مؤسسية، وذاكرة تجارية قابلة للفحص والاستحواذ.
المبدأ الحاكم: DON'T DELETE KNOWLEDGE - COMPOUND IT. أي معرفة ذات قيمة مستقبلية يجب ألا تبقى في Log مؤقت أو محادثة أو تحليل منفصل؛ بل تتحول إلى سجل structured + versioned + searchable + attributable + governed.
# 2. المعمارية العليا لتراكم القيمة
## 2.1 محركات التراكم الثمانية
Flywheel المستهدف: More operation → more evidence → more knowledge → better intelligence → better product → more users → more outcomes → stronger distribution → more revenue → more institutional adoption → stronger moat → higher strategic value.
## 2.2 خزائن القيمة الاثنتا عشرة
# 3. Platform & Enterprise Architecture - ما يجب زرعه أثناء التصميم
# 4. Proprietary Intelligence & Asset Accumulation System
يجب تصميم طبقة منطقية مستقلة هدفها تحويل التشغيل إلى أصول متراكمة، لا مجرد تخزين بيانات. التقسيم أدناه Logical؛ لا يعني إنشاء Database منفصلة لكل بند.
Raw/Normalized Market History
Derived Intelligence Store
Signal Registry
Prediction Ledger
Decision Ledger
Outcome Ledger
Failure & Incident Intelligence
Market Event Knowledge Base
Entity/Relationship Graph
Feature Store
Model Registry
Experiment Registry
Data Lineage / Provenance
Usage & Product Analytics
Commercial/Growth Intelligence
Evidence & Track-Record Store
## 4.1 طبقات التشغيل الأربع
### Collection Layer
جمع البيانات المسموح بجمعها من Market/Order Book/OI/Funding/Liquidations/On-chain وغيرها، إضافة إلى Signals/Predictions/Decisions التي ينتجها النظام.
### Historical/Proprietary Data Layer
حفظ التاريخ المفيد بشكل structured/versioned مع provenance وحقوق الاستخدام.
### Intelligence/Learning Layer
Jobs/Engines تربط Inputs → Signal → Prediction/Decision → Outcome → Error → Performance.
### UI/UX Layer
عرض القيمة للمستخدم بصورة مضغوطة: Confidence, Track Record, Historical Similarity, Evidence, Data Quality.
# 5. الأصول التي يجب أن تتراكم - التصنيف المؤسسي الكامل
# 6. أنظمة المعرفة والتقييم المتقدمة التي لا يجوز إسقاطها
# 7. Data Rights, Privacy, IP & Corporate Defensibility
Data Rights Registry: لكل مصدر - storage rights، retention limits، derived works، resale، training، redistribution/API rights.
IP Provenance: من كتب الأصل، مصدره، dependencies/licenses، هل هو proprietary، هل توجد قيود copyleft/GPL أو competitor wrappers.
SBOM + Dependency History: تاريخ المكونات والتراخيص والإصدارات والمخاطر.
Dataset Genealogy: Source → Raw → Cleaning → Normalization → Enrichment → Features → Model/Engine → Output.
Purpose/Consent/Legal Basis where applicable → Minimization → Security → Retention → Access → Deletion/Anonymization.
عدم جمع كل ما يمكن جمعه؛ البيانات غير الضرورية أو غير المرخصة قد تتحول إلى Liability تقلل قيمة الأصل.
# 8. تسريع التراكم قبل الإطلاق دون تزوير التاريخ
الاستراتيجية المتوازية المعتمدة: Historical Backfill + Point-in-Time Replay + Event Reconstruction + Parallel Simulation + Synthetic/Stress Testing + 24/7 Shadow Production + Continuous Outcome Evaluation + Knowledge Extraction + Entity Graph Backfill.
قاعدة نزاهة إلزامية: لا يجوز وصف اكتشاف من Replay تاريخي بأنه Prediction حقيقي صدر وقت الحدث. الصياغة الصحيحة: Current engine successfully detected the historical event under point-in-time replay.
## 8.1 Minimum Pre-Launch Accumulation Core - يبدأ الآن
1. Live Shadow Collection
2. Historical Backfill
3. Signal Registry
4. Prediction Ledger
5. Decision Ledger
6. Automated Outcome Evaluator
7. Data Provenance
8. Algorithm/Model Versioning
9. Historical Replay Engine
10. Market Event Library
11. Failure Registry
12. Evidence Store
## 8.2 خط الأنابيب السريع
Licensed Historical Data → Massive Backfill → Point-in-Time Replay Engine → Signal/Prediction/Decision Ledger → Automated Outcome Evaluator → Event Knowledge Base + Entity Graph → Model/Signal Validation.
وبالتوازي: Live Market → 24/7 Shadow Engine → Immutable Timestamped Forward Record. وبعد الإطلاق: Real Users → Usage/Commercial/Network/Institutional Data.
# 9. Trust, Evidence, Security & Reliability Compounding
# 10. Product, Growth & Distribution Compounding by Design
# 11. Strategic Optionality & Platform Monetization
يجب ألا تُحصر الأصول الأساسية في نموذج إيراد واحد. نفس Intelligence Core يجب أن يكون قابلًا لإعادة الاستخدام - حسب الحقوق والمنتج - في Retail SaaS، Professional SaaS، Institutional API، Data Licensing، Research Products، Widgets، Developer API، Enterprise Feeds، وMachine-Readable intelligence للـAI agents/trading terminals/bots/third-party applications.
# 12. BLACKDARK Proprietary Asset Graph
المخطط المرجعي الذي يجب أن يربط الأصول بدل أن تعيش كجزر منفصلة:
Raw Data → Derived Data → Entity → Event → Feature → Signal → Prediction → Decision → Confidence → User Exposure → Outcome → Error → Learning → Model Version → Improvement → Commercial Impact.
يجب أن تسمح هذه السلسلة مستقبلًا بالإجابة القابلة للقياس عن: أي الإشارات الخاصة أدت إلى أفضل قرارات؟ ما مصادرها؟ ما دقتها التاريخية؟ في أي regimes؟ ما أثرها على retention/subscription؟ وما حقوق استخدام البيانات/IP التي بُنيت عليها؟
# 13. مصفوفة التوقيت والتنفيذ
# 14. ترتيب التنفيذ المقترح للاستشاري
1. إكمال الأعمال الجارية الحالية دون قطعها بهذا المسار.
2. عمل Audit فقط للمشروع الحالي لتحديد ما الموجود بالفعل من Signal/Outcome/Data/Evidence/Platform infrastructure وما الذي يضيع بعد الحساب.
3. إنتاج Gap Matrix مقابل هذه المواصفة، دون بناء قبل معرفة الموجود.
4. اعتماد Target Architecture لـAsset Accumulation + Platform boundaries + Data rights/privacy/governance.
5. تنفيذ Minimum Pre-Launch Accumulation Core.
6. تشغيل Live Shadow Collection وForward Track Record فورًا بمجرد سلامة المحركات الأساسية.
7. بدء Backfill/Replay/Event Reconstruction بالتوازي مع Product work دون تعطيل مسار الإطلاق.
8. إقامة registries: Truth/Claims/Capability/Model/Experiment/IP/Data Rights/SBOM/Evidence.
9. بناء Evidence Room حي يتحدث آليًا بدل جمع الأدلة قبل الاستحواذ.
10. إعادة مراجعة مؤسسية قبل الإطلاق عبر GATE - PROPRIETARY ASSET ACCUMULATION & DATA FLYWHEEL READINESS.
# 15. بوابة الإغلاق المؤسسي الإلزامية
GATE - PROPRIETARY ASSET ACCUMULATION & DATA FLYWHEEL READINESS
PASS لا يعني وجود Database. PASS يعني أنه من أول يوم Production يمكن تتبع كل حدث ذي قيمة من: Source Data → Processing/Normalization → Feature → Signal → Prediction/Decision → Version → Outcome → Evidence، مع جودة/Freshness/حقوق استخدام/خصوصية/احتفاظ/وصول واضحة، ومع فصل تام بين Backtested وSimulated وShadow/Forward وProduction Verified evidence.
القرار النهائي للبوابة: VERIFIED COMPLETE أو NOT READY. لا يُسمح بـ"تقريبًا مكتمل" في العناصر الحرجة.
# 16. معايير قبول أعمال الاستشاري
عدم إنشاء أسماء/واجهات شكلية دون data contracts وimplementation/evidence فعلي.
عدم حذف أي Source Requirement بحجة التشابه؛ يمكن فقط ربطه بمتطلب موحّد مع بقاء traceability.
عدم خلط Backtest/Simulation/Shadow/Production evidence في التقارير أو التسويق.
عدم جمع بيانات بلا purpose/rights/governance.
عدم ربط Intelligence core مباشرة بالـHTML بحيث يمنع Web/Mobile/API/B2B reuse.
كل Claim مهم مرتبط بـEvidence قابلة لإعادة الاختبار وصلاحية زمنية/version scope.
كل Capability مهمة لها Capability DNA: Purpose → Data → Algorithm → Dependencies → Tests → Benchmark → Limitations → Owner/IP → Version → Evidence.
كل Dataset مهمة لها Genealogy وData Rights واضحة.
كل Model/Algorithm مهم له genealogy/benchmark/drift/failure history.
كل فشل مهم يدخل Failure Corpus ويولد regression protection عند الإمكان.
# 17. نتيجة المراجعة الخماسية - سجل التدقيق

# الملحق 1: النص المرجعي الكامل للتقرير 1 - محفوظ دون دمج
Control: lines=603 | nonblank=369 | chars=11612 | SHA-256=ac61fa4781bcbca9433e8dce34c4ad97b3567ced783de6d71146c4d9b9b52fff
هذا الملحق هو المرجع النصي الأعلى عند أي اختلاف بين الصياغة الاستشارية والنص المصدر.
لنموذج الكامل: 12 خزينة قيمة يجب أن يبنيها المشروع

بدل تخزين كل شيء عشوائيًا، أفكر في المشروع كأنه يبني 12 خزينة باستمرار:

#	خزينة القيمة	ما يتراكم فيها	تأثيرها
1	Data Vault	التاريخ السوقي والـon-chain والبيانات المشتقة	Moat بيانات
2	Intelligence Vault	Signals، relationships، events، proprietary metrics	ذكاء خاص
3	Decision & Outcome Vault	Predictions، Decisions، Outcomes، calibration	إثبات الأداء
4	Model Vault	Models، algorithms، versions، benchmarks	تطور التكنولوجيا
5	Failure Vault	الأخطاء والحالات الفاشلة وأسبابها	رفع الجودة
6	Evidence Vault	Tests، security، load، reliability، claims evidence	الثقة وDD
7	IP Vault	Algorithms، datasets، research، licenses، provenance	الملكية الفكرية
8	Product Vault	Experiments، UX decisions، feature economics	تحسين المنتج
9	Customer Vault	الاستخدام، retention، conversion، feedback	معرفة العميل
10	Distribution Vault	SEO، referrals، content، embeds، community	قوة التوزيع
11	Institutional Vault	APIs، integrations، SLA، enterprise knowledge	قيمة B2B
12	Corporate/DD Vault	ownership، contracts، decisions، documentation	قابلية الاستحواذ

لكن يوجد داخلها أشياء إضافية مهمة جدًا لم نركز عليها كفاية.

1. بناء «ذاكرة سوق» وليس مجرد Data Warehouse

بدل تخزين:

BTC = $X

نخزن حالة السوق الكاملة عند اللحظات المهمة:

Market State → Liquidity → OI → Funding → Whales → Order Book → Volatility → On-chain → Risk → Events

وبمرور الزمن تتكون Market State Library.

فتصبح قدرة BLACKDARK مستقبلًا ليست فقط تحليل السوق الحالي، وإنما:

السوق الحالي يشبه 317 حالة تاريخية سابقة بنسبة معينة، وماذا حدث بعدها؟

هذه أقوى كثيرًا من مجرد Historical Charts.

2. Counterfactual Intelligence

إضافة مهمة لم نذكرها بهذا الوضوح.

عندما يقول النظام:

WAIT

لا نسجل فقط هل WAIT نجحت.

نحسب أيضًا:

ماذا كان سيحدث لو اختار BUY؟
ماذا لو SELL؟
ماذا لو انتظر ساعة؟
ماذا لو Threshold كان مختلفًا؟

وهكذا تتكون قاعدة:

Decision → Outcome + Alternative Outcomes

وده يساعد جدًا في تحسين Decision Engine.

3. Opportunity-Missed Ledger

ليس المهم فقط تسجيل الأخطاء.

نسجل أيضًا:

الفرص التي حدثت ولم يكتشفها BLACKDARK.

مثلاً حدث Squeeze مهم والنظام لم يصدر Signal.

هذه تدخل:

Missed Opportunity → Why missed → Required data/features → Fix → Regression case

دي مهمة جدًا لأن تقييم النظام بناءً على الإشارات التي أصدرها فقط قد يخفي نقاط ضعف ضخمة.

4. Hard-Case Library

نبحث باستمرار عن الحالات التي يحتار فيها النظام:

Sources متعارضة.
Confidence منخفض.
Models مختلفة الرأي.
أحداث غير معتادة.
Data ناقصة.
تغير Market Regime.

ونحفظها في:

BLACKDARK Hard Cases Dataset

هذه الحالات تحديدًا ممتازة لتطوير الجيل التالي من المحركات.

5. Uncertainty Intelligence

لا نخزن فقط:

Prediction = X.

نخزن:

لماذا النظام غير متأكد؟

Data uncertainty
Model uncertainty
Source disagreement
Regime uncertainty
Novel-event uncertainty.

وبمرور الوقت يتعلم النظام متى لا يعرف.

في Financial Intelligence، دي قيمة كبيرة جدًا.

6. Data Disagreement Corpus

إذا قالت 5 مصادر أشياء مختلفة، لا نرمِ الاختلاف بعد اختيار مصدر.

نحفظه.

Source A = X
Source B = Y
Source C = Z
Final consensus = ...

ثم نرى لاحقًا:

من كان الصحيح؟

بعد آلاف الحالات يمكن أن نبني Source Trust Intelligence حقيقية.

7. Intelligence Half-Life Database

كل Signal لها عمر.

قد تكون Whale Signal مفيدة 30 دقيقة، وأخرى ساعات.

نسجل:

Signal creation → peak usefulness → decay → expiry

ومع الوقت يعرف BLACKDARK:

متى تصبح المعلومة قديمة؟

وده يمكن أن يحسن Alerts وRanking وDecision Engine بصورة كبيرة.

8. Lead-Time Advantage History

نسجل:

قبل الحدث بكم دقيقة/ساعة اكتشفناه؟

ليس فقط:

هل توقعناه؟

مثلاً نظامان Accuracy متشابهة، لكن أحدهما يكتشف الخطر قبل الآخر بـ40 دقيقة.

هذه قيمة تجارية حقيقية إذا أثبتناها.

9. Intelligence Uniqueness Score

دي مهمة للـ600+ قدرة الموجودة في المشروع.

نقيس لكل Intelligence:

هل BLACKDARK أضاف معلومة جديدة فعلًا أم أعاد صياغة شيء موجود؟

مع الوقت نستطيع معرفة:

Commodity Intelligence مقابل Proprietary Intelligence.

ونركز التطوير على الثانية.

10. Capability Economic Ledger

لكل Capability نريد مستقبلًا سجلًا:

Development cost
Operating cost
Data cost
Compute cost
Usage
Retention impact
Conversion impact
Revenue attribution
Uniqueness
Accuracy/effectiveness

ثم نعرف:

Capability ROI

وبالتالي الـ600 قدرة لا تصبح عبئًا.

يمكن أن نكتشف أن 30 قدرة هي التي تنتج 80% من قيمة المنتج.

11. Capability Dependency Graph

نبني Graph:

CAP-100
يعتمد على:
Data X → Feature Y → Engine Z → API A → UI B.

لو Data X تعطلت نعرف فورًا:

أي قدرات أصبحت غير موثوقة؟

هذه مهمة جدًا للكفاءة والموثوقية والفحص المؤسسي.

12. Truth Registry

دي أراها مهمة جدًا لـBLACKDARK.

أي رقم يظهر للمستخدم يكون له تعريف مركزي.

مثلاً:

Net Edge
Confidence
Risk Score
Whale Score

لا يكون لدينا 4 صفحات تحسب نفس المفهوم بأربع طرق مختلفة.

ننشئ:

Metric/Truth Registry

Metric → canonical definition → formula → sources → version → owner → tests

وده يمنع تناقض المنتج داخليًا.

13. Claims Registry

كل Claim تسويقية:

Faster
More accurate
Detects X
Covers 100 exchanges
AI-powered...

ترتبط بـ:

Claim → Evidence → Test → Date → Version → Valid/Expired

لو Evidence انتهت صلاحيتها لا نسمح للمنتج بالاستمرار في ادعائها.

دي حماية ضخمة للثقة.

14. Reproducible Intelligence Receipts

لكل Insight مهمة نقدر إنتاج Receipt داخلي:

Insight ID
Timestamp
Data snapshot
Source
Algorithm version
Output
Confidence
Evidence hash
Outcome لاحقًا

وبالتالي بعد سنتين يمكن إعادة فحص لماذا صدر القرار.

15. Golden Benchmark Suite

بدل أن نختبر Algorithms باختبارات مختلفة كل مرة، نبني Benchmark ثابتًا ومتناميًا.

يحتوي:

Normal markets
Bull
Bear
Crash
Squeeze
Depeg
Manipulation-like cases
Bad data
Outages
Extreme volatility.

أي Engine جديد يجب أن يهزم أو يساوي الـBaseline قبل Production.

وبمرور السنوات يصبح Benchmark نفسه أصلًا معرفيًا ثمينًا.

16. Adversarial Market Laboratory

طبقة أعلى من الاختبارات.

نحاول عمدًا خداع النظام:

Fake volume-like patterns
Spoofing-like data patterns
Data corruption
Extreme latency
Contradictory exchanges
Whale noise
Sudden liquidity disappearance.

كل حالة تكشف ضعفًا تدخل المكتبة.

وبالتالي النظام يصبح أقوى كلما حاولنا كسره.

17. Shadow Challenger System

بدل Model واحدة فقط:

Champion Model تعمل Production.

وفي الخلفية:

Challenger Models

تعمل على نفس البيانات بدون التأثير على المستخدم.

وبعد آلاف الحالات:

Challenger B أفضل فعلًا من Champion؟

إذا ثبت ذلك فقط تتم ترقيتها.

هذه طريقة ممتازة لتحسين النظام دون المخاطرة بالمستخدم.

18. Automated Drift Memory

نراقب هل العلاقات التي تعلمناها بدأت تتغير.

مثلاً Signal كانت ممتازة في 2026، ثم بدأت تفقد فعاليتها.

نسجل:

Performance over time → degradation → regime → cause

فتصبح لدينا ذاكرة تطور السوق نفسه.

19. Human Override Ledger مستقبلًا

لو محلل مؤسسي أو مستخدم محترف رفض Recommendation، وبموافقة مناسبة على استخدام هذه البيانات:

AI said X → Expert chose Y → Outcome Z

مع كمية كافية من البيانات يمكن دراسة:

متى يتفوق الإنسان؟
ومتى يتفوق النظام؟
ومتى يكون الجمع بينهما أفضل؟

دي Dataset محتملة ذات قيمة عالية.

20. User Question Corpus

بعد الإطلاق، نحفظ بصورة آمنة ومناسبة أنماط الأسئلة والاحتياجات، وليس بالضرورة النصوص الحساسة الخام.

مثلاً آلاف المستخدمين يسألون:

لماذا انخفض ETH؟

هذا يكشف Demand على Intelligence معينة.

فتصبح Roadmap مبنية على الأسئلة الحقيقية للسوق.

21. Unmet Demand Ledger

كل شيء يبحث عنه المستخدم ولا يجده:

Search with zero result
Feature request
Unsupported asset
Unsupported exchange
Missing analysis.

يتحول إلى:

Demand Dataset

بدل تخمين ماذا نبني بعد ذلك.

22. Institutional Requirement Corpus

كل صندوق يسأل:

هل عندكم X؟

حتى لو لم يشترِ.

نسجل المتطلبات بشكل منظم.

بعد مقابلات كثيرة نعرف:

ما الذي تطلبه المؤسسات فعليًا بدل افتراض ما تحتاجه.

23. Lost Customer Intelligence

المستخدم الذي لم يشترك مهم مثل الذي اشترك.

نسجل بصورة مناسبة:

Visited → activated? → trial? → paid? → left? → reason

وكذلك B2B:

Lead → Demo → Objection → Lost reason

بعد فترة نمتلك Objection Database ضخمة تساعد Product + Sales.

24. Pricing Intelligence

ليس مجرد السعر الحالي.

نحفظ تاريخ:

Price
Conversion
Segment
Country/region where appropriate
Plan
Retention
Upgrade
Downgrade.

وبمرور الزمن نعرف Willingness-to-pay أفضل.

25. Distribution Knowledge Graph

مش مجرد Google Analytics.

نريد مستقبلًا فهم:

Creator → Content → Community → Visitor → User → Subscriber → Referral

وبالتالي نعرف كيف تنتشر BLACKDARK فعليًا.

وده مهم جدًا لخطة الانتشار التي تريدها.

26. Viral Content Genome

كل Card/Chart/Insight خرج من BLACKDARK:

موضوعه
شكله
نوع الحدث
وقت النشر
CTR
Shares
Signups
Paid conversions.

بعد آلاف القطع نبدأ نفهم:

أي نوع Intelligence ينتشر ولماذا؟

فتتحول Viral Marketing نفسها من تخمين إلى Data Science.

27. SEO Intelligence Corpus

نحفظ تاريخ:

Queries
Rankings
CTR
Pages
Backlinks
Conversions
Search intent.

بعد سنوات يصبح لدينا Search Demand Map لسوق Crypto Intelligence.

28. Integration Graph

كل نظام يعتمد على BLACKDARK:

Customer → API → endpoints → workflows → usage

مع الوقت نعرف مدى تغلغل المنتج في Ecosystem.

ده مفيد جدًا لتقييم Switching Costs.

29. Revenue Quality Dataset

المستحوذ لن يهتم فقط بـMRR.

نحتاج تاريخًا يستطيع إثبات:

Recurring revenue
Retention
Expansion
Concentration
Gross margin
Cohort durability
Refunds
Failed payments.

$1M ARR عالي الجودة ≠ $1M ARR ضعيف الجودة.

30. Acquisition-Ready Data Room حي

وأريد تغيير مفهوم الـData Room نفسه.

لا يكون Folder نعمله عندما يظهر مشتري.

يكون:

Living Due-Diligence System

يتحدث باستمرار:

Architecture
IP
Security
Tests
Data rights
Models
Performance
Customers
Financials
Incidents
Contracts
Risks
Compliance evidence.

وبالتالي لو ظهر مستحوذ فجأة، المشروع لا يبدأ تجهيز نفسه للبيع؛ هو كان قابلًا للفحص طوال الوقت.

وهناك شيء أهم من «ماذا نخزن؟»
ماذا لا نخزن؟

دي علامة النضج المؤسسي.

لا نخزن كل شيء لمجرد أنه ممكن.

أي Data تمر على:

Does it create value?
↓
Do we have the right to collect/use it?
↓
Is it necessary?
↓
How long is it needed?
↓
How is it secured?
↓
Who can access it?
↓
When is it deleted/anonymized?

لأن Dataset ضخمة بلا حقوق واضحة أو مليئة ببيانات شخصية غير لازمة قد تقلل قيمة الشركة بدل رفعها.

الخلاصة التي وصلت إليها

بعد كل ما ناقشناه، أنا لا أريد أن نبني مجرد:

BLACKDARK Data Collection System

بل منظومة أكبر:

BLACKDARK COMPOUNDING VALUE ARCHITECTURE

وتتكون من 8 محركات تراكم رئيسية:

1 — DATA COMPOUNDING
السوق والتاريخ والـKnowledge Graph.

2 — INTELLIGENCE COMPOUNDING
Signals + relationships + proprietary metrics + market memory.

3 — LEARNING COMPOUNDING
Predictions + decisions + outcomes + failures + counterfactuals + missed opportunities.

4 — TECHNOLOGY COMPOUNDING
Models + algorithms + benchmarks + experiments + hard cases + drift.

5 — TRUST COMPOUNDING
Forward track record + security + reliability + reproducible evidence.

6 — PRODUCT & CUSTOMER COMPOUNDING
Usage + demand + retention + economics + institutional requirements.

7 — DISTRIBUTION COMPOUNDING
SEO + viral objects + referrals + creators + embeds + API ecosystem.

8 — CORPORATE VALUE COMPOUNDING
IP + data rights + documentation + revenue quality + DD evidence.

والأقوى أن هذه الثمانية تغذي بعضها:

More operation → more evidence → more knowledge → better intelligence → better product → more users → more outcomes → stronger distribution → more revenue → more institutional adoption → stronger moat → higher strategic value.

توصية مهمة الآن

قبل أن نضيف أي شيء فعليًا إلى Cursor، أرى أننا وصلنا لمرحلة تستحق تجميع كل ما ناقشناه منذ بداية موضوع التراكم والـMoat وحتى الآن في Master Specification واحدة بدون تكرار، ثم نعمل Gap Audit مقابل المشروع الحالي.

لأن عندنا الآن عشرات الأفكار الممتازة، والخطر أصبح العكس: أن تضيع أو تتكرر أو يتحول تنفيذها إلى فوضى.

هذه الـMaster Specification ستكون المرجع الذي يحدد بصرامة:

BUILD NOW / START ACCUMULATING NOW / DESIGN NOW-BUILD LATER / REQUIRES USERS / REQUIRES SCALE / DO NOT BUILD.

وده في رأيي الخطوة الصحيحة التالية قبل كتابة سطر كود إضافي في هذا المسار.

# الملحق 2: النص المرجعي الكامل للتقرير 2 - محفوظ دون دمج
Control: lines=477 | nonblank=299 | chars=10278 | SHA-256=898885e29f921a55f34c0817c1b6759b0b0fcd76e54fd4f0503fbc308725cf09
هذا الملحق هو المرجع النصي الأعلى عند أي اختلاف بين الصياغة الاستشارية والنص المصدر.
نعم. وفي رأيي جمع البيانات مجرد أصل واحد من مجموعة أصول يجب أن نبدأ صناعتها قبل الإطلاق.

لو كنت أراجع BLACKDARK كرئيس لجنة Product + Engineering + Data + AI + Security + Acquisition، فسأضيف الآن برنامجًا موازيًا للتطوير اسمه:

BLACKDARK Pre-Launch Value Compounding Program

فكرته: أي شيء يحتاج الزمن لكي يصبح ذا قيمة، نبدأ ساعته من الآن بدل يوم الإطلاق.

وأهم ما أبدأه، بالترتيب:

الأولوية	الأصل الذي نبدأ تكوينه الآن	لماذا يرفع القيمة؟	هل يبدأ الآن؟
1	Forward Track Record	تاريخ حي لا يمكن اختلاقه لاحقًا	🔴 فورًا
2	Historical Data + Replay Corpus	ذاكرة سوق واختبارات واسعة	🔴 فورًا
3	Signal/Decision/Outcome Ledger	يثبت ماذا عرف النظام وماذا حدث	🔴 فورًا
4	Proprietary Derived Dataset	أصعب في النسخ من Raw Data	🔴 فورًا
5	Market Event Knowledge Base	ذاكرة الأزمات والحالات النادرة	🔴 فورًا
6	Financial Entity/Knowledge Graph	شبكة علاقات مالية تتعمق مع الزمن	🔴 فورًا
7	Failure Intelligence Library	كل خطأ يجعل النظام أنضج	🔴 فورًا
8	Model/Algorithm Evolution History	يثبت التحسن الحقيقي	🔴 فورًا
9	Benchmark & Evidence History	يبني مصداقية DD مستقبلية	🔴 فورًا
10	Security/Threat Intelligence	دفاع خاص مبني على تاريخ المشروع	🔴 فورًا
11	Reliability/SRE Track Record	تاريخ uptime/latency/failures حقيقي	🔴 فورًا
12	Research/IP Corpus	يحول الاكتشافات إلى ملكية معرفية	🔴 فورًا
13	Experiment Knowledge Base	يمنع تكرار الأخطاء ويثبت القرارات	🔴 فورًا
14	Public Research/Authority Engine	يبدأ بناء السمعة قبل الإطلاق	🟠 قريبًا
15	SEO/Domain Authority	يحتاج شهورًا، لذلك التأخير مكلف	🟠 قريبًا
16	Developer/API Ecosystem	يجعل المنتج بنية تحتية لا موقعًا فقط	🟠 نصممه الآن
17	Integration Ecosystem	يزيد Switching Costs والتوزيع	🟠 نصممه الآن
18	Community/Waitlist Graph	أول Network Asset قبل المستخدمين	🟠 قبل الإطلاق
19	Trust/Transparency Infrastructure	الثقة نفسها تتراكم	🟠 نصممه الآن
20	Acquisition Evidence Room	يحول كل ما سبق إلى أصل قابل للفحص	🔴 من الآن

لكن توجد نقاط داخلها أعتبرها شديدة الأهمية وتستحق شرحًا منفصلًا.

1. Forward Track Record — أبدأه قبل أي شيء

دي ربما أهم إضافة بعد حديثنا السابق.

نشغل أهم محركات BLACKDARK على السوق الحقيقي Shadow Mode 24/7.

كل Prediction/Signal:

Timestamp → Inputs → Engine Version → Prediction → Confidence → Horizon

وبعدها نسجل:

Actual Outcome

وبالتالي إذا استغرق الإطلاق 90 يومًا، نصل إلى الإطلاق ومعنا 90 يومًا من Forward Evidence بدل صفر.

والـForward Evidence أقوى من Backtest لأنه صدر قبل معرفة المستقبل.

2. Immutable Evidence Ledger

لا يكفي Database يمكن تعديلها لاحقًا.

للتوقعات المهمة نحتاج Evidence Architecture تجعلنا قادرين مستقبلًا على إثبات:

هذا ما قاله BLACKDARK فعلًا في الساعة X قبل وقوع الحدث.

Timestamp + version + hashes/append-only audit controls المناسبة.

ليس المقصود Blockchain لمجرد استخدام Blockchain؛ المقصود Tamper-evident evidence.

هذا قد يصبح مهمًا جدًا في التسويق والثقة وDue Diligence.

3. Golden Market Event Library

لا أريد مجرد ملايين Rows.

نختار مئات/آلاف الحالات المهمة تاريخيًا:

Terra/LUNA
FTX
USDC depeg
ETF-related volatility
major liquidation cascades
exchange outages
flash crashes
major squeezes
extreme funding events
whale events
network congestion
protocol failures

ثم نحتفظ بحالة السوق:

قبل الحدث → أثناءه → بعده.

وكلما حدث شيء جديد في المستقبل يدخل المكتبة.

بعد سنوات يصبح لدينا مختبر أزمات مالي خاص بـBLACKDARK.

4. Proprietary Derived Metrics Registry

دي نقطة مهمة جدًا للـMoat.

لا أريد أن تكون قيمة المشروع:

Binance أعطتنا Data وعرضناها بشكل أجمل.

نريد أن يبدأ النظام في إنتاج أشياء BLACKDARK هي التي تحسبها.

مثل Scores/Indices/relationships/behavioral classifications الخاصة بالمشروع.

لكل Derived Metric:

Definition
Inputs
Formula/model
Version
Validation
Performance history
IP ownership

مع الوقت قد تصبح بعض هذه المقاييس نفسها منتجات Data قابلة للبيع عبر API.

5. Financial Knowledge Graph

بدل أن نحتفظ بـ:

Wallet A
Wallet B
Token C
Exchange D

كصفوف منفصلة فقط، نبدأ تصميم Graph:

Wallet ↔ Wallet
Wallet ↔ Exchange
Wallet ↔ Protocol
Wallet ↔ Token
Entity ↔ Event
Entity ↔ Behavior

وتزداد جودة العلاقات والتصنيفات بمرور الزمن.

بعد فترة يمكن أن يصبح لدينا خريطة مالية معرفية خاصة بالمشروع.

6. Failure Corpus

وده شيء الشركات الصغيرة غالبًا ترميه.

كل مرة BLACKDARK يخطئ:

لا نمسح الخطأ ونصلحه فقط.

نسجل:

Failure → Conditions → Root Cause → Impact → Fix → Regression Test → Recurrence

وبعد سنوات سيكون عندنا Dataset عن:

كيف يفشل النظام وكيف تمنع حالات الفشل.

وده أصل هندسي مهم.

7. Model & Algorithm Genealogy

أريد لكل محرك شجرة نسب.

مثلًا:

Whale Engine v1
↓
v2
↓
v3
↓
v4

ومع كل Version:

ما الذي تغير؟

لماذا؟

ما Benchmark قبل؟

ما Benchmark بعد؟

هل التحسن حقيقي؟

في أي Market Regime؟

وبالتالي لا يستطيع أحد تعديل Algorithm ثم يقول:

أصبحت أفضل.

لازم يثبت أنها أصبحت أفضل.

8. Competitive Intelligence Memory

دي مختلفة عن مقارنة المنافسين مرة واحدة.

نبني قاعدة تاريخية:

Competitor → Feature → Price → Positioning → Data → UX → API → Change over time.

كل فترة Snapshot.

بعد سنة نعرف:

ماذا يفعل السوق؟
من رفع الأسعار؟
من ألغى Feature؟
أين يتحرك المنافسون؟
وأين توجد فجوة لم يملأها أحد؟

دي تصبح ذاكرة استراتيجية للشركة.

9. Experiment Registry

كل تجربة نعملها:

Feature
Algorithm
UI
Pricing
Onboarding
Alert
Landing page
Growth mechanism

نسجل:

Hypothesis → Experiment → Result → Decision.

حتى التجربة الفاشلة لا تضيع.

بعد سنوات الشركة تمتلك ذاكرة قرارات.

10. Research/IP Factory

كلما اكتشفنا علاقة جديدة في السوق لا تبقى داخل محادثة أو Notebook.

تمر عبر Pipeline:

Discovery → Reproduction → Validation → Documentation → IP Classification → Production Candidate.

ثم نصنفها:

Trade Secret
Algorithm
Dataset
Metric
Research finding
Potential patent candidate إن كان يستحق قانونيًا.

وبالتالي BLACKDARK يبدأ إنتاج IP باستمرار وليس Features فقط.

11. Reliability Track Record

من أول تشغيل حقيقي نسجل:

Uptime
Latency p50/p95/p99
Data freshness
Error rates
Recovery time
Incidents
Capacity
Provider failures.

بعد سنتين تستطيع مؤسسة أن ترى:

24 months operational history.

دي أقوى بكثير من كتابة:

Enterprise Grade.

12. Security Track Record

كذلك من الآن:

Vulnerabilities discovered
Time-to-remediation
Dependency incidents
Attack/abuse attempts
Security tests
Pentests
Secrets rotations
Access reviews
Security releases.

وبالتالي يتكون Security maturity history.

13. Evidence Room من الآن وليس قبل البيع

دي من أهم توصياتي.

غلط نقرر بيع المشروع وبعدها نقول:

يلا نجمع الأدلة.

من الآن كل Evidence تدخل تلقائيًا في نظام منظم:

Architecture Evidence
Data Evidence
Algorithm Evidence
Security Evidence
Performance Evidence
Reliability Evidence
Model Evidence
IP Evidence
Commercial Evidence لاحقًا.

فتصبح Due Diligence Room نتاج سنوات التشغيل وليست PDF كتبناها قبل الاستحواذ.

14. SEO Authority يبدأ قبل الإطلاق

دي ليست برمجة فقط، لكنها من الأشياء التي الزمن يرفع قيمتها.

Domain history، صفحات Research حقيقية، أدوات مجانية قابلة للفهرسة، backlinks طبيعية، citations، branded search.

لا أريد انتظار Launch Day ثم نبدأ SEO.

الـDomain Authority والـsearch footprint يحتاجان وقتًا.

15. Public Intelligence Reputation

يمكن قبل الإطلاق الكامل نشر جزء مجاني من Intelligence:

Market reports
Research
Indices
Live market pages
Charts
Embeddable widgets.

الهدف أن يبدأ الإنترنت يعرف:

BLACKDARK = مصدر Intelligence

قبل أن نقول:

BLACKDARK launched.

وبالتالي الإطلاق يكون انفجارًا لشيء بدأ الناس يلاحظونه، وليس ظهور اسم مجهول في صباح واحد.

16. API-First Architecture

دي تتضاف في التصميم المعماري الآن.

أي Intelligence مهمة لا أحب أن تكون مربوطة بالـDashboard فقط.

تكون:

Intelligence Engine → Internal API/service contract → Web → Mobile → Institutional API → Widget

وبالتالي نفس الأصل يمكن بيعه واستخدامه في 5 أماكن.

ده يرفع القيمة جدًا مقارنة بمشروع قدراته محبوسة داخل HTML.

17. Machine-Readable Product

أذهب أبعد من API.

نصمم Intelligence بحيث يمكن مستقبلًا أن يستخدمها:

AI agents
Trading terminals
Bots
Institutional systems
Developers
Third-party apps.

أي أننا لا نبني BLACKDARK للبشر فقط.

نبنيه ليصبح مصدر Intelligence للبرمجيات الأخرى أيضًا.

وده يمكن أن يفتح Distribution مختلفًا تمامًا مستقبلًا.

18. Trust Architecture داخل التصميم

في الـUI نفسه من البداية أماكن لـ:

Why this insight?
Data freshness
Confidence
Evidence
Historical performance
Limitations
Source quality

بدل إضافة Trust بعد سنة.

وده يحل أيضًا المشكلة التي ناقشناها سابقًا: لا نريد ادعاءات أكبر من الأدلة.

19. Shareability Architecture

برضه تتصمم الآن.

أي Insight قوي يكون له:

Share Card
Permanent URL
Timestamp
BLACKDARK branding
Evidence link
Embeddable version

فتتحول البيانات المتراكمة إلى Distribution Asset أيضًا.

مثلاً اكتشاف Market Event قوي لا يموت داخل Dashboard؛ يمكن أن ينتشر خارجه.

وده سيرتبط مباشرة بخطة الإطلاق الفيروسي لاحقًا.

20. Optionality Architecture

ودي نقطة Acquisition مهمة جدًا.

لا نصمم BLACKDARK بحيث له Business Model واحد فقط.

الأصول نفسها يمكن استخدامها في:

Retail SaaS
Professional SaaS
Institutional API
Data licensing
Research products
Widgets
Developer API
Enterprise feeds.

كلما كانت الأصول الأساسية قابلة لإعادة الاستخدام، زادت Strategic Optionality للمشروع والمستحوذ.

لو سألتني: ما أخطر 10 أشياء نبدأها الآن تحديدًا؟

لن أبدأ 20 مشروعًا عشوائيًا.

سأبدأ بهذا الترتيب:

① Live Forward Shadow Track Record

② Historical Backfill + Point-in-Time Replay

③ Signal → Prediction → Decision → Outcome Ledger

④ Proprietary Derived Intelligence Store

⑤ Golden Market Event Library

⑥ Financial Entity/Knowledge Graph

⑦ Model/Algorithm Version + Experiment Registry

⑧ Failure + Security + Reliability History

⑨ Automatic Evidence/Due-Diligence Repository

⑩ Research/IP Registry

ثم أثناء تصميم الواجهة والهندسة الحالية نضمن من البداية:

API-first + Evidence-first + Shareability + Trust UI + Data lineage + Privacy + Versioning.

والأهم من كل ذلك

أنا لا أريد أن نحول BLACKDARK الآن إلى مشروع Data Engineering لمدة سنة وننسى المنتج.

الأذكى أن يكون هناك مساران يعملان بالتوازي:

المسار A — Product:
نكمل التصميم والقدرات والاختبارات وجاهزية الإطلاق.

المسار B — Compounding Assets:
الآلة تعمل في الخلفية 24/7 وتبدأ بناء التاريخ والـEvidence والـIP والـKnowledge.

كل يوم نعمل فيه على المنتج، المسار الثاني يزداد قيمة بدل أن تكون فترة التطوير وقتًا ميتًا.

ولو بقي أمام الإطلاق 60 أو 90 أو 120 يومًا، فبدل أن نصل للإطلاق ومعنا مجرد منتج جاهز، نصل ومعنا:

منتج جاهز + تاريخ حي + Backtests + Event Library + Derived Dataset + Knowledge Graph + Track Record + IP Registry + Reliability/Security Evidence + Due-Diligence history.

دي بالنسبة لي نقلة استراتيجية أهم بكثير من إضافة عشرات Features جديدة الآن.

# الملحق 3: النص المرجعي الكامل للتقرير 3 - محفوظ دون دمج
Control: lines=176 | nonblank=92 | chars=8521 | SHA-256=30a466ef0d20f7ad88e37be68534ad87803b45d6827cdc0af3f6bf91e4895564
هذا الملحق هو المرجع النصي الأعلى عند أي اختلاف بين الصياغة الاستشارية والنص المصدر.
1. تصميم المنتج كـ Platform وليس Website فقط

نفصل قدرات BLACKDARK الأساسية عن صفحات الموقع. أي Engine مهم يجب أن يستطيع مستقبلًا خدمة Web، Mobile، API، Widgets، B2B وأنظمة أخرى. هذا يجعل الأصل التقني نفسه قابلًا لإعادة البيع والتوزيع بأكثر من شكل بدل أن يكون محبوسًا داخل Dashboard.

2. تصميم Multi-Tenant Institutional Architecture من البداية

حتى لو المؤسسات قليلة عند الإطلاق، نجهز المفاهيم الأساسية لـOrganizations، Teams، Roles، RBAC، API credentials، usage metering، audit logs، entitlements وعزل بيانات العملاء. لأن تحويل منتج Retail بعد النجاح إلى Enterprise قد يتطلب إعادة هندسة مؤلمة جدًا.

3. بناء Entitlement Engine حقيقي

بدل أن تكون FREE/PRO/ELITE/QUANT مجرد if plan == pro موزعة في الكود، تصبح كل Capability لها entitlement وسياسات usage واضحة. وقتها نستطيع تغيير الأسعار، إنشاء Enterprise contracts، Trials، Bundles أو API packages بدون إعادة بناء المنتج.

4. تصميم Metering لكل أصل قابل للبيع

من الآن نستطيع قياس: API calls، intelligence requests، signals، alerts، data consumption، compute-heavy analysis وغيرها. ليس بالضرورة لتحصيل المال الآن، بل حتى نعرف مستقبلًا ما الذي يستهلكه العميل وما تكلفته وما قيمته.

5. Unit Economics Telemetry

أريد أن نعرف مستقبلًا ليس فقط أن العميل يدفع $49، بل مثلًا: هذا النوع من العملاء يستهلك Compute/Data/AI/API بتكلفة X ويحقق Gross Margin Y. ده مهم جدًا عند التوسع والاستحواذ.

6. Cost Attribution Architecture

كل Engine/Data provider/AI operation له تكلفة يمكن تتبعها. بعد مئات الآلاف من المستخدمين، نعرف بالضبط أين تحترق الأموال بدل اكتشاف أن Feature مجانية تكلفنا أكثر مما تحققه من قيمة.

7. Feature-Level Economics

نربط مستقبلًا:

Feature → Usage → Retention → Conversion → Revenue → Infrastructure Cost

وبالتالي نستطيع اكتشاف أن Capability معينة تكلف كثيرًا ولا يحتفظ بها أحد، بينما أخرى صغيرة هي التي تحول المستخدمين إلى PRO.

دي معرفة منتجية ثمينة جدًا.

8. Experimentation Platform

بدل تعديل المنتج لكل المستخدمين، نصمم Feature Flags وExperiments وCohorts. نستطيع تجربة onboarding أو pricing presentation أو algorithm جديد على نسبة محدودة، قياس النتيجة، ثم اتخاذ القرار.

وهكذا تبدأ الشركة بتكوين ذاكرة تجريبية من قبل الإطلاق الكامل.

9. Reproducibility Architecture

أي نتيجة مهمة يصدرها BLACKDARK يجب أن نستطيع مستقبلًا إعادة إنتاجها: أي Data؟ أي Version؟ أي configuration؟ أي timestamp؟ أي algorithm/model؟ هذا مهم للـAI والمال وDue Diligence.

10. Provenance لكل Intelligence

ليس فقط Data lineage. حتى النتيجة نفسها يكون لها نسب:

Sources → transformations → features → engines → signal → decision

وبالتالي زر Why? في الواجهة يمكن أن يكون مدعومًا بحقيقة هندسية، وليس شرحًا مولدًا بعد النتيجة.

11. Confidence Architecture موحدة

بدل أن كل Engine يخترع Confidence بطريقته، نضع Framework موحدًا: Model confidence، Data confidence، Signal agreement، Historical reliability، Uncertainty. وبمرور الوقت يمكن Calibration لهذه الدرجات مقابل النتائج الفعلية.

12. Time-to-Value Instrumentation

من أول مستخدم نعرف:

Signup → أول لحظة فهم فيها قيمة BLACKDARK

هل استغرقت 20 ثانية؟ 4 دقائق؟ لم يصل إليها أصلًا؟

دي من أهم البيانات التي سنحتاجها لخطة النمو.

13. Activation Definition

نحدد قبل الإطلاق ماذا يعني Activated User فعلًا. ليس مجرد Registered. مثلًا شاهد Insight ذا قيمة + حفظ Asset + فعل Alert، أو تعريف آخر تثبته التجارب. وإلا سنحتفل بأعداد Accounts ليس لها قيمة.

14. Retention Architecture

نصمم المنتج ليكون له سبب حقيقي للعودة: Watchlists، personalized intelligence، alerts، market changes، saved workspaces، historical comparisons. ليس Gamification فارغًا؛ قيمة جديدة تتجدد مع تغير السوق.

15. Viral Object Architecture

دي شديدة الأهمية لخطة الإطلاق المستقبلية. لا نصمم Sharing في النهاية. نصمم من الآن أشياء داخل BLACKDARK مولودة لكي تخرج من BLACKDARK: Signal Cards، Risk Cards، Whale Events، Market Maps، Prediction receipts، charts، public reports، widgets.

كل واحد له permanent URL + timestamp + branding + evidence + share metadata.

16. Attribution Architecture

لو انتشرت Card وجلبت 40,000 شخص، نريد أن نعرف ذلك. لذلك من البداية:

Content/Creator/Referral/Widget → Visitor → Signup → Activation → Paid → Retention

وإلا قد يحدث Viral Growth ولا نعرف ما الذي سببه.

17. Referral Graph وليس Referral Code فقط

نصمم إمكانية معرفة شجرة التوزيع بصورة تحترم الخصوصية: من أحضر من؟ أي communities تنشر؟ أي users أصبحوا super-spreaders؟ أي Intelligence object انتشر أكثر؟

هذا يمكن أن يصبح Distribution Intelligence خاصة بالمشروع.

18. Public/Private Intelligence Boundary

من البداية نصنف المعلومات إلى: Public/shareable، Free، Premium، Institutional، Sensitive/Internal. ده يسمح لنا مستقبلًا باستخدام جزء من Intelligence كآلة SEO/viral distribution بدون تسريب المنتج المدفوع.

19. Programmatic Public Intelligence Pages

نصمم Architecture تسمح لاحقًا بصفحات مفيدة حقيقية لكل Asset/Metric/Event حيث توجد قيمة فعلية، بدل آلاف صفحات SEO رديئة. مع الزمن يمكن أن يتكون Search footprint ضخم حول Intelligence الخاصة بالمنتج.

20. Embeddable BLACKDARK

نصمم بعض الأصول لتعيش على مواقع الآخرين: Widgets، charts، market pulse، risk indicators وغيرها. كل Embed يصبح نقطة توزيع خارجية للمشروع.

21. Developer Experience من البداية

API contracts مستقرة، versioning، SDK-ready architecture، webhooks/event streams، documentation generation وsandbox. إذا أصبح المنتج مشهورًا، المطور يستطيع البناء فوقه بدل انتظارنا.

22. Event-Driven Architecture للأحداث المهمة

بدل أن تكون المعلومات موجودة فقط عند فتح الصفحة، Market Event يمكن أن يولد Event داخليًا يستهلكه Alert، Mobile، API، Institution، Evidence system، analytics. ده يجعل التوسع في قنوات جديدة أسهل.

23. Portable Intelligence Objects

نصمم وحدة Intelligence نفسها ككيان مستقل يحتوي على asset، timestamp، evidence، confidence، provenance، expiry/freshness، entitlement. نفس الـInsight يمكن أن يظهر في Web أو Mobile أو Telegram أو API بدون إعادة اختراع المنطق.

24. Localization Architecture صحيحة

بما أن المنتج يستهدف سوقًا عالميًا، اللغة لا تكون نصوص HTML مترجمة يدويًا. نفصل content/formatting/timezones/currencies/RTL وغيرها عن المنطق الأساسي، حتى لا يتحول التوسع العالمي لاحقًا إلى إعادة بناء.

25. Privacy-by-Design

قبل وجود ملايين المستخدمين نحدد data minimization، consent، retention، deletion، export، purpose limitation، access controls وفصل telemetry عن البيانات الحساسة. إصلاح هذا بعد تراكم سنوات من البيانات أصعب بكثير.

26. Data Rights Registry

ودي مهمة جدًا للـMoat. لكل مصدر بيانات نعرف: هل يسمح بالتخزين؟ مدة الاحتفاظ؟ derived works؟ إعادة البيع؟ التدريب؟ API redistribution؟ لأن Dataset بمليارات السجلات قيمتها قد تصبح صفرًا للمستحوذ إذا لم نستطع إثبات حق استخدامها.

27. IP Provenance

لكل أصل مهم نعرف: من كتبه؟ مصدره؟ dependencies؟ license؟ هل هو proprietary فعلًا؟ هل يحتوي GPL/third-party restrictions؟ هل يعتمد على competitor wrapper؟ المستحوذ يريد معرفة أنه يشتري IP يمكنه امتلاكه قانونيًا.

28. SBOM + Dependency History

نسجل Software Bill of Materials وتطور dependencies. يفيد الأمن وDue Diligence ويمنع مفاجأة وجود dependency خطرة داخل قلب المنتج.

29. Vendor Independence

لا نجعل أصل BLACKDARK الأساسي مربوطًا بطريقة يستحيل فصلها عن Provider واحد. نضع abstraction في الأماكن الحرجة بحيث يمكن تغيير Data/Cloud/AI provider عندما يكون ذلك اقتصاديًا وهندسيًا منطقيًا.

ده يزيد Strategic Independence.

30. Exit/Acquisition Architecture

ودي قد تبدو غريبة لكنها مهمة لهدف المشروع. من الآن نفصل الملكية الفكرية، الوثائق، العقود، secrets، infrastructure، dependencies، licenses، architecture decisions والأدلة بطريقة تجعل المستحوذ يستطيع فهم ما سيشتريه ونقله وتشغيله.

لا نبني المشروع فقط لكي يعمل؛ نبنيه لكي يكون قابلًا للفحص والنقل والاستحواذ.

والآن لو أجمع كل حديثنا الأخير، فأنا أرى أن هناك 7 آلات يجب أن نزرعها داخل BLACKDARK أثناء التصميم:

① Intelligence Compounding Machine
Data → Signals → Decisions → Outcomes → Learning.

② Evidence Compounding Machine
كل يوم تشغيل → Track Record أقوى.

③ IP Compounding Machine
Research → Derived Metrics → Algorithms → Proprietary Assets.

④ Trust Compounding Machine
Performance + Security + Reliability + transparency → ثقة متراكمة.

⑤ Distribution Compounding Machine
Insights → Shares → Embeds → Search → Referrals → Audience.

⑥ Customer/Commercial Learning Machine
Usage → Activation → Retention → Conversion → Economics → Better Product.

⑦ Ecosystem Compounding Machine
API → Developers → Integrations → Institutions → Switching Costs → Network effects.

لو زرعنا السبعة الآن، كل شهر يمر قبل وبعد الإطلاق يمكن أن يجعل BLACKDARK أصلًا أقوى بدل أن يكون مجرد شهر إضافي من عمر الموقع.

وأنا تحديدًا سأضع هذه النقاط مع Data Flywheel + Moat + Evidence + Track Record داخل برنامج الفحص قبل الإطلاق الذي بنيناه سابقًا، وليس كأعمال جانبية. لأنها قد تؤثر على القيمة المستقبلية للمشروع أكثر من إضافة عشرات القدرات الجديدة

# الملحق 4: النص المرجعي الكامل للتقرير 4 - محفوظ دون دمج
Control: lines=1111 | nonblank=843 | chars=29064 | SHA-256=4b43ad8c8594d7367374902f0443ba2d2c2b704cfc009182fdc3f8b6a31126ba
هذا الملحق هو المرجع النصي الأعلى عند أي اختلاف بين الصياغة الاستشارية والنص المصدر.
الحصر الشامل للأصول التي تتكون بمرور الزمن
A — أصول البيانات السوقية Market Data Assets

هذه هي الذاكرة التاريخية للسوق التي يبنيها BLACKDARK:

Historical Market Data — الأسعار التاريخية.
Historical Trades — الصفقات المنفذة تاريخيًا.
Historical Order Books — حالات دفتر الأوامر عبر الزمن.
Order-Book Depth History — تاريخ عمق السيولة.
Bid/Ask Spread History.
Liquidity History.
Slippage History.
Volatility History.
Volume History.
OHLCV multi-timeframe history.
Cross-exchange price history.
Cross-exchange liquidity history.
Funding-rate history.
Open-interest history.
Basis history.
Liquidation history.
Long/Short positioning history.
Options/IV/Greeks history حيث تتوفر البيانات.
DEX liquidity/pool history.
Bridge-flow history.
Stablecoin-flow history.
Gas/fee/congestion history.
Exchange health/outage history.
Latency/freshness history لكل Data Source.

لكن تخزين هذه البيانات وحده ليس Moat قويًا إذا كان يستطيع المنافس شراء البيانات نفسها.

القيمة الأكبر تبدأ في الطبقات التالية.

B — البيانات المشتقة Proprietary Derived Data

BLACKDARK يأخذ البيانات الخام ويخلق منها بيانات خاصة به:

Normalized datasets.
Cleaned datasets.
Deduplicated datasets.
Time-aligned cross-source datasets.
Entity-enriched datasets.
Anomaly-labelled datasets.
Market-regime-labelled datasets.
Liquidity-condition labels.
Whale-behavior labels.
Manipulation-pattern labels.
Risk-event labels.
Liquidation-event labels.
Squeeze-event labels.
Depeg-event labels.
Correlation-break labels.
Exchange-stress labels.
Counterparty-risk observations.
Internal-exchange-flow classifications.
Sybil classifications.
Wallet-behavior classifications.
Smart-money classifications.
Signal-feature datasets.
Multi-source convergence datasets.
Event-before/event-after datasets.

هنا تبدأ BLACKDARK Dataset الخاصة فعلًا.

C — On-Chain Intelligence Memory
Historical wallet activity.
Wallet clusters.
Wallet-to-wallet relationships.
Wallet-to-exchange relationships.
Wallet-to-protocol relationships.
Entity attribution history.
Whale wallet histories.
Wallet-age histories.
Accumulation/distribution histories.
Dormant-wallet activation histories.
Exchange inflow/outflow histories.
Cross-chain wallet behavior.
Bridge behavior.
Token movement patterns.
Smart-money behavioral histories.
Contract/protocol interaction histories.
Suspicious-wallet observations.
Dusting/Sybil behavior histories.

وبمرور السنوات قد يتحول ذلك إلى:

BLACKDARK Financial Entity Graph

بدل مجرد Database من Addresses.

D — Market Event Knowledge Base

وهذه أراها شديدة القيمة.

كل حدث كبير يتم تحويله إلى Case تاريخية:

Crashes.
Pumps.
Flash crashes.
Short squeezes.
Long squeezes.
Liquidation cascades.
Depegs.
Exchange outages.
Hacks/exploits عندما تكون ذات صلة بالتحليل.
Whale accumulation events.
Whale distribution events.
Liquidity withdrawals.
Funding anomalies.
OI anomalies.
Correlation breakdowns.
Extreme volatility.
Market manipulation-like patterns.
Major macro/crypto events.
Network congestion.
Protocol failures.

ثم نسجل:

Before → During → After

لكل حدث.

بعد سنوات يصبح لدى النظام مكتبة حالات سوقية تاريخية يمكن مقارنة السوق الحالي بها.

E — Signal Registry

كل Signal أنتجها BLACKDARK منذ البداية:

Signal ID.
Timestamp.
Asset.
Signal type.
Input state.
Data sources.
Model/algorithm version.
Strength.
Confidence.
Expected horizon.
Supporting signals.
Contradicting signals.
Market regime.
Data quality.
Data freshness.
Subsequent outcome.

هذه تتحول إلى:

Sovereign Signal Registry

الذي سبق أن وضعناه ضمن الأصول المطلوبة للمشروع.

F — Prediction Ledger

نحتفظ بكل توقع، وليس الناجح فقط:

Prediction.
Timestamp.
Forecast horizon.
Probability.
Confidence.
Inputs.
Model version.
Market conditions.
Actual outcome.
Error.
Correct/incorrect classification.
Calibration result.

بعد فترة يصبح لدينا:

Verified Historical Prediction Track Record.

وده أصل لا يستطيع منافس بدأ غدًا إعادة خلقه بأثر رجعي.

G — Decision Ledger

ليس كل Intelligence Prediction.

لذلك نحتفظ أيضًا بكل Decision:

Decision ID.
Decision timestamp.
BUY/SELL/WAIT/AVOID أو التصنيف المستخدم.
Inputs.
Supporting evidence.
Conflicting evidence.
Confidence.
Risk assessment.
Algorithm/model versions.
User context إذا كان مسموحًا ومناسبًا.
Subsequent outcome.

فتصبح لدينا ذاكرة:

BLACKDARK Decision History
H — Outcome Intelligence

دي من أهم الطبقات كلها.

نربط:

What BLACKDARK knew → What BLACKDARK said → What actually happened.

ويتراكم:

Correct outcomes.
Incorrect outcomes.
Partial successes.
False positives.
False negatives.
Missed events.
Detection lead time.
Prediction error magnitude.
Decision performance.
Performance by asset.
Performance by exchange.
Performance by market regime.
Performance by volatility.
Performance by liquidity environment.
Performance by horizon.

وبالتالي النظام لا يعرف فقط:

كم مرة أصبت؟

بل:

متى أكون جيدًا ومتى لا ينبغي الوثوق بي بنفس الدرجة؟

وده أكثر قيمة.

I — Confidence & Calibration Intelligence
Predicted confidence.
Actual success probability.
Calibration history.
Confidence by engine.
Confidence by asset.
Confidence by regime.
Confidence by horizon.
Confidence deterioration/drift.
Confidence correction history.

ومن هنا تتطور قدرة مثل Personal/Model Confidence Calibration التي ناقشناها سابقًا.

J — Proprietary Feature Library

مع مرور الوقت نكتشف متغيرات جديدة لا تأتي جاهزة من Exchange.

Derived indicators.
Behavioral indicators.
Liquidity features.
Whale features.
Order-book features.
Cross-market features.
Cross-chain features.
Risk features.
Temporal features.
Composite indicators.
Feature interactions.
Regime-specific features.

وقد نكتشف مثلًا:

Feature A + B + C + D within T minutes

أقوى كثيرًا من أي منها منفردًا.

هذه المعرفة تصبح جزءًا من IP.

K — Proprietary Signal Combinations
Signal correlations.
Signal dependencies.
Signal conflicts.
Signal sequencing.
Signal timing relationships.
Signal decay.
Signal lead/lag.
Cross-asset signal relationships.
Cross-chain relationships.
Cross-exchange relationships.
Regime-dependent combinations.

وهنا يبدأ BLACKDARK في امتلاك Market Knowledge وليس مجرد Market Data.

L — Model Assets
Trained model versions.
Model checkpoints.
Training datasets.
Validation datasets.
Golden datasets.
Feature sets.
Hyperparameter histories.
Calibration models.
Ensemble configurations.
Regime-specific models.
Model-performance histories.
Model-drift histories.
Failure-case libraries.
Adversarial test datasets.
Benchmark histories.

لكن مهم: لا نعتبر Model نفسها Moat لمجرد وجود AI.

القيمة في:

Model + proprietary data + history + outcomes + feedback.

M — Market Regime Intelligence

مع الزمن يتعلم النظام حالات السوق المختلفة:

Bull regimes.
Bear regimes.
Sideways regimes.
High-volatility regimes.
Low-volatility regimes.
Liquidity crises.
Risk-on/risk-off.
Extreme funding regimes.
Deleveraging regimes.
Correlation regimes.
Stablecoin stress regimes.

ثم:

أي Engine يعمل أفضل في أي Regime؟

وهذه معرفة مهمة جدًا.

N — Failure Intelligence

هذه غالبًا يتم تجاهلها رغم أنها أصل مهم.

نحتفظ بكل مرة أخطأ فيها BLACKDARK:

Wrong predictions.
Bad signals.
False alarms.
Missed events.
Bad data incidents.
Data-source failures.
Algorithm failures.
Model failures.
Latency failures.
Infrastructure failures.
User-impact incidents.
Root-cause analyses.
Corrective actions.
Recurrence information.

بعد سنوات يصبح لدى BLACKDARK ذاكرة أخطاء تجعل النظام أكثر نضجًا.

O — User Intelligence

بموافقة المستخدم وبضوابط الخصوصية:

Feature preferences.
Assets followed.
Frequently used analyses.
Alert preferences.
Risk preferences.
Expertise level.
Preferred information depth.
Usage patterns.
Search/query patterns.
Decision-explanation preferences.
Portfolio-context preferences.
Notification behavior.

هذه لا تُستخدم للتجسس.

تستخدم لجعل:

BLACKDARK الخاص بالمستخدم A ≠ BLACKDARK الخاص بالمستخدم B.

P — Product Usage Intelligence

على مستوى المنتج، وبشكل مجمع عندما يكون ذلك مناسبًا:

Feature usage.
Feature retention.
Feature abandonment.
Session behavior.
Activation paths.
Conversion paths.
Upgrade paths.
Churn paths.
Search demand.
Most requested assets.
Most shared insights.
Most valuable alerts.
Feature-to-payment relationships.
Feature-to-retention relationships.
Friction points.
UX failure points.

وده يجعل تطوير المنتج بعد سنة مبنيًا على Evidence وليس رأينا.

Q — Commercial Intelligence
Conversion history.
ARPU history.
ARPPU history.
MRR history.
ARR history.
Churn history.
Retention cohorts.
LTV histories.
CAC by channel.
Payback period.
Tier migration.
Pricing elasticity.
Discount effectiveness.
Trial conversion.
Cancellation reasons.
Reactivation patterns.
Geographic monetization.
Segment monetization.

هذه نفسها تصبح معرفة تجارية مهمة جدًا للشركة.

R — Distribution/Growth Intelligence
Which channels produce users.
Which produce paying users.
Creator performance.
Affiliate performance.
Referral networks.
Viral coefficient history.
Share rates.
Content performance.
SEO authority/history.
Backlinks.
Search rankings.
Organic keyword footprint.
Community footprint.
Brand mentions.
Earned media.
PR relationships.
Creator relationships.
Community relationships.

بعد سنوات الشركة لا تملك منتجًا فقط.

تملك Distribution Network.

S — Network Effects

إذا صُممت أجزاء المنتج لذلك:

Community predictions.
User-generated intelligence.
Shared watchlists/strategies حيث يناسب المنتج.
Community reputation.
Analyst reputation.
Prediction reputation.
Collaborative intelligence.
Collective anomaly reporting.
Community datasets.
Benchmarking across aggregated users.

كل مستخدم جديد يمكن أن يجعل أجزاء من النظام أفضل للمستخدمين الآخرين.

وده Network Effect حقيقي إذا صممناه بطريقة صحيحة، وليس مجرد Community page.

T — Institutional Assets

مع كل مؤسسة جديدة:

API integrations.
Data-feed integrations.
Institutional workflows.
Custom reporting knowledge.
Institutional usage history.
SLA performance history.
Institutional support knowledge.
Integration templates.
Enterprise security experience.
Procurement experience.
Due-diligence responses.
Enterprise implementation playbooks.
Institutional reference customers.
Case studies.

وهذه تجعل بيع المؤسسة رقم 50 أسهل من بيع المؤسسة رقم 1.

U — Switching Costs

مع الاستخدام الحقيقي يتكون:

Saved configurations.
Historical dashboards.
Alerts.
Watchlists.
User-specific models/settings.
API integrations.
Workflow integrations.
Historical reports.
Team workflows.
Institutional audit history.
Customized intelligence.

كلما أصبحت BLACKDARK جزءًا من workflow العميل، تصبح تكلفة تغييره أكبر بسبب القيمة المتراكمة وليس بسبب حبس العميل اصطناعيًا.

V — Trust Capital

هذا أصل ضخم جدًا لا يوجد يوم الإطلاق:

Verified prediction history.
Availability history.
Security history.
Incident transparency.
SLA performance.
Accurate claims history.
Independent audit history.
Customer reviews.
Institutional references.
Public case studies.
Research credibility.
Media credibility.
Brand reputation.

لا يمكنك شراء 3 سنوات من الثقة في يوم واحد.

W — Operational Knowledge
Runbooks.
Incident playbooks.
Failure recovery knowledge.
Scaling knowledge.
Exchange-specific operational knowledge.
Data-provider behavior knowledge.
Deployment knowledge.
Capacity histories.
Traffic patterns.
Cost optimization knowledge.
Reliability tuning.
Security response knowledge.

هذا يسمى أحيانًا Organizational/Operational Know-how.

ومنافس جديد لا يمتلكه حتى لو امتلك نفس الكود.

X — Engineering Assets
Mature codebase.
Tested architecture.
Reusable components.
Internal libraries.
Data pipelines.
Observability infrastructure.
Testing infrastructure.
Simulation infrastructure.
Benchmark infrastructure.
Deployment infrastructure.
Security tooling.
Feature flags.
Experimentation infrastructure.
Data-quality infrastructure.
Model-validation infrastructure.

الكود نفسه يتراكم، لكن الكود + تاريخ إثباته وتشغيله أهم من عدد الأسطر.

Y — Security Intelligence
Attack history.
Abuse patterns.
Fraud patterns.
Bot patterns.
Authentication anomalies.
API-abuse patterns.
Threat indicators.
Security incident knowledge.
False-positive security patterns.
Detection rules.
Response playbooks.

وبالتالي Security نفسها تتحسن بمرور التشغيل.

Z — Data Quality Intelligence
Source reliability histories.
Source latency histories.
Source error histories.
Exchange-specific anomalies.
Schema-change histories.
Missing-data patterns.
Corrupt-data patterns.
Cross-source disagreement histories.
Data-quality scoring models.

بعد سنوات BLACKDARK قد يعرف:

أي مصدر أثق به، وفي أي ظرف، وبأي درجة.

ودي معرفة مهمة جدًا لنظام مالي.

AA — Intellectual Property

مع الزمن قد يتكون:

Proprietary algorithms.
Proprietary datasets.
Proprietary derived metrics.
Proprietary scoring systems.
Proprietary classifications.
Proprietary signal combinations.
Proprietary models.
Proprietary knowledge graph.
Proprietary benchmarks.
Trade secrets.
Potential patentable inventions حيث يكون ذلك منطقيًا قانونيًا.
Copyrighted research/content/code.
Brand/trademark assets.

هذه هي الطبقة التي تهم المستحوذ جدًا إذا كانت موثقة الملكية فعلًا.

AB — Experiment Knowledge
A/B test history.
Failed experiments.
Successful experiments.
Pricing experiments.
UX experiments.
Alert experiments.
Model experiments.
Feature experiments.
Growth experiments.
Onboarding experiments.

حتى التجربة الفاشلة تصبح معرفة:

جربنا X على 40,000 مستخدم ولم يعمل.

منافس جديد لا يعرف ذلك وقد يضيع ستة أشهر ليكتشفه.

AC — Research Knowledge Base
Internal research.
Market studies.
Quantitative studies.
Model studies.
Competitor histories.
Feature research.
Market-structure research.
On-chain research.
Failure research.
Experimental findings.

بمرور الزمن يمكن أن يصبح لدى الشركة Research Corpus خاص بها.

AD — Human/Organizational Capital

لو تحولت لاحقًا لشركة وفريق:

Engineering expertise.
Quant expertise.
Crypto market expertise.
Data expertise.
Security expertise.
Institutional sales knowledge.
Customer-support knowledge.
Relationships.
Hiring knowledge.
Internal processes.

هذا أيضًا جزء حقيقي من قيمة الشركة، وإن لم يكن Software.

AE — Brand & Attention Assets
Brand recognition.
Direct traffic.
Social followers.
Newsletter audience.
Telegram/Discord/community audience.
Creator network.
Media relationships.
Search demand for BLACKDARK.
Branded searches.
User advocacy.
Word of mouth.

لو بعد سنوات ملايين الأشخاص يعرفون الاسم، فهذه قيمة اقتصادية مستقلة عن الكود.

AF — Customer Assets
Registered user base.
Active user base.
Paying subscribers.
High-value users.
Institutional customers.
Customer cohorts.
Retained customers.
Referral users.
Enterprise pipeline.
Customer relationships.

طبعًا المستخدمون ليسوا «ملكية»، لكن قاعدة العملاء والعلاقات والإيرادات الناتجة عنها أصل اقتصادي للشركة مع احترام حقوقهم وخصوصيتهم.

AG — Financial History
Revenue history.
MRR growth.
ARR growth.
Gross margin history.
Cash-flow history.
Cohort revenue.
Revenue quality.
Renewal history.
Expansion revenue.
Enterprise contract history.

شركة لديها ثلاث سنوات نمو مثبت تختلف جذريًا في تقييمها عن شركة لديها نفس المنتج ولم تحقق إيرادًا بعد.

AH — Evidence & Due-Diligence Capital

وهذه مهمة جدًا لهدف الاستحواذ:

Capability evidence.
Test history.
Security audit history.
Pen-test history.
Load-test history.
Chaos-test history.
Availability evidence.
Model-validation history.
Data-lineage evidence.
Claims evidence.
Incident history.
Compliance evidence حيث ينطبق.
Architecture decision records.
Release certification history.
Independent review history.

بعد سنوات لا تقول للمستحوذ:

النظام ممتاز.

بل تعطيه سنوات من الأدلة.

AI — Regulatory/Compliance Maturity

ليس «ترخيصًا تلقائيًا»، وإنما المعرفة والأدلة التي تتراكم:

Privacy records.
Consent histories.
Data-retention governance.
Access reviews.
Audit trails.
Policy histories.
Risk assessments.
Vendor assessments.
Compliance-control evidence.
Regulatory-response experience.
AJ — Ecosystem Assets
Developer integrations.
API customers.
Apps using BLACKDARK data.
Widgets embedded externally.
Partners.
Data partners.
Technology partners.
Research partners.
Institutional partners.
Affiliate ecosystem.

وهنا BLACKDARK يبدأ التحول من Product إلى Platform.

AK — Developer Ecosystem
API adoption.
SDK adoption.
Developer accounts.
Third-party integrations.
Community libraries.
Integration templates.
Developer documentation knowledge.
API usage datasets.
External applications dependent on BLACKDARK.

دي من أقوى أنواع Switching/Network effects لو نجحت.

AL — Economic/Market Intelligence About BLACKDARK Itself
Demand forecasting.
Capacity forecasting.
Revenue forecasting.
Churn prediction.
User-LTV models.
Conversion prediction.
Fraud-risk prediction.
Infrastructure-cost models.
Market expansion intelligence.
Geographic demand intelligence.
Segment opportunity intelligence.

يعني BLACKDARK لا يتعلم السوق فقط؛ الشركة تتعلم نفسها.

لكن هناك طبقة أخيرة أعتبرها الأهم

كل ما سبق لا ينبغي أن يعيش كجزر منفصلة.

نحتاج من البداية:

BLACKDARK PROPRIETARY ASSET GRAPH

يربط:

Raw Data

→ Derived Data

→ Entity

→ Event

→ Feature

→ Signal

→ Prediction

→ Decision

→ Confidence

→ User exposure

→ Outcome

→ Error

→ Learning

→ Model version

→ Improvement

→ Commercial impact.

وبالتالي بعد سنوات نستطيع مثلًا أن نسأل النظام:

أي إشارات BLACKDARK الخاصة أدت إلى أفضل قرارات أثناء انهيارات السوق، وما مصدر بياناتها، وما دقتها التاريخية، وما المستخدمون الذين استفادوا منها، وهل أدت إلى retention أو subscription؟

ويكون لدينا جواب قابل للقياس.

والآن أهم تحذير في الحصر كله

ليس معنى أننا نستطيع جمع 500 نوع من المعلومات أننا يجب أن نجمع كل شيء.

كل Data تتعلق بالمستخدم يجب أن تمر على:

Purpose → Consent/legal basis where applicable → Minimization → Security → Retention → Access → Deletion.

لأن البيانات الزائدة قد تتحول من Asset إلى Liability.

وكذلك البيانات السوقية الخارجية يجب أن تكون حقوق تخزينها وإعادة استخدامها واضحة؛ لا نستطيع افتراض أن كل API يسمح لنا ببناء Dataset تجارية دائمة منها.

إذا أردت اختصار الـ500 نقطة إلى «الأصول الكبرى» التي أريد أن تتضاعف قيمتها

لدينا 15 أصول استراتيجية عليا:

1. Proprietary Historical Intelligence Dataset
2. Financial Entity/Relationship Graph
3. Market Event Knowledge Base
4. Sovereign Signal Registry
5. Prediction Ledger
6. Decision Ledger
7. Outcome & Failure Intelligence
8. Proprietary Features/Models/Algorithms
9. Verified Performance & Track Record
10. Product/User Intelligence
11. Distribution + Brand + Community Network
12. Institutional Integrations & Customer Base
13. Operational/Security/Engineering Know-how
14. Evidence/IP/Due-Diligence Capital
15. Ecosystem + API + Developer Network

والعلاقة بينهم هي التي تصنع الشيء الخطير:

More usage → More legitimate data → More outcomes → Better evidence → Better intelligence → Better product → More users → More integrations → More data/history → Stronger moat.

هذه هي الـFlywheel الحقيقية التي أقصدها.

والشيء الذي أؤكد عليه بشدة: يجب ألا ننتظر نجاح BLACKDARK ثم نفكر في بناء هذه الآلة. جزء كبير من البنية التي تسجل الـSignals والـPredictions والـDecisions والـOutcomes والـModel Versions والـData Provenance والـUsage Evidence يجب أن يكون موجودًا قبل Day 1 من الإطلاق، وإلا سنفقد جزءًا من أثمن أصل لا يمكن شراؤه لاحقًا: التاريخ.


كيف يتم ذلك عمليًا؟

لدينا أربع طبقات:

1. طبقة الجمع Collection Layer.
تلتقط باستمرار البيانات المسموح لنا بجمعها: Market/Order Book/OI/Funding/Liquidations/On-chain وغيرها، بالإضافة إلى ما ينتجه BLACKDARK نفسه من Signals وPredictions وDecisions. وبالنسبة لسلوك المستخدم، لا نجمع إلا ما له غرض واضح وبضوابط الخصوصية المناسبة.

2. طبقة الذاكرة Historical/Proprietary Data Layer.
بدل أن يستخدم المحرك البيانات ثم يرميها، نخزن ما يلزم تاريخيًا بصورة منظمة. هنا تتكون بمرور الوقت قواعد مثل: Market History وSignal Registry وPrediction Ledger وDecision Ledger وOutcome Ledger وMarket Event Library وEntity Graph وModel/Algorithm Version History وData Provenance.

3. طبقة التعلم والتحويل Intelligence Layer.
Jobs/Engines تعمل في الخلفية وتربط الماضي بالحاضر. مثال بسيط جدًا:

10:00 BLACKDARK أصدر إشارة BTC بثقة 82%.

نسجل ماذا كانت البيانات وقت إصدارها ونسخة المحرك التي أصدرتها.

10:30 / 4h / 24h حسب Horizon الإشارة، Outcome Evaluator يعود تلقائيًا ليرى ماذا حدث.

فتتحول الإشارة إلى سجل:

Inputs → Signal → Prediction → Decision → Actual Outcome → Error → Performance

وتتكرر العملية ملايين المرات مستقبلًا.

4. طبقة العرض UI/UX.
هنا فقط يأتي التصميم. المستخدم لا يرى ملايين السجلات. يرى النتيجة المفيدة منها: Confidence، Track Record، Historical Similarity، Evidence، جودة البيانات، أو Insight مخصص له.
إذن كيف يصبح «كل ده عندي»؟

ليس بعمل Folder اسمه Data Flywheel.

نحتاج قبل الإطلاق بناء منظومة فعلية داخل Architecture المشروع.

وأنا أقترح أن يكون اسمها داخليًا مثلًا:

BLACKDARK Proprietary Intelligence & Asset Accumulation System

وتحتها مستودعات/خدمات منطقية مثل:

Raw/Normalized Market History
Derived Intelligence Store
Signal Registry
Prediction Ledger
Decision Ledger
Outcome Ledger
Failure & Incident Intelligence
Market Event Knowledge Base
Entity/Relationship Graph
Feature Store
Model Registry
Experiment Registry
Data Lineage / Provenance
Usage & Product Analytics
Commercial/Growth Intelligence
Evidence & Track-Record Store

مش شرط إطلاقًا أن يكون كل واحد Database منفصلة. هذه تقسيمات منطقية؛ التصميم الفعلي يعتمد على Architecture الحالية وحجم البيانات والتكلفة.

مثال يوضح لك الموضوع

افترض يوم الإطلاق مستخدم فتح ETH.

BLACKDARK استقبل 20 نوع Data → أنتج 12 Derived Features → 4 Engines حللوها → أنتج Signal → Decision Engine أصدر WAIT بثقة 76%.

الواجهة تقول للمستخدم ببساطة:

WAIT — Elevated liquidation risk — Confidence 76%

لكن في الخلفية يمكن أن نسجل شيئًا مثل:

Event ID
Timestamp
ETH
Source versions
Data-quality state
Relevant feature values
Engine versions
Signal outputs
Decision = WAIT
Confidence = 76%
Expected horizon = 4h

وبعد 4 ساعات:

Actual market outcome
Was decision correct?
Error magnitude
Regime
Calibration result

وهكذا انتهى المستخدم من الشاشة في 20 ثانية، لكن BLACKDARK أصبح أغنى بحالة تاريخية جديدة.

كررها عبر ملايين الأحداث على مدى سنوات، وستفهم لماذا التاريخ نفسه يمكن أن يصبح أصلًا.

وبعض الأصول السابقة لا تُبرمج أصلًا

وده تصحيح مهم للحصر السابق.

هناك أشياء يبنيها النظام تقنيًا: البيانات التاريخية، Signals، Decisions، Outcomes، Knowledge Graph، Track Record.

وأشياء تتكون من الاستخدام التجاري: العملاء، MRR، retention cohorts، churn history، pricing intelligence.

وأشياء تتكون من الانتشار: Brand، backlinks، community، creator relationships، direct traffic.

وأشياء تتكون من التشغيل: incident history، reliability history، runbooks، operational know-how.

وأشياء تتكون من المؤسسات: API integrations، contracts، reference customers، SLA history.

وأشياء تتكون من الفحص المستمر: security evidence، performance evidence، audit history، release certifications.

يعني لا يوجد كود واحد يخلق الـ500 نقطة. نحن نبني قبل الإطلاق البنية التي تسمح للأصول المناسبة منها بالتراكم، ثم التشغيل الحقيقي يبني الباقي.

وما الذي يجب فعله الآن تحديدًا؟

لا أريد أن تقول لـCursor: "نفذ الـ500 نقطة". ده قد ينتج Architecture ضخمة ومكلفة بلا داعٍ.

الأصح عندما ننتهي من الأعمال الحالية أن نطلب أولًا Audit فقط للمشروع الحالي:

ما الموجود بالفعل من هذه المنظومة؟
ما الذي يجمعه المشروع حاليًا؟
ما الذي يخزنه؟
ما الذي يضيع بعد الحساب؟
هل Signals محفوظة؟
هل Predictions محفوظة؟
هل Outcomes مرتبطة بها؟
هل Model/Algorithm versions محفوظة؟
هل يوجد Data lineage؟
هل توجد Usage analytics؟
وهكذا.

ثم نبني Gap Matrix مقابل الأصول التي حصرتها لك.

بعدها نصنفها:

MUST EXIST BEFORE LAUNCH
BUILD AFTER REAL USAGE STARTS
EMERGES NATURALLY WITH SCALE
NOT WORTH COLLECTING

وهذا يمنعنا من بناء مصنع بيانات عملاق قبل وجود مستخدمين.

والأهم

أريد إضافة هذا رسميًا إلى برنامج الفحص المؤسسي الذي اتفقنا عليه قبل الإطلاق تحت Gate مستقل:

GATE — PROPRIETARY ASSET ACCUMULATION & DATA FLYWHEEL READINESS

ومعيار النجاح ليس:

لدينا Database.

بل:

من أول يوم Production، كل حدث ذي قيمة يمكن تتبعه من مصدر البيانات → المعالجة → Feature → Signal → Prediction/Decision → Version → Outcome → Evidence، مع سياسات جودة وخصوصية واحتفاظ وحقوق استخدام واضحة.

إذا تحقق ذلك، أنت لا تحتاج كل سنة أن تعمل شيئًا يدويًا حتى "تكوّن الأصل". النظام نفسه مصمم ليكوّن الأجزاء القابلة للتراكم أثناء التشغيل، بينما الاستخدام والعملاء والسمعة والأدلة يضيفون الطبقات الأخرى بمرور الزمن.

وده بالضبط ما أريد أن نضمن وجوده قبل الإطلاق، لأننا نستطيع إصلاح Feature بعد الإطلاق، لكن لا نستطيع الرجوع إلى اليوم الأول بعد سنتين واستعادة تاريخ لم نسجله أصلًا.
ده هو الـMoat.

وفي حالة BLACKDARK تحديدًا، الـMoat القوي الذي أريد بناءه ليس شيئًا واحدًا، بل منظومة مترابطة:

Proprietary Data → Signals → Decisions → Outcomes → Learning → Better Intelligence → More Users → More Data/Outcomes → Stronger Track Record → More Institutions → More Integrations → Stronger BLACKDARK.

الأصل الذي نحفظه من الآن	ماذا نحفظ؟	لماذا قد يرفع القيمة؟
1. Architecture Decision History	كل قرار معماري + البدائل + سبب الاختيار	يثبت نضج الهندسة ويمنع ضياع المعرفة
2. Capability Evolution Ledger	تاريخ كل قدرة من الفكرة حتى Production	يثبت أن القدرات حقيقية وليست أسماء
3. Benchmark History	أداء كل Engine في كل إصدار	يثبت التحسن بمرور الزمن
4. Data Quality History	جودة/Freshness/فشل كل مصدر	يتحول لمعرفة خاصة عن موثوقية السوق
5. Data Rights & Licensing Ledger	مصدر كل Dataset وحقوق التخزين والاستخدام	مهم جدًا لقيمة البيانات عند الاستحواذ
6. IP Provenance Registry	أصل الكود والخوارزمية والـDataset والـlicense	يثبت ما الذي تملكه الشركة فعلًا
7. Dependency/SBOM History	المكتبات والإصدارات والتراخيص	يقلل مخاطر DD والأمن
8. Security Evidence History	scans، vulnerabilities، fixes، tests	يصنع سجل نضج أمني طويل
9. Reliability History	uptime، latency، errors، recovery	دليل تشغيلي لا يمكن اختلاقه لاحقًا
10. Cost History	تكلفة كل Engine/Data/API/AI operation	يبني معرفة Unit Economics
11. Performance/Capacity History	throughput، concurrency، bottlenecks	يثبت قابلية التوسع
12. Experiment Registry	التجربة والفرضية والنتيجة والقرار	حتى التجارب الفاشلة تصبح معرفة
13. Failure Corpus	الأخطاء، root cause، الإصلاح، regression test	يصنع ذاكرة هندسية متراكمة
14. Research Corpus	الدراسات والاكتشافات والفرضيات والنتائج	يتحول إلى Know-how/IP
15. Competitive Evolution Database	تغير المنافسين والأسعار والقدرات	يصنع ذاكرة استراتيجية للسوق
16. Claims Evidence Registry	كل ادعاء تسويقي وما الدليل عليه	يحمي الثقة ويقوي الفحص المؤسسي
17. Design Decision History	لماذا صُممت تجربة المستخدم بهذه الطريقة	يمنع تغييرات UX العشوائية
18. Test Evidence History	ماذا اختُبر ومتى وعلى أي Version	يحول QA إلى سجل إثبات
19. Release History	كل إصدار وما تغير وأدلته	تاريخ تطور المنتج
20. Acquisition Evidence Vault	الأدلة السابقة بصورة منظمة	يجعل DD جاهزًا باستمرار
وهناك 6 أشياء إضافية أعتبرها ذات قيمة خاصة

أولًا: Capability DNA.
كل قدرة مهمة يكون لها سجل دائم:

Capability → Purpose → Data → Algorithm → Dependencies → Tests → Benchmark → Limitations → Owner/IP → Version → Evidence

وبالتالي بعد سنتين، لو المستحوذ سأل: «ما القيمة التقنية الحقيقية للقدرة رقم 217؟» لا نبدأ البحث في الكود؛ عندنا ملف إثبات كامل لها.

ثانيًا: Negative Knowledge.
نحفظ ليس فقط ما نجح، بل ما اكتشفنا أنه لا يعمل: Algorithms فشلت، Data sources سيئة، Signals مضللة، أفكار تم رفضها، Experiments لم تحقق نتيجة. هذه المعرفة توفر سنوات من إعادة ارتكاب الأخطاء.

ثالثًا: Performance Frontier History.
نحفظ أفضل ما استطاع BLACKDARK تحقيقه في كل مرحلة: Accuracy/precision المناسب للمهمة، latency، data freshness، throughput، false positives وغيرها. فيصبح لدينا منحنى تاريخي يوضح تطور التكنولوجيا بدل ادعاء «النظام تحسن».

رابعًا: Dataset Genealogy.
لكل Dataset مهمة:

Source → Raw → Cleaning → Normalization → Enrichment → Features → Model/Engine → Output

وبذلك نعرف بالضبط كيف تكوّن الأصل، وهل نملك حق استخدامه، ومن يستخدمه.

خامسًا: Institutional Readiness History.
من الآن نحفظ نتائج Security/Architecture/Performance/Data/AI/Financial Accuracy reviews والإغلاقات وإعادة الاختبارات. بعد فترة يصبح لدينا تاريخ طويل من الحوكمة الهندسية وليس تقريرًا صنعناه قبل البيع بأسبوع.

سادسًا: Source Reliability Intelligence.
BLACKDARK مع الزمن يتعلم مثلًا أن Source X ممتاز في الظروف العادية ولكنه يتأخر أثناء volatility، بينما Source Y أسرع لكنه أكثر أخطاءً. هذه المعرفة يمكن لاحقًا أن تجعل النظام يختار أو يزن مصادره ديناميكيًا. وهنا حتى تاريخ أخطاء مزودي البيانات يصبح أصل Intelligence.

وفي مرحلة التصميم نفسها، هناك أشياء لا تحتاج حتى انتظار السوق

يمكن أن نبدأ فورًا في حفظ:

Git/Code history + Architecture decisions + Capability evolution + Tests + Benchmarks + Experiments + Failures + Security evidence + Performance evidence + Data provenance + Dataset rights + IP provenance + Research + Competitive intelligence + Design decisions + Release certifications.

يعني مرحلة التطوير الحالية نفسها يمكن تحويلها إلى أصل متراكم بدل أن تكون مجرد فترة نكتب فيها كودًا.

والقاعدة التي أوصي باعتمادها للمشروع من الآن:

DON'T DELETE KNOWLEDGE — COMPOUND IT.

أي معلومة نتعلمها ولها قيمة مستقبلية لا تظل داخل محادثة Cursor أو log مؤقت ثم تختفي؛ تتحول إلى structured, versioned, searchable evidence/knowledge.

وبالتالي نحن أصبح لدينا 4 أنواع من التراكم تبدأ قبل الإطلاق:

Market Intelligence — يتعلم السوق.
Product Intelligence — يتعلم المنتج والمستخدم مستقبلًا.
Engineering Intelligence — يتعلم من البناء والأخطاء والاختبارات.
Business/IP Intelligence — يحفظ البحث والملكية والأدلة والقرارات.

ولو جمعنا هذا مع Data Flywheel + Forward Track Record + Knowledge Graph + Platform Architecture + Evidence System التي اتفقنا عليها، فنحن لا نصمم BLACKDARK فقط؛ نحن نصمم آلة تجعل قيمة الأصل قابلة للتراكم من فترة التطوير نفسها.

# الملحق 5: النص المرجعي الكامل للتقرير 5 - محفوظ دون دمج
Control: lines=137 | nonblank=83 | chars=7129 | SHA-256=d7ca764289d32426fd7717c2dad89da1d0a6519243723e478ed1bb8bdfb778f4
هذا الملحق هو المرجع النصي الأعلى عند أي اختلاف بين الصياغة الاستشارية والنص المصدر.
أيوه، نقدر نسرّع التراكم جدًا، لكن لا توجد طريقة شرعية/علمية تحول مشروعًا جديدًا إلى صاحب «3 سنوات Track Record حقيقي» في أسبوع. الحل الاحترافي هو أن نفصل بين التاريخ الذي يمكن Backfill له الآن وبين التاريخ الذي لا يمكن أن يتكون إلا من تشغيل BLACKDARK نفسه.

أسرع استراتيجية أراها هي Historical Backfill + Replay + Synthetic Stress + Shadow Production بالتوازي:

Historical Backfill: بدل انتظار السوق من اليوم، نستورد تاريخًا قديمًا مرخصًا قدر الإمكان: أسعار، OHLCV، Funding، OI، Liquidations، On-chain، DEX، gas، وبعض Order Book history إذا توفر قانونيًا. بذلك تبدأ قواعد البيانات بتاريخ سابق بدل Day Zero.
Historical Replay: هذه أهم خطوة. نشغل محركات BLACKDARK الحالية على البيانات القديمة وكأن الزمن يتحرك لحظة بلحظة. عند كل لحظة لا نسمح للمحرك برؤية المستقبل. يصدر Signal/Prediction/Decision، ثم نكشف له ما حدث لاحقًا ونكتب Outcome. بذلك يمكننا تكوين ملايين Signal → Outcome بسرعة حاسوبية بدل انتظار ملايين الأحداث في الزمن الحقيقي.
Event Reconstruction: نبني مكتبة تاريخية لأحداث حقيقية: انهيارات، depegs، liquidation cascades، squeezes، exchange outages، volatility explosions، whale movements وغيرها، ثم نعيد تشغيل BLACKDARK عليها. وهكذا يبدأ Market Event Knowledge Base ممتلئًا قبل الإطلاق.
Parallel Simulation: نشغل آلاف السيناريوهات بالتوازي على عدة Assets/Exchanges/Timeframes. سنة تاريخية لا يلزم أن تستغرق سنة فعلية؛ Compute يستطيع تحليلها أسرع بكثير.
Synthetic/Stress Data: نصنع سيناريوهات مصطنعة لاختبار الحالات النادرة: انقطاع مصدر، stale prices، انهيار سيولة، extreme volatility، corrupt data وغيرها. لكن تظل موسومة SYNTHETIC ولا تختلط مطلقًا بالـreal historical evidence.
Shadow Mode قبل الإطلاق: بمجرد جاهزية المحركات، نشغلها 24/7 على السوق الحقيقي حتى لو لم يدخل مستخدم واحد. لا تنفذ أموالًا؛ فقط Live Data → Signal → Timestamp → Prediction → Outcome. وهكذا يبدأ Forward Track Record الحقيقي قبل الإطلاق التجاري.
Continuous Outcome Factory: كل Signal ينتجه النظام مستقبلًا يجب أن ينشئ تلقائيًا Outcome jobs مثل 5m/1h/4h/24h بحسب نوع الإشارة. بذلك لا نحتاج موظفًا يعود ويقيم ملايين التوقعات يدويًا.
Knowledge Extraction: بعد الـReplay لا نخزن النتائج فقط؛ نستخرج العلاقات: أي Signals تعمل معًا؟ متى تفشل؟ أي Regime؟ أي Exchange؟ أي Asset؟ Lead time؟ False positives؟ وهنا يتحول التاريخ إلى Proprietary Intelligence.
Entity Graph Backfill: بالنسبة للـon-chain، يمكن إعادة بناء تاريخ العلاقات المتاح قانونيًا: Wallet ↔ Wallet ↔ Exchange ↔ Protocol ↔ Token ↔ Event، ثم يستمر تحديثه Live. بذلك لا يبدأ Knowledge Graph فارغًا.
ابدأ Product Analytics وEvidence من أول يوم حقيقي. أشياء مثل retention، conversion، churn، user preferences، institutional integrations، brand، community وcustomer history لا يمكن Backfill لها بصدق. هذه تحتاج مستخدمين وزمنًا حقيقيين.

والنقطة الحاسمة: نفصل داخل BLACKDARK بين أربعة أنواع Evidence:

BACKTESTED = BLACKDARK اختُبر على الماضي.
SIMULATED = سيناريو مصطنع.
SHADOW/LIVE FORWARD = قرار صدر لحظيًا قبل معرفة النتيجة.
PRODUCTION VERIFIED = سجل استخدام إنتاجي حقيقي.

ممنوع مثلًا أن نشغل المحرك اليوم على بيانات 2024 ثم نقول للمستثمر: «BLACKDARK تنبأ بانهيار 2024». الصحيح: «Current engine successfully detected the historical event under point-in-time replay.» الفرق ضخم أمام Due Diligence.

أسرع بنية ممكنة

بدل:

نطلق → ننتظر سنتين → تتكون البيانات.

نعمل:

Licensed Historical Data
↓
Massive Backfill
↓
Point-in-Time Replay Engine
↓
Signal/Prediction/Decision Ledger
↓
Automated Outcome Evaluator
↓
Event Knowledge Base + Entity Graph
↓
Model/Signal Validation

وفي نفس الوقت:

Live Market → 24/7 Shadow Engine → Immutable Timestamped Forward Record

ثم عند الإطلاق:

Real Users → Usage/Commercial/Network/Institutional Data

وبالتالي يوم الإطلاق قد نمتلك بالفعل تاريخًا سوقيًا طويلًا + ملايين الاختبارات التاريخية + مكتبة أحداث + Knowledge Graph + Benchmarking واسع + أسابيع/أشهر من Forward Shadow Evidence، بدل البدء من الصفر.

لكن الشيء الذي لا أريد اختصاره صناعيًا هو الـForward Track Record والثقة والـretention والعملاء والسمعة. مرور الزمن نفسه جزء من قيمة هذه الأصول.

لو هدفنا تعظيم قيمة BLACKDARK بسرعة، فهذه تحديدًا نقطة تستحق أن تدخل في الـPre-Launch Architecture: نبدأ الآن الـBackfill + Replay + Shadow Mode بدل انتظار يوم الإطلاق.


نعم، ونقدر نبدأ من دلوقتي، وده في الحقيقة أفضل من انتظار اكتمال التصميم.

لأن معظم المنظومة التي تكلمنا عنها Backend/Data Infrastructure وليست شكل الموقع. تغيير الألوان أو Dashboard أو ترتيب الصفحات لاحقًا لا يمنعها من العمل.

والأفضل أن نبدأ الآن في الأشياء التي كل يوم تأخير فيها يعني تاريخًا ضائعًا:

1. Live Shadow Collection — تشغيل جمع البيانات الحقيقية المتاحة 24/7 من الآن، بدون انتظار المستخدمين وبدون تنفيذ مالي.

2. Historical Backfill — ملء التاريخ السابق من المصادر التي تسمح شروطها وحقوقها بذلك، بدل أن تبدأ قواعدنا من أغسطس 2026 فقط.

3. Signal Registry — أي Signal حقيقية تنتجها المحركات الحالية تبدأ تُحفظ مع Timestamp والمدخلات والمصدر.

4. Prediction Ledger — تسجيل أي Prediction قبل معرفة النتيجة.

5. Decision Ledger — تسجيل قرارات المحركات وأسبابها وConfidence وإصدار الخوارزمية.

6. Automated Outcome Evaluator — يرجع بعد المدة المحددة ويعرف ماذا حدث بالفعل ويربط النتيجة بالتوقع/القرار.

7. Data Provenance — الاحتفاظ بمصدر البيانات، وقت الحصول عليها، Freshness، Quality، والتحويلات التي تمت عليها.

8. Algorithm/Model Versioning — لازم نعرف أن Prediction معينة صدرت بواسطة Version X، لأن الخوارزميات ستتغير أثناء استمرارنا في التصميم.

9. Historical Replay Engine — تشغيل المحركات على الماضي بطريقة Point-in-Time صحيحة لتكوين Backtested Evidence بسرعة.

10. Market Event Library — إعادة بناء وتسجيل الأحداث التاريخية المهمة وربط ما كانت تراه المحركات قبل/أثناء/بعد الحدث.

11. Failure Registry — تسجيل Data failures، engine failures، missing/stale data، والانحرافات من الآن.

12. Evidence Store — نتائج الاختبارات والـbenchmarks والـbacktests والـforward observations تحفظ بصورة قابلة للتدقيق بدل أن تضيع في Logs متفرقة.

وهناك أشياء لا نبدأ بتصنيعها الآن لأنها تحتاج مستخدمين حقيقيين: Retention، Churn، Conversion، User behavior، Referral network، Community، Brand equity، Institutional switching costs وغيرها. ستبدأ طبيعيًا عند الـBeta/Launch.

وهناك ميزة كبيرة جدًا لبدء هذا الآن

نحن ما زلنا نعدل BLACKDARK.

افترض أن المحرك اليوم هو V1، وبعد شهر أصبح V7.

لن نمسح القديم.

يصبح لدينا:

V1 → 62% historical performance
V2 → 65%
V3 → 61%
V4 → 70%
…
V7 → 76%

الأرقام مثال فقط.

وبالتالي يتكون عندنا تاريخ تطور حقيقي للمحركات، ونستطيع معرفة هل التعديلات حسنت النظام فعلًا أم أننا فقط نظن ذلك.

لكن هناك شرط هندسي مهم

لا أريد أن نقول لكلود الآن: «ابنِ كل منظومة الـ500 نقطة».

ده ممكن يخليه يوقف العمل الحالي ويدخل في Architecture ضخمة جدًا.

الترتيب الصحيح:

أولًا: يكمل الأعمال الحالية التي يعمل عليها.

ثانيًا: نعمل Audit للمشروع لمعرفة ما الموجود أصلًا؛ لأن أجزاء من Signal/Outcome/Data infrastructure قد تكون موجودة بالفعل.

ثالثًا: نصمم Asset Accumulation Architecture بناءً على الموجود، وليس من الصفر.

رابعًا: ننفذ Minimum Pre-Launch Accumulation Core.

خامسًا: نشغل الـLive Shadow Collection فورًا.

من اللحظة دي الساعة تبدأ لصالحنا.

ولو بدأناه مثلًا هذا الأسبوع ثم استغرق إكمال BLACKDARK شهرين، فلن نصل إلى يوم الإطلاق ونبدأ جمع Forward History وقتها؛ سيكون النظام بالفعل قضى الشهرين السابقين يراقب ويتعلم ويسجل ويُقيَّم.

وده بالضبط النوع من العمل الذي أفضّل أن يبدأ أثناء التصميم وليس بعده.




تمام النقطة الى بعها الى عاوز ابعت لكورسر واتاكد من التنفيذ والجاهزية  باعلى المعاير المؤسسية العالمية وكل الى قولتلك علية قبلكدا محتاج اتاكد منة حبعت اطلب منة اية ملاحظة مهمة الطلب يكون محدد جدا لتوفير اقصى مساحة من استهلاك كورسر مع تحقيق الهدف المطلوب

# 18. ملحق التطوير المؤسسي الحاكم — Institutional Committee Hardening Addendum v4
حالة هذا الملحق: DOMAIN-SPECIFIC GOVERNING OVERLAY — تابع للمرجع المؤسسي BLACKDARK v5 المحدث، ولا ينشئ مصدر حقيقة موازياً له. عند التعارض: v5 يحكم المنهج والبوابات والحالات والأدلة؛ والملاحق الخمسة الأصلية داخل هذه الوثيقة تحكم نية المصدر والمحتوى التخصصي الذي لا يتعارض مع v5.
منهج التطوير: Source-Preserved / Append-Only. لم يتم حذف أو استبدال أي نص من الوثيقة الأصلية؛ التطوير يضيف فقط متطلبات تخصصية لازمة لجعل منظومة البيانات والتخزين والتراك قابلة للفحص وإعادة الأداء أمام لجنة تصميم/فحص/استحواذ.
مرجع التقييم: ISO/IEC 25010:2023، ISO/IEC 25012:2008، ISO/IEC/IEEE 29148:2018، NIST CSF 2.0، NIST SSDF 1.1، NIST AI RMF 1.0، وممارسات Google SRE عند SLI/SLO/Error Budget. استخدام هذه المراجع هنا هو مواءمة معيارية/إرشادية؛ وليس ادعاء شهادة أو امتثال قانوني.
# 19. نتيجة المراجعة المعيارية السباعية
# 20. سجل العيوب والفجوات والحلول المؤسسية
# 21. المتطلبات التخصصية الإلزامية الجديدة — Domain-Specific Requirements Register
هذه المتطلبات لا تعيد كتابة v5. أي Security/AI/UX/CI/G0–G7 requirement عام يظل في v5؛ البنود التالية تضيف فقط ما يلزم لهذه الوثيقة التخصصية في البيانات والتخزين والتراك.
# 22. Data Asset Contract — النموذج الحاكم لكل أصل بيانات مادي
# 23. Point-in-Time / Replay / Track-Record Integrity Framework
كل replay يستخدم فقط المعلومات التي كانت متاحة فعليًا عند decision timestamp، مع فصل event time عن ingest/availability time.
Universe membership وasset/exchange eligibility يجب snapshot عند الزمن التاريخي؛ لا يجوز اختيار الناجين فقط بعد معرفة النتائج.
Provider revisions/backfills/corrections يجب إما استخدام النسخة التي كانت متاحة حينها أو وسم التجربة بوضوح بأنها reconstructed-with-later-data؛ لا تخلط النوعين.
تثبت الحزمة: data snapshot/hash، code SHA، model/rule/config version، clock/timezone، feature versions، oracle، horizon، fees/slippage assumptions إن كانت مؤثرة، exclusions، result.
كل Forward Shadow record يصدر قبل outcome ويخزن immutable timestamp + inputs + version + confidence + horizon، ثم يرتبط بالOutcome لاحقًا.
أي تصحيح لاحق يضاف كنسخة/Correction Event؛ لا يمحو الادعاء أو السجل الأصلي.
الـTrack Record يعرض denominator أيضًا: emitted predictions + eligible opportunities + misses + abstentions حيث ينطبق، وليس success rate للإشارات المختارة فقط.
# 24. Storage, Retention & Cost Architecture
المبدأ: لا تُحوَّل الوثيقة إلى مشروع Data Engineering ضخم. تُبنى فقط الطبقات التي تحفظ تاريخًا غير قابل للاستعادة لاحقًا أو تخدم use-case/assurance واضح. التصنيف التالي هو قرار تصميم، وليس إلزامًا باستخدام قاعدة بيانات منفصلة لكل بند.
Cost guard: كل أصل كبير أو high-frequency يجب أن يملك owner + storage/compute/data-provider cost + growth rate + query/replay value + deletion/compaction strategy. الهدف منع تحول الـMoat إلى تكلفة تخزين غير منضبطة.
# 25. Evidence / Recovery / Reperformance Package
لكل أصل أو claim مادي، يجب أن تستطيع لجنة مستقلة الوصول من Requirement إلى نتيجة قابلة لإعادة الأداء دون ذاكرة المطور:
Requirement → Asset/Claim ID → Owner → Data Rights → Canonical Source → Dataset Snapshot/Version → Transformation/Feature → Model/Rule/Config Version → Test/Oracle → Tested SHA/Build → Evidence → Outcome → Exceptions/Residual Risk → Local/Integrated/Live/Independent State.
للـstateful ledgers/registries: وجود backup لا يساوي recovery. يجب وجود Restore Test يثبت integrity بعد الاستعادة وRTO/RPO المحققين حيث ينطبق.
# 26. بوابة الإغلاق المحدثة — DATA FLYWHEEL & PROPRIETARY ASSET READINESS
تظل البوابة الأصلية قائمة، لكن لا تُغلق بعد هذا التطوير إلا إذا تحقق الآتي للمواد الجوهرية:
لا توجد Dataset/Stream مادية بلا Data Asset Contract.
لا توجد Data Rights مجهولة أو غير قابلة للإنفاذ في مسار الاستخدام المقصود.
لا يوجد replay/backtest مادي بلا PIT evidence قابل لإعادة الأداء.
لا يوجد Signal/Prediction/Decision مادي بلا version/provenance/evidence/outcome trace.
لا توجد history corrections تمحو النسخ المستخدمة سابقًا.
لا توجد quality/freshness failures تمر بصمت للمستخدم أو للـAI/decision path.
لا يوجد critical stateful asset بلا restore evidence مناسب.
لا يوجد claim يخلط Backtested/Simulated/Forward Shadow/Verified Production/Independent Assurance.
لا يوجد unresolved material conflict في truth/entity/data lineage.
لا توجد locally-solvable material deficiencies معروفة؛ وما يتطلب Live/G6 أو Independent/G7 يظل مصنفًا خارجيًا ولا يتحول إلى PASS محلي.
الحالات المسموح بها لهذه البوابة: READY_NOT_PROVEN / PASS_ENGINEERING / PASS_LIVE / ASSURANCE_READY، وفق تعريفات v5. لا تستخدم COMPLETE VERIFIED كبديل غامض عن طبقة الدليل الفعلية.
# 27. Red Flags — NO-GO تخصصية
Unknown/ambiguous material data storage or derived-use rights.
Point-in-time leakage أو future/revision information مستخدمة دون disclosure.
Replay/Backtest presented as historical live prediction.
Outcome denominator أو opportunity universe غير معرف مع نشر accuracy/recall claims.
Entity/Wallet attribution عالي الأثر بلا provenance/confidence أو مع conflict غير ظاهر.
Historical corrections overwrite evidence needed for reproducibility.
Stale/corrupt data can reach a decision path as LIVE without explicit degradation.
Critical ledger/registry backup exists but restore has never been proven where local/integrated proof is possible.
Rights/retention policy says “do not use” but technical path still allows export/training/API resale.
Living Data Room contains stale/expired claims presented as current.
# 28. ترتيب التنفيذ بعد اعتماد هذا التطوير
1) لا تُبنى كل البنود دفعة واحدة. Audit المشروع الحالي أولًا ضد DSR-001…DSR-024 وv5.
2) أنشئ Gap Matrix: EXISTING_VERIFIED / PARTIAL_CANONICAL / GREENFIELD / EXTERNAL_BLOCKED وغيرها حسب v5.
3) أغلق محليًا أولًا: contracts, lineage, rights, registries, evidence, replay integrity, versioning, restore design/tests الممكنة، بدون Railway إذا لم يكن مطلوبًا تقنيًا.
4) شغّل Live Shadow/Forward Record فقط عندما البيئة الحية متاحة وآمنة؛ لا تزعم PASS_LIVE قبل G6.
5) ما يحتاج real users/institutions/time يظل في فئته ولا يتم اصطناعه أو backfill زائفًا.
6) G7/Independent Assurance يبقى مستقلًا؛ لا يُستبدل بأدلة Cursor/CI.
# 29. سجل المراجع العلمية/المعيارية المستخدمة في التطوير
# 30. الحكم المؤسسي النهائي للوثيقة بعد التطوير
الحكم على النسخة الأصلية: STRONG DOMAIN SPECIFICATION / NOT FULLY COMMITTEE-CLOSED — قوية جدًا استراتيجيًا ومعماريًا، لكن كانت تحتاج عقودًا تخصصية قابلة لإعادة الأداء للبيانات، الحقوق، PIT replay، schema/history corrections، storage lifecycle، evidence integrity، recovery، وasset-value governance.
الحكم على النسخة المطورة: COMMITTEE-HARDENED DOMAIN GOVERNING SPECIFICATION — قابلة للاستخدام كمرجع تخصصي تحت v5 لإجراء Audit/Gap Matrix وتنفيذ Delta فقط. هذا الحكم يخص جودة المواصفة نفسها؛ ولا يعني أن مشروع BLACKDARK نفذ كل المتطلبات، ولا يعني PASS_LIVE أو G7 أو شهادة ISO/NIST.
قاعدة الإغلاق: NO KNOWN MATERIAL DOCUMENT-SPECIFICATION DEFICIENCY within this review scope. Implementation assurance remains evidence-dependent and must be proven against the actual repository/environment.

## Table 1
| الجولة | ماذا تم فحصه | الحالة |
| --- | --- | --- |
| الجولة 1 - Ingestion Integrity | التحقق من وجود التقارير الخمسة، أحجامها، وعدم فقدان ملفات المصدر. | PASS |
| الجولة 2 - Structural Inventory | التحقق من العناوين/الأطر/القوائم العليا المميزة لكل تقرير، بما فيها 12 Vaults، 20 Pre-Launch Assets، 30 Design Mandates، A-AL Asset Inventory، و4 Evidence Classes. | PASS |
| الجولة 3 - Preservation Audit | إدراج النص الكامل لكل تقرير داخل ملاحق مستقلة دون حذف متعمد أو دمج للمصدر. | PASS |
| الجولة 4 - Consultant Rewrite Audit | إعادة تنظيم المتطلبات في هيكل استشاري، مع الحفاظ على المعنى والشروط والقيود والتمييز بين ما يبدأ الآن وما يتطلب مستخدمين أو Scale. | PASS |
| الجولة 5 - Reverse Traceability & Render QA | مراجعة عكسية: كل مجموعة رئيسية في المصدر لها تمثيل في المواصفة أو الملحق المرجعي؛ ثم فحص إخراج DOCX بصريًا بعد الرندر. | PASS بعد الرندر النهائي |

## Table 2
| التقرير | عدد الأسطر | غير الفارغ | عدد المحارف | SHA-256 مختصر |
| --- | --- | --- | --- | --- |
| R1 | 603 | 369 | 11612 | ac61fa4781bcbca9… |
| R2 | 477 | 299 | 10278 | 898885e29f921a55… |
| R3 | 176 | 92 | 8521 | 30a466ef0d20f7ad… |
| R4 | 1111 | 843 | 29064 | 4b43ad8c8594d736… |
| R5 | 137 | 83 | 7129 | d7ca764289d32426… |

## Table 3
| المحرك | وظيفته |
| --- | --- |
| DATA COMPOUNDING | السوق، التاريخ، البيانات الخام والمشتقة، Knowledge Graph. |
| INTELLIGENCE COMPOUNDING | Signals، العلاقات، المقاييس الخاصة، Market Memory. |
| LEARNING COMPOUNDING | Predictions، Decisions، Outcomes، Failures، Counterfactuals، Missed Opportunities. |
| TECHNOLOGY COMPOUNDING | Models، Algorithms، Benchmarks، Experiments، Hard Cases، Drift. |
| TRUST COMPOUNDING | Forward Track Record، Security، Reliability، Reproducible Evidence، Transparency. |
| PRODUCT & CUSTOMER COMPOUNDING | Usage، Demand، Retention، Conversion، Economics، Institutional requirements. |
| DISTRIBUTION COMPOUNDING | SEO، Viral Objects، Referrals، Creators، Embeds، API ecosystem. |
| CORPORATE VALUE COMPOUNDING | IP، Data Rights، Documentation، Revenue Quality، Due-Diligence Evidence. |

## Table 4
| الخزينة | ما يتراكم فيها |
| --- | --- |
| Data Vault | Market/on-chain history + derived data. |
| Intelligence Vault | Signals + relationships + events + proprietary metrics. |
| Decision & Outcome Vault | Predictions + decisions + outcomes + calibration. |
| Model Vault | Models + algorithms + versions + benchmarks. |
| Failure Vault | Errors + failed cases + root causes. |
| Evidence Vault | Tests + security + load + reliability + claims evidence. |
| IP Vault | Algorithms + datasets + research + licenses + provenance. |
| Product Vault | Experiments + UX decisions + feature economics. |
| Customer Vault | Usage + retention + conversion + feedback. |
| Distribution Vault | SEO + referrals + content + embeds + community. |
| Institutional Vault | APIs + integrations + SLA + enterprise knowledge. |
| Corporate/DD Vault | Ownership + contracts + decisions + documentation. |

## Table 5
| المتطلب | الصياغة الاستشارية |
| --- | --- |
| Platform, not Website-only | فصل Intelligence Core عن صفحات الويب بحيث يخدم Web/Mobile/API/Widgets/B2B/third-party systems. |
| Multi-Tenant Institutional Architecture | Organizations, Teams, Roles, RBAC, API credentials, usage metering, audit logs, entitlements, tenant isolation. |
| Entitlement Engine | سياسة مركزية للـFREE/PRO/ELITE/QUANT/Institutional بدل شروط مبعثرة داخل الكود. |
| Metering | قياس API calls, intelligence requests, signals, alerts, data consumption, heavy compute. |
| Unit Economics Telemetry | ربط العميل/الشريحة بتكلفة Compute/Data/AI/API وGross Margin. |
| Cost Attribution | إسناد التكلفة إلى Engine/Data provider/AI operation. |
| Feature-Level Economics | Feature → Usage → Retention → Conversion → Revenue → Infrastructure Cost. |
| Experimentation Platform | Feature flags + cohorts + controlled experiments. |
| Reproducibility Architecture | إعادة إنتاج أي Intelligence من Data/Version/configuration/timestamp/model. |
| Intelligence Provenance | Sources → transformations → features → engines → signal → decision. |
| Unified Confidence Architecture | Model confidence + Data confidence + Signal agreement + Historical reliability + Uncertainty + Calibration. |
| Event-Driven Architecture | تحويل Market Events إلى events يستهلكها Web/Mobile/API/Alerts/Institution/Evidence/Analytics. |
| Portable Intelligence Objects | Asset + timestamp + evidence + confidence + provenance + expiry/freshness + entitlement. |
| Developer Experience | Stable contracts + versioning + SDK readiness + webhooks/event streams + docs generation + sandbox. |
| Localization Architecture | فصل content/formatting/timezones/currencies/RTL عن المنطق. |
| Privacy-by-Design | Minimization + consent/legal basis + retention + deletion + export + purpose limitation + access control. |
| Vendor Independence | Abstraction في النقاط الحرجة لتقليل lock-in غير الضروري لمزود Data/Cloud/AI واحد. |
| Exit/Acquisition Architecture | تنظيم IP/docs/contracts/secrets/infrastructure/dependencies/licenses/ADRs/evidence بحيث يكون الأصل قابلًا للفحص والنقل. |

## Table 6
| النطاق | محتواه الإلزامي |
| --- | --- |
| A. Market Data Assets | Historical prices/trades/order books/depth/spread/liquidity/slippage/volatility/volume/OHLCV/cross-exchange/funding/OI/basis/liquidations/long-short/options/DEX/bridges/stablecoins/gas/exchange health/source latency-freshness. |
| B. Proprietary Derived Data | Normalized/cleaned/deduped/time-aligned/entity-enriched/anomaly-labelled/regime-labelled/liquidity/whale/manipulation/risk/liquidation/squeeze/depeg/correlation/exchange stress/counterparty/internal flow/Sybil/wallet/smart-money/convergence/event datasets. |
| C. On-Chain Intelligence Memory | Wallet activity/clusters/relationships/entity attribution/whale histories/age/accumulation/distribution/dormancy/exchange flows/cross-chain/bridges/token movements/smart-money/contracts/suspicious/dusting-Sybil. |
| D. Market Event Knowledge Base | Crashes/pumps/flash crashes/squeezes/liquidation cascades/depegs/outages/hacks/whale events/liquidity withdrawals/funding-OI anomalies/correlation breaks/extreme volatility/manipulation-like patterns/macro events/network congestion/protocol failures; Before→During→After. |
| E. Signal Registry | ID/timestamp/asset/type/input state/sources/version/strength/confidence/horizon/supporting/contradicting/regime/data quality/freshness/outcome. |
| F. Prediction Ledger | Prediction/timestamp/horizon/probability/confidence/inputs/model version/market condition/outcome/error/correctness/calibration. |
| G. Decision Ledger | Decision ID/time/action/inputs/evidence/conflicts/confidence/risk/version/user context if lawful/outcome. |
| H. Outcome Intelligence | Correct/incorrect/partial/false positive/false negative/missed events/lead time/error magnitude/performance by asset/exchange/regime/volatility/liquidity/horizon. |
| I. Confidence & Calibration | Predicted confidence vs actual success; by engine/asset/regime/horizon; deterioration/drift/correction. |
| J-K. Proprietary Features & Signal Combinations | Derived/behavioral/liquidity/whale/order-book/cross-market/cross-chain/risk/temporal/composite/regime-specific features + correlations/dependencies/conflicts/sequencing/timing/decay/lead-lag/cross-asset-chain-exchange combinations. |
| L-M. Model & Regime Assets | Models/checkpoints/training-validation-golden datasets/features/hyperparameters/calibration/ensembles/regime models/performance/drift/failure/adversarial/benchmarks + market-regime intelligence. |
| N. Failure Intelligence | Wrong predictions/bad signals/false alarms/missed events/bad data/source/algorithm/model/latency/infrastructure/user-impact/root-cause/fix/recurrence. |
| O-P. User & Product Intelligence | Preferences/assets/analysis/alerts/risk/expertise/depth/usage/search/explanation/portfolio/notification + feature usage/retention/abandonment/session/activation/conversion/upgrade/churn/demand/shared insights/valuable alerts/payment-retention links/friction/UX failure. |
| Q-R. Commercial & Distribution Intelligence | ARPU/ARPPU/MRR/ARR/churn/retention/LTV/CAC/payback/tier migration/pricing/trials/cancellations/reactivation/geography/segment + channel/creator/affiliate/referral/viral/share/content/SEO/backlinks/search/community/brand/media relationships. |
| S-U. Network, Institutional & Switching Assets | Community/user-generated/collaborative intelligence/reputation/benchmarking + APIs/data feeds/workflows/custom reports/SLA/support/procurement/DD/playbooks/reference customers/case studies + saved configs/historical dashboards/alerts/watchlists/settings/integrations/audit history. |
| V-W. Trust & Operational Know-how | Prediction/availability/security/incident/SLA/claims/audit/reviews/case studies/research/media/brand + runbooks/incidents/recovery/scaling/exchange/data-provider/deploy/capacity/traffic/cost/reliability/security response. |
| X-Z. Engineering, Security & Data-Quality Intelligence | Code/architecture/components/libraries/pipelines/observability/testing/simulation/benchmark/deploy/security/feature flags/experimentation/data quality/model validation + attack/abuse/fraud/bots/auth/API threats + source reliability/latency/errors/schemas/missing/corrupt/disagreement/quality scoring. |
| AA-AC. IP, Experiment & Research | Proprietary algorithms/datasets/metrics/scoring/classifications/signals/models/graphs/benchmarks/trade secrets/patent candidates/copyright/brand + A/B/failed/successful/pricing/UX/alert/model/feature/growth/onboarding experiments + research corpus. |
| AD-AG. Human, Brand, Customer & Financial Capital | Expertise/relationships/processes + brand/direct traffic/social/newsletter/community/creators/media/search/advocacy/word-of-mouth + users/subscribers/institutions/pipeline/relationships + revenue/MRR/ARR/margins/cash-flow/cohorts/renewals/expansion/contracts. |
| AH-AK. DD, Compliance, Ecosystem & Developers | Capability/test/security/pen/load/chaos/availability/model/data lineage/claims/incidents/compliance/ADR/release/independent-review evidence + privacy/consent/retention/access/audit/policy/risk/vendor/regulatory response + integrations/API customers/apps/widgets/partners/SDKs/dev accounts/community libs/external apps. |
| AL. Intelligence About BLACKDARK Itself | Demand/capacity/revenue/churn/LTV/conversion/fraud/infrastructure-cost/market expansion/geographic demand/segment opportunity intelligence. |

## Table 7
| النظام | المطلوب |
| --- | --- |
| Market State Library | حفظ حالة السوق الكاملة عند اللحظات المهمة وربطها بأقرب الحالات التاريخية. |
| Counterfactual Intelligence | تقييم ما كان سيحدث تحت قرارات بديلة BUY/SELL/WAIT/thresholds/timing مختلفة. |
| Opportunity-Missed Ledger | تسجيل الأحداث/الفرص التي حدثت ولم يكتشفها النظام مع سبب الفقد والإصلاح وحالة regression. |
| Hard-Case Library | Source conflicts, low confidence, model disagreement, novel events, missing data, regime changes. |
| Uncertainty Intelligence | Data/model/source/regime/novel-event uncertainty؛ النظام يتعلم متى لا يعرف. |
| Data Disagreement Corpus | حفظ اختلاف المصادر والـconsensus ثم تقييم من كان أدق لاحقًا. |
| Intelligence Half-Life | قياس creation → peak usefulness → decay → expiry لكل Signal. |
| Lead-Time Advantage | قياس كم سبق النظام الحدث، لا مجرد هل أصاب. |
| Intelligence Uniqueness Score | تمييز Commodity Intelligence عن Proprietary Intelligence. |
| Capability Economic Ledger | Development/operating/data/compute cost + usage/retention/conversion/revenue/uniqueness/effectiveness → Capability ROI. |
| Capability Dependency Graph | Data → Feature → Engine → API → UI مع impact propagation عند تعطل dependency. |
| Metric/Truth Registry | تعريف مركزي لكل Net Edge/Confidence/Risk/Whale Score وغيرها مع formula/sources/version/owner/tests. |
| Claims Registry | Claim → Evidence → Test → Date → Version → Valid/Expired. |
| Reproducible Intelligence Receipts | Insight ID/timestamp/data snapshot/source/version/output/confidence/evidence hash/outcome. |
| Golden Benchmark Suite | Baseline ثابت ومتنامٍ يغطي normal/bull/bear/crash/squeeze/depeg/manipulation-like/bad data/outage/extreme volatility. |
| Adversarial Market Laboratory | اختبارات fake-volume-like/spoofing-like/corruption/latency/conflicting exchanges/whale noise/liquidity disappearance. |
| Champion-Challenger Shadow System | Champion production + challenger models in shadow; promotion only by evidence. |
| Automated Drift Memory | Performance over time → degradation → regime → cause. |
| Human Override Ledger | AI said X → expert chose Y → outcome Z، عند وجود أساس قانوني/موافقة مناسبة. |
| User Question Corpus | أنماط الأسئلة والاحتياجات بطريقة آمنة وغير حساسة قدر الإمكان. |
| Unmet Demand Ledger | Zero-result searches/feature requests/unsupported assets/exchanges/missing analyses. |
| Institutional Requirement Corpus | كل متطلب B2B/Fund يُسجل حتى لو لم يتم البيع. |
| Lost Customer Intelligence | Visitor/lead funnel + objection/lost reason. |
| Pricing Intelligence | Price/conversion/segment/geography/plan/retention/upgrade/downgrade. |
| Distribution Knowledge Graph | Creator → Content → Community → Visitor → User → Subscriber → Referral. |
| Viral Content Genome | Card/chart/insight topic/format/event/time/CTR/shares/signups/paid conversions. |
| SEO Intelligence Corpus | Queries/rankings/CTR/pages/backlinks/conversions/search intent. |
| Integration Graph | Customer → API → endpoints → workflows → usage. |
| Revenue Quality Dataset | Recurring revenue/retention/expansion/concentration/gross margin/cohort durability/refunds/failed payments. |
| Living Acquisition Data Room | Architecture/IP/Security/Tests/Data rights/Models/Performance/Customers/Financials/Incidents/Contracts/Risks/Compliance evidence. |

## Table 8
| نوع الدليل | التعريف |
| --- | --- |
| BACKTESTED | المحرك الحالي اختُبر على الماضي بطريقة point-in-time دون الاطلاع على المستقبل. |
| SIMULATED | سيناريو مصطنع/Stress؛ يجب أن يبقى موسومًا بوضوح ولا يختلط بالواقع التاريخي. |
| SHADOW/LIVE FORWARD | قرار/توقع صدر لحظيًا قبل معرفة النتيجة على بيانات السوق الحي دون تنفيذ مالي. |
| PRODUCTION VERIFIED | سجل استخدام إنتاجي حقيقي بعد الإطلاق. |

## Table 9
| الأصل | التنفيذ |
| --- | --- |
| Immutable/Tamper-Evident Evidence Ledger | Timestamp + version + hashes/append-only controls المناسبة للتوقعات المهمة. |
| Forward Track Record | تشغيل أهم المحركات Shadow 24/7 من الآن؛ Prediction/Signal → timestamp/inputs/version/confidence/horizon → outcome. |
| Model & Algorithm Genealogy | شجرة إصدارات، سبب التغيير، benchmark before/after، الأداء حسب regime. |
| Reliability Track Record | Uptime, latency p50/p95/p99, freshness, error rates, recovery time, incidents, capacity, provider failures. |
| Security Track Record | Vulnerabilities, remediation time, dependency incidents, abuse attempts, tests, pentests, secret rotations, access reviews, security releases. |
| Evidence Room | Architecture/Data/Algorithm/Security/Performance/Reliability/Model/IP evidence + Commercial evidence لاحقًا. |
| Institutional Readiness History | تاريخ reviews والإغلاقات وإعادة الاختبارات عبر Security/Architecture/Performance/Data/AI/Financial Accuracy. |
| Source Reliability Intelligence | تعلم موثوقية كل مصدر حسب الظروف والـvolatility والlatency/error profile. |

## Table 10
| المكوّن | الهدف |
| --- | --- |
| Time-to-Value Instrumentation | Signup → first value moment. |
| Activation Definition | تعريف Activated User على أساس قيمة فعلية، لا Registration. |
| Retention Architecture | Watchlists/personalized intelligence/alerts/market changes/saved workspaces/historical comparisons. |
| Viral Object Architecture | Signal/Risk/Whale/Market/Prediction cards + public reports/widgets، مع permanent URL/timestamp/branding/evidence/share metadata. |
| Attribution Architecture | Content/Creator/Referral/Widget → Visitor → Signup → Activation → Paid → Retention. |
| Referral Graph | شجرة توزيع تحترم الخصوصية وتكشف communities/super-spreaders/viral objects. |
| Public/Private Intelligence Boundary | Public/shareable / Free / Premium / Institutional / Sensitive/Internal. |
| Programmatic Public Intelligence Pages | صفحات حقيقية ذات قيمة لكل Asset/Metric/Event؛ تجنب SEO spam. |
| Embeddable BLACKDARK | Widgets/charts/market pulse/risk indicators كعقد توزيع خارجية. |
| Public Intelligence Reputation | Research/indices/live pages/charts/widgets قبل الإطلاق الكامل لبناء authority. |
| SEO Authority | Domain history, research pages, backlinks, citations, branded search تبدأ قبل Launch Day. |

## Table 11
| التصنيف | ما يندرج تحته |
| --- | --- |
| BUILD / DESIGN NOW | Platform separation، multi-tenancy foundations، entitlements، metering، provenance/versioning، privacy/data rights/IP provenance، event-driven/portable intelligence contracts، registries الأساسية، evidence architecture، experiment/feature flags. |
| START ACCUMULATING NOW | Live shadow forward record، historical backfill/replay، signal/prediction/decision/outcome/failure ledgers، source reliability، benchmarks، security/reliability evidence، research/IP، architecture/capability/design decision history. |
| DESIGN NOW - BUILD/EXPAND LATER | Developer ecosystem، public pages، widgets، full institutional integrations، advanced machine-readable external product، network effects. |
| REQUIRES REAL USERS | Retention/churn/conversion/user behavior/questions/unmet demand/referrals/viral genome/pricing willingness-to-pay/customer cohorts. |
| REQUIRES INSTITUTIONS | Enterprise workflows/SLA history/procurement/DD responses/reference customers/case studies/switching costs. |
| REQUIRES SCALE/TIME | Brand equity، community reputation، mature distribution network، long forward track record، multi-year trust/operational history. |
| DO NOT COLLECT / BUILD BY DEFAULT | بيانات بلا غرض واضح، بيانات بلا حق استخدام، telemetry حساسة غير لازمة، architecture ضخمة لا يدعمها use case، أو features شكلية لا تخلق قيمة أو evidence. |

## Table 12
| الجولة | نوع المراجعة | النتيجة |
| --- | --- | --- |
| الجولة الأولى | Source ingestion | تم نسخ التقارير إلى ملفات مرجعية مستقلة وحساب counts/hashes. لم يتم الاعتماد على الذاكرة وحدها. |
| الجولة الثانية | Structural coverage | تم التحقق آليًا من العلامات الفارقة: R1 vaults/30 systems، R2 20 priorities/10 immediate actions، R3 30 design items/7 machines، R4 A-AL/15 strategic assets/Gate، R5 4 evidence classes/12 core items. |
| الجولة الثالثة | Preservation | تم إدراج كل تقرير كاملًا في ملحق مستقل داخل نفس الوثيقة. هذا هو الضمان الأساسي ضد السهو أو الدمج المحرف. |
| الجولة الرابعة | Semantic organization | تمت إعادة الصياغة في الأقسام 1-16 مع الحفاظ على القيود المميزة: timing، privacy، rights، evidence classes، no-fake-track-record، platform separation، acquisition readiness. |
| الجولة الخامسة | Reverse traceability + visual QA | تم التأكد من وجود كل تقرير في الملاحق، وإجراء فحص نصي بعد إنشاء DOCX، ثم رندر صفحات الوثيقة ومراجعة التنسيق قبل التسليم. |

## Table 13
| # | مستوى الفحص | الحكم | العيب المؤسسي | الإغلاق المضاف |
| --- | --- | --- | --- | --- |
| 1 | سلامة المصدر والسلطة | قوي جدًا | المصدر محفوظ، لكن كان يلزم تثبيت هرم السلطة مع v5 ومنع إنشاء SSOT موازٍ. | تمت إضافة Authority & Scope صريحة. |
| 2 | المتطلبات والحوكمة | قوي مفاهيميًا / ناقص إجرائيًا | المتطلبات كثيرة لكن ليست كلها بصيغة Normative IDs قابلة للتتبع. | إضافة DSR-001…DSR-024 وربطها ببوابة الإغلاق. |
| 3 | جودة البيانات والحقوق والتخزين | قوي جدًا / يحتاج عقودًا تنفيذية | حقوق، lineage وprivacy موجودة؛ ينقص Data Contract/Retention/Schema evolution/quality SLO التفصيلي. | إضافة Data Asset Contract وStorage Lifecycle. |
| 4 | النزاهة الكمية والـReplay/Track Record | قوي جدًا | الفصل بين Backtest/Shadow/Production ممتاز؛ ينقص إثبات PIT completeness ومنع survivorship/revision leakage. | إضافة PIT Evidence Contract وReplay Reperformance. |
| 5 | AI/Models/Derived Intelligence | قوي | Genealogy/Drift/Champion موجودة؛ promotion/rollback ومعيار المخاطر غير مغلق داخل الوثيقة التخصصية. | الإحالة إلى v5 + Domain Model Asset Contract. |
| 6 | الأمن/الاعتمادية/التشغيل | جيد جدًا | Security/Reliability histories موجودة؛ ينقص ربطها بتخزين الأدلة، recovery، integrity وretention. | إضافة Evidence Storage, restore, tamper-evidence, SLO/RPO/RTO bindings. |
| 7 | المنتج/الاستحواذ/القيمة المتراكمة | ممتاز استراتيجيًا | القيمة موصوفة، لكن يلزم proof-of-value وasset valuation/rights/readiness state قابل لإعادة الأداء. | إضافة Asset Value Ledger + Acquisition Reperformance Pack. |

## Table 14
| ID | الشدة | العيب | المخاطرة | الحل المؤسسي | معيار الإغلاق |
| --- | --- | --- | --- | --- | --- |
| D-01 | حرج | غياب عقد موحد لكل أصل بيانات مادي | قد يوجد Source/Lineage دون contract كامل للغرض، المستهلكين، الحقوق، freshness، retention، fallback. | Data Asset Contract إلزامي + owner + schema/version + rights + quality SLO + retention + fallback + evidence. | لا Dataset مادية بلا contract قابل للتتبع. |
| D-02 | حرج | Point-in-Time integrity غير قابلة لإعادة الأداء بالكامل | الوثيقة تمنع رؤية المستقبل، لكنها لا تفرض proof pack موحدًا لكل replay. | PIT Evidence Contract: knowledge cutoff, event/ingest time, revision policy, universe snapshot, survivorship controls, code/data SHA. | إعادة تشغيل حالة benchmark من snapshot تعطي نفس النتيجة ضمن tolerance معلن. |
| D-03 | عالٍ | Schema evolution غير محكومة بوضوح | تغير schemas قد يفسد historical replay أو lineage بصمت. | Schema Registry + compatibility policy + migration/backfill record + consumer impact test. | لا breaking schema بلا migration evidence وconsumer reconciliation. |
| D-04 | عالٍ | Data retention/deletion tiers غير محددة | وجود retention principle لا يحدد ماذا يحتفظ به لكل فئة ولماذا. | Retention Class لكل dataset/evidence/user telemetry + legal/business basis + deletion/anonymization proof. | كل أصل مادي له retention class وexpiry/deletion behavior. |
| D-05 | حرج | حقوق البيانات لا ترتبط آليًا بمسارات الاستخدام | قد تكون الحقوق موثقة لكن reuse/API/training/resale لا يُمنع تقنيًا. | Rights Enforcement Tags على datasets + policy checks قبل export/training/API/licensing. | اختبار سلبي يثبت منع الاستخدام غير المسموح. |
| D-06 | عالٍ | Provenance يصف السلسلة لكنه لا يفرض immutability/version binding | قد يتغير مصدر/تحويل دون ربط output بهوية دقيقة. | Immutable Intelligence Receipt يربط source snapshot + transform + feature + model/rule + config + output + evidence hash. | كل claim/insight مادي قابل لإعادة التكوين من receipt. |
| D-07 | عالٍ | Outcome truth غير مفصول عن prediction truth بما يكفي | Evaluator قد يتغير بعد إصدار prediction. | Versioned Outcome Definition Registry + outcome evaluator version + correction history. | إعادة تقييم قديم لا يمحو النتيجة السابقة؛ يسجل correction/version. |
| D-08 | عالٍ | Missed-opportunity denominator غير معرف | تسجيل missed events ممتاز لكن بدون universe واضح قد يصبح recall غير قابل للمقارنة. | Opportunity Universe Contract لكل نوع حدث: eligibility window, detection rule, ground truth, exclusions. | Recall/false-negative metrics لها denominator قابل للإثبات. |
| D-09 | عالٍ | Entity/Wallet attribution confidence غير محكوم | Knowledge Graph قد يراكم علاقات خاطئة كحقيقة. | Entity Assertion Contract: assertion type, source, confidence, evidence, expiry, contradiction, human review for high-impact. | لا attribution مادي بلا confidence/provenance/validity state. |
| D-10 | متوسط-عالٍ | Derived metric IP/value قد تختلط مع commodity transforms | وجود Uniqueness Score وحده غير كافٍ. | Derived Asset Classification: commodity / configured / proprietary / trade-secret candidate + evidence of novelty/value. | كل derived asset مادي مصنف وله owner/rights/value evidence. |
| D-11 | عالٍ | تكلفة التخزين/الحوسبة غير مرتبطة بسياسة lifecycle | Cost Attribution موجود لكن لا يحدد hot/warm/cold/delete tiers. | Storage Tiering Policy حسب access frequency, replay need, evidence criticality, cost and rights. | كل dataset لها tier + migration trigger + cost guard. |
| D-12 | حرج | Backup ≠ Restore evidence | الوثيقة تسجل reliability لكن لا تفرض استعادة الأصول الحرجة. | RTO/RPO + backup/restore test + integrity checks للـledgers/registries/evidence. | Restore evidence حديث ومربوط بنسخة/بيئة. |
| D-13 | عالٍ | Tamper-evident evidence غير محدد بآلية تحقق | ذكر hashes/append-only صحيح لكنه لا يحدد validation chain. | Evidence Integrity Manifest: chained hashes/immutable store controls, signer/producer identity, timestamp, verification procedure. | مراجع مستقل يتحقق من عدم العبث دون ذاكرة المطور. |
| D-14 | عالٍ | Data quality score قد يصبح رقمًا تجميليًا | لا يوجد contract يحدد مكونات score وتأثيرها على decision. | Quality Dimensions + thresholds + fail/degrade policy + propagation إلى confidence/availability. | Stale/bad data لا تمر كـlive intelligence دون downgrade صريح. |
| D-15 | متوسط-عالٍ | Experiment/Model promotion يحتاج criterion مسبق | الوثيقة تقول promotion by evidence لكن لا تحدد pre-registered gate. | Promotion Record: hypothesis, baseline, sample/regime coverage, metric, non-regression, rollback trigger, approver. | لا promotion بلا gate مسبق وreproducible evidence. |
| D-16 | عالٍ | Living Data Room لا يحدد completeness/freshness state | وجود الملفات لا يعني DD-ready. | Data Room Index: artifact owner, scope, version, freshness, evidence strength, exceptions, residual risk, expiry. | كل مادة DD لها state وصلاحية وإعادة أداء. |
| D-17 | متوسط | Asset value غير قابل للقياس بصورة موحدة | الـFlywheel قوي لكن بعض الأصول قد تتضخم بلا أثر. | Asset Value Ledger: uniqueness, usage, accuracy/effectiveness, cost, rights, revenue/retention contribution, strategic reuse. | مراجعة دورية: keep/invest/deprecate/stop collecting. |
| D-18 | عالٍ | التمييز بين بيانات حقيقية ومشتقة/مصطنعة يحتاج lineage label دائم | الوثيقة تفصل Evidence Classes لكن label يجب أن ينتقل مع كل derived object. | Evidence-Origin Label إلزامي ومتوارث عبر transformations. | لا يمكن أن يتحول SIMULATED/BACKTESTED إلى VERIFIED PRODUCTION عبر transform. |
| D-19 | عالٍ | تصحيح البيانات التاريخية قد يغير الماضي بصمت | Provider corrections/reorgs/backfills قد تغير benchmark. | Bitemporal/correction policy: observed-at vs effective-at + correction ledger + reproducibility snapshot. | كل correction مادي قابل للتتبع دون محو النسخة المستخدمة سابقًا. |
| D-20 | متوسط-عالٍ | الـKnowledge Graph يحتاج conflict resolution lifecycle | مصادر متعددة قد تعطي علاقات/كيانات متعارضة. | Assertion conflict states + source reliability + adjudication/expiry + consumer rules. | لا تُعرض حقيقة مؤكدة إذا كانت الحالة CONFLICTED/LOW_CONFIDENCE. |

## Table 15
| Requirement ID | النص الحاكم |
| --- | --- |
| DSR-001 | كل Dataset/Stream مادي يجب أن يملك Data Asset Contract canonical. |
| DSR-002 | كل Data Asset Contract يحدد owner, purpose, consumers, schema/version, event time, ingest time, freshness, completeness, validity, uniqueness, reconciliation, missing/corrupt behavior, lineage, rights, retention, fallback, monitoring, evidence. |
| DSR-003 | كل historical replay/backtest مادي يملك Point-in-Time Evidence Contract يمنع look-ahead/future/revision leakage وsurvivorship bias حيث ينطبق. |
| DSR-004 | كل benchmark/replay قابل لإعادة الأداء من data snapshot + code/model/rule/config version + universe snapshot + oracle. |
| DSR-005 | كل source/dataset له Rights Profile machine-enforceable عند storage, derived use, training, redistribution, API, resale/licensing. |
| DSR-006 | كل schema مادي يخضع versioning وcompatibility/migration policy وconsumer impact verification. |
| DSR-007 | كل تصحيح تاريخي مادي يسجل observed-at/effective-at/corrected-at ولا يمحو snapshot المستخدم سابقًا. |
| DSR-008 | كل Signal/Prediction/Decision مادي يصدر Intelligence Receipt قابل لإعادة التحقق. |
| DSR-009 | Outcome definition/evaluator version جزء من lineage ولا يجوز إعادة كتابة history بلا correction record. |
| DSR-010 | Missed-opportunity/recall metrics لا تُحسب دون Opportunity Universe Contract محدد. |
| DSR-011 | كل entity/relationship assertion مادي يحمل source, confidence, validity, expiry, conflict state, evidence. |
| DSR-012 | Evidence origin label BACKTESTED/SIMULATED/FORWARD_SHADOW/VERIFIED_PRODUCTION/INDEPENDENT يبقى متوارثًا عبر المشتقات. |
| DSR-013 | SIMULATED أو BACKTESTED لا يمكن ترقيتهما دلاليًا إلى VERIFIED_PRODUCTION بسبب aggregation أو transformation. |
| DSR-014 | كل dataset/ledger مادي له retention class وstorage tier وdeletion/anonymization behavior. |
| DSR-015 | كل stateful critical registry/ledger له RTO/RPO وrestore evidence وفق v5. |
| DSR-016 | Evidence Ledger المادي يجب أن يكون tamper-evident وقابلًا للتحقق بخطوات موثقة. |
| DSR-017 | Data-quality failure يجب أن يؤثر صراحة في availability/confidence/degradation؛ لا silent stale data. |
| DSR-018 | Champion/Challenger promotion لأي model/algorithm ذي أثر مادي يخضع pre-defined promotion gate وrollback trigger. |
| DSR-019 | كل derived intelligence asset يصنف commodity/configured/proprietary ويملك owner/rights/value evidence. |
| DSR-020 | Asset Value Ledger يربط cost + usage + effectiveness + uniqueness + rights + monetization/retention/strategic reuse. |
| DSR-021 | Living Data Room له index canonical يبين completeness, freshness, evidence strength, exceptions, residual risk, owner. |
| DSR-022 | Claims عن accuracy/coverage/lead-time/uniqueness/value لا تُعرض دون claim→evidence→version→validity chain. |
| DSR-023 | لا تُجمع بيانات مستخدم/سوق لمجرد إمكانية الجمع؛ كل collection يحتاج purpose, rights/legal basis where applicable, minimization, retention and deletion. |
| DSR-024 | بوابة PROPRIETARY ASSET ACCUMULATION & DATA FLYWHEEL لا تغلق إلا إذا كانت المتطلبات المادية أعلاه قابلة لإعادة الأداء وبدون Red Flag غير محلول. |

## Table 16
| المجال | الحد الأدنى الإلزامي |
| --- | --- |
| Identity | dataset/stream ID, canonical name, owner, steward where needed, business purpose |
| Authority & Rights | source, contract/license reference, permitted storage/retention/derived works/training/API/resale/redistribution |
| Temporal | event_time, ingest_time, observed_at, effective_at, correction/revision semantics, timezone/clock assumptions |
| Schema | schema version, compatibility class, required/optional fields, units, precision, null/unknown semantics |
| Quality | freshness, completeness, validity, uniqueness, reconciliation, missing/corrupt thresholds, source disagreement |
| Lineage | raw source → normalization → enrichment → feature/model/engine → output consumers |
| Lifecycle | hot/warm/cold/archive/delete tier, retention, deletion/anonymization, legal/business hold if applicable |
| Failure behavior | fallback, degrade, stale/unavailable behavior, impact propagation to capabilities |
| Security | classification, access roles, encryption expectations, auditability, sensitive-field handling |
| Evidence | tests, quality monitoring, current evidence state, last validation, exceptions/residual risk |

## Table 17
| Tier | الاستخدام | هدف التصميم | شرط الانتقال |
| --- | --- | --- | --- |
| HOT | بيانات حالية ومسارات قرار نشطة | وصول منخفض الكمون، freshness عالية | ينتقل وفق age/usage/cost/rights |
| WARM | history متكرر للبحث/replay | queryable + أقل تكلفة | ينتقل عند انخفاض الاستخدام |
| COLD/ARCHIVE | evidence/history طويل الأجل | immutability/retrievability أهم من latency | حسب retention/right/restore need |
| DELETE/ANONYMIZE | لا غرض مستمر أو انتهت الحقوق/المدة | إزالة أو anonymization مثبتة | deletion evidence + lineage impact |

## Table 18
| المرجع | الاستخدام الصحيح | الرابط الرسمي |
| --- | --- | --- |
| ISO/IEC 25010:2023 | Product quality model — nine quality characteristics for specification, measurement and evaluation. | https://www.iso.org/standard/78176.html |
| ISO/IEC 25012:2008 | Data quality model — requirements, measures and evaluation of structured data quality. | https://www.iso.org/standard/35736.html |
| ISO/IEC/IEEE 29148:2018 | Requirements engineering — lifecycle requirements processes and information items. | https://www.iso.org/standard/72089.html |
| NIST CSF 2.0 | High-level cybersecurity risk outcomes; does not prescribe one implementation. | https://www.nist.gov/publications/nist-cybersecurity-framework-csf-20 |
| NIST SP 800-218 SSDF v1.1 | Secure software development practices and root-cause prevention. | https://csrc.nist.gov/pubs/sp/800/218/final |
| NIST AI RMF 1.0 | Voluntary, non-sector-specific framework for managing AI risks. | https://www.nist.gov/publications/artificial-intelligence-risk-management-framework-ai-rmf-10 |
| Google SRE — SLO practice | Industry practice for SLI/SLO/error-budget operational discipline; not an ISO standard. | https://sre.google/sre-book/service-level-objectives/ |


---

# الملحق التنفيذي والاستراتيجي المدمج — Data Extra v3 Corrected

> **حالة الحوكمة:** المحتوى التالي مدمج كمكوّن استراتيجي/منتجي/تنفيذي مكمل داخل المرجع التخصصي. لا ينشئ SSOT موازيًا، ولا يثبت التنفيذ في الكود. أي mapping إلى 1–826 أو PASS/Live/Assurance يظل تابعًا للـSSOT التقني والأدلة الفعلية.

# ملف البيانات الإضافي — النسخة المؤسسية المصححة والقابلة للتنفيذ

**الحالة:** CORRECTED / SOURCE-VERIFIED / EXECUTION-READY-AS-STRATEGIC-REGISTER

> هذا الملف **ليس دليلًا على أن عناصره منفذة في الكود**. هو سجل استراتيجي/منتجي/حوكمي مصحح يحدد ما يجب بناؤه أو قياسه أو حوكمته، وما الدليل المطلوب قبل أي claim. أي ادعاء تنفيذ أو PASS يجب أن يأتي من SSOT التقني الحالي للمشروع، والـRTM، ومسار التنفيذ/المستهلك، والاختبارات، والـSHA/evidence؛ لا من هذا الملف وحده.

## 0. قواعد الحقيقة وعدم الادعاء

- **[FACT — SOURCE]** المصدر الفعلي الذي تمت مراجعته هو `ملف البيانات الاضافى.md`، ويحتوي بنيويًا على: **20 نقطة أصلية + 40 ميزة/قدرة من الفكرة رقم 1 + 7 إضافات استراتيجية + 8 تصنيفات عوامل + 5 أولويات**. هذه الفئات تتداخل دلاليًا؛ لذلك **لا تُجمع كعدد قدرات فريدة**.
- **[FACT — SOURCE]** الادعاء السابق `20/20 + 68/68 + 42/42 + 40/40` لا يطابق بنية المصدر الحالي، ولذلك أُلغي نهائيًا.
- **[FACT — REVIEW]** السجل المشتق يحتوي 73 سجلًا Canonical، لكنه **ليس 73 قدرة**: التصنيف المصحح هو **40 Capability + 17 Control/Governance + 9 Asset + 4 Metric + 3 Operating Model/Strategy = 73**.
- **[RULE]** لا يُستخدم أي Record غير Capability لزيادة عداد القدرات.
- **[RULE]** لا يُستخدم `NOW` أو `KEEP` كدليل تنفيذ. التنفيذ الفعلي يحتاج binding/consumer path/oracle/tests/source SHA/evidence.
- **[RULE]** لا تُخترع خريطة IDs 1–826. أي mapping غير مثبت من الـ826 SSOT الحالي يبقى `UNVERIFIED_PENDING_826_SSOT_RECONCILIATION`.
- **[RULE]** أي اعتماد خارجي أو vendor أو حقوق بيانات أو ترخيص: لا شراء ولا اشتراك تلقائي، ولا claim availability/rights قبل التحقق.

### بصمات مواد العمل

- Working source snapshot SHA-256: `b39ae5276789b891591a9d7e061356fcc0c2475757f6d1bac1e00bf682adb66f`
- Previous institutional file snapshot SHA-256: `4025726fca3b69879c00e5c99cb1bcb2abb42e30c5ea27f449a2ff23d47e6341`

## 1. المراجعة الخماسية المنفذة

| طبقة المراجعة | ما تم فحصه | قاعدة القبول | النتيجة |
|---|---|---|---|
| 1 — Source Integrity | بنية المصدر، العدّ، العناوين، الفئات | لا claim coverage يخالف المصدر | PASS بعد تصحيح العدّ وإلغاء 170/170 القديم |
| 2 — Taxonomy & Counting | Capability/Asset/Control/Metric/Strategy | كل نوع في عداد مستقل | PASS: 40/17/9/4/3 |
| 3 — Evidence & Standards | كل claim، بوابة دليل، attribution | لا template evidence؛ لا نسبة معيارية زائفة | PASS بعد استبدال البوابات العامة بمتطلبات فردية |
| 4 — Product/Execution/Market | Daily pull، user outcome، ترتيب التنفيذ، dependencies، competitive reality | الاستراتيجية لا تساوي قيمة مستخدم؛ البناء لا يساوي proof | PASS بعد إضافة W0/W1 وفصل evidence-later |
| 5 — Reverse Reconciliation | المصدر→Canonical، التكرار، 826 mapping، claims | كل مصدر له disposition؛ لا mapping مختلق | PASS داخل هذا المصدر؛ 826 mapping يبقى صريحًا غير مثبت حتى repo reconciliation |

## 2. الإطار المؤسسي المستخدم

يُفصل بوضوح بين **[STD] معيار رسمي** و**[FRAMEWORK] إطار مهني** و**[POLICY] قرار BLACKDARK**:

| المرجع | الاستخدام الصحيح هنا | ما لا يدعيه الملف |
|---|---|---|
| **[STD] ISO/IEC 25010:2023** | Product quality model؛ تحديد/قياس/تقييم خصائص جودة المنتج | لا يعني certification ولا يفرض أرقام أداء خاصة بـBLACKDARK |
| **[STD] ISO/IEC 25019:2023** | Quality-in-use؛ ربط الجودة بسياق الاستخدام ونتيجة stakeholder | لا يعرّف "wow" كرقم معياري؛ مؤشرات الانبهار/الاعتماد أدناه [POLICY/METRIC] |
| **[STD] ISO/IEC/IEEE 29148:2018** | requirements engineering وtraceability/information items | لا يفرض أسماء ملفات أو أعمدة RTM بعينها |
| **[STD] ISO/IEC/IEEE 12207:2026** | life-cycle processes عبر التطوير/التشغيل/الصيانة | لا يفرض sequence خطيًا واحدًا ولا methodology بعينها |
| **[STD] ISO/IEC/IEEE 29119-2:2021** | test processes عبر نماذج دورة الحياة | لا يفرض test suite موحدة لكل Record بلا مراعاة المخاطر |
| **[STD] ISO/IEC 25012:2008** | data quality requirements/measures/evaluation | لا يثبت جودة dataset بعينه دون قياس فعلي |
| **[STD] ISO/IEC 27001:2022** | ISMS risk-management requirements | لا يعني أن BLACKDARK حاصل على ISO certification |
| **[STD] ISO/IEC 27017:2026 / 27018:2025** | cloud-security guidance / PII protection حيث ينطبق | لا تنطبق تلقائيًا على كل Record |
| **[FRAMEWORK] NIST AI RMF 1.0** | AI risk management والثقة والمراقبة حسب السياق | voluntary framework؛ لا يساوي certification |
| **[FRAMEWORK] NIST Privacy Framework** | enterprise privacy-risk management | لا يحل محل المتطلبات القانونية حسب الولاية |
| **[FRAMEWORK] OWASP ASVS 5 / API Security Top 10:2023** | verification/security-risk reference للتطبيقات والـAPIs | لا يساوي compliance claim مستقل |
| **[FRAMEWORK] AICPA Trust Services Criteria** | control criteria للأمن/التوافر/سلامة المعالجة/السرية/الخصوصية | لا يعني SOC 2 بدون attestation |

## 3. فصل الأنواع والعدّ الصحيح

| Record Class | العدد | يدخل عداد القدرات؟ | الاستخدام |
|---|---:|---|---|
| CAPABILITY | 40 | نعم | سلوك/وظيفة مستخدم أو نظام قابلة للبناء والاختبار |
| CONTROL_OR_GOVERNANCE | 17 | لا | ضابط/حوكمة/assurance |
| ASSET | 9 | لا | أصل بيانات/IP/تشغيل/قيمة متراكم |
| METRIC | 4 | لا | قياس فقط؛ لا يبنى كميزة مستقلة |
| OPERATING_MODEL_OR_STRATEGY | 3 | لا | سياسة تشغيل/تموضع/حوكمة استراتيجية |
| **الإجمالي** | **73** | **40 فقط** | 73 سجلًا Canonical متعدد الأنواع |

> **P0/P1/P2 في النسخة السابقة أصبح "Strategic Criticality" فقط، وليس Queue تنفيذ.** ترتيب التنفيذ الفعلي موجود في `Execution Lane` أدناه حتى لا يتحول P0 العريض إلى محاولة بناء كل شيء دفعة واحدة.

## 4. الـ20 Strategic Value Drivers — محفوظة كدوافع لا كقدرات

| # | Driver | العربي | النوع | Strategic Criticality | Evidence State | Canonical Link |
|---:|---|---|---|---|---|---|
| 1 | Proven Track Record | سجل أداء موثق وقابل للتدقيق | CORE_STRATEGIC_ASSET | P0 | INFRA_NOW; FORWARD_EVIDENCE_NEEDS_TIME | A01–A08 |
| 2 | Proprietary IP / Intelligence | الذكاء والملكية الفكرية الخاصة | CORE_STRATEGIC_ASSET | P0 | NOW | B01–B09 + G01–G03 + J03 |
| 3 | Workflow Lock-in | الارتباط القيمي بسير العمل | CORE_STRATEGIC_ASSET | P0 | NOW; USER_VALUE_EVIDENCE_LATER | C02–C09 + E02/E03 |
| 4 | Institutional Trust Layer | طبقة الثقة المؤسسية | CORE_STRATEGIC_ASSET | P0 | NOW_LOCAL; LIVE/INDEPENDENT_EVIDENCE_LATER | A02/A07/A08/B09/H08/J09 |
| 5 | Distribution Moat | حاجز/ميزة التوزيع | STRATEGIC_OUTCOME/INFRA | P1 | INFRA_NOW; ADOPTION_PROOF_LATER | J07 + E01–E03 |
| 6 | Network Effects | تأثيرات الشبكة | STRATEGIC_OUTCOME/INFRA | P1 | INFRA_NOW; EFFECT_NEEDS_USERS | D01–D06 |
| 7 | Unique Data Coverage | تغطية بيانات فريدة | CORE_DATA_ASSET | P0 | NOW | J01 |
| 8 | Cross-Domain Intelligence | ذكاء عابر للمجالات | CORE_INTELLIGENCE_ASSET | P0 | NOW | B02 + G01–G03 |
| 9 | Personalization Engine | محرك التخصيص | CORE_PRODUCT_CAPABILITY | P0 | INFRA_NOW; PERSONAL_LEARNING_NEEDS_USERS | C01–C04 + B10 |
| 10 | Outcome Feedback Loop | حلقة النتائج والتعلم | CORE_LEARNING_ASSET | P0 | NOW_INFRA; OUTCOMES_ACCUMULATE | A03–A06 + J11 |
| 11 | Retention + Willingness to Pay | الاحتفاظ والاستعداد للدفع | MARKET_OUTCOME | P0 | NEEDS_USERS | MARKET_OUTCOME_ONLY |
| 12 | Recurring Revenue Quality | جودة الإيراد المتكرر | MARKET_OUTCOME | P0 | NEEDS_CUSTOMERS/REVENUE | MARKET_OUTCOME_ONLY |
| 13 | API / Embedded Platform Value | قيمة المنصة المدمجة | PLATFORM_ASSET | P0 | NOW_INFRA; ADOPTION_LATER | E01–E05 |
| 14 | Data Rights / Licensing Position | حقوق البيانات والترخيص | GOVERNANCE/DATA_ASSET | P0 | NOW | J02 |
| 15 | Vendor Independence | استقلالية الموردين | ARCHITECTURE_ASSET | P0 | NOW_LOCAL; LIVE_EVIDENCE_LATER | J04 |
| 16 | Operational Reliability | الاعتمادية التشغيلية | OPERATIONAL_ASSET | P0 | NOW_LOCAL; LIVE_G6_LATER | J05 |
| 17 | Brand + Trust Reputation | العلامة والسمعة | MARKET_OUTCOME | P1 | NEEDS_MARKET/TIME | MARKET_OUTCOME_ONLY |
| 18 | Developer Ecosystem | منظومة المطورين | PLATFORM/GROWTH_ASSET | P1 | NOW_INFRA; ECOSYSTEM_ADOPTION_LATER | J06 |
| 19 | Acquisition Readiness | جاهزية الاستحواذ | ENTERPRISE_VALUE_ASSET | P0 | NOW; EXTERNAL_ITEMS_AS_APPLICABLE | J09 + J03/J02/J05/J10 |
| 20 | Speed of Learning | سرعة التعلم | LEARNING_ASSET | P0 | NOW_INFRA; PERFORMANCE_HISTORY_LATER | J11 |

**الفصل الحاكم:** Retention/WTP، Recurring Revenue Quality، Brand/Trust Reputation هي **MARKET OUTCOMES** وليست Features؛ لا تدخل عداد القدرات ولا يُعلن اكتمالها قبل وجود evidence فعلي.

## 5. السجل Canonical المصحح — 73 سجلًا مع فصل النوع والتنفيذ

| ID | Record | العربي | Record Class | Strategic Criticality | Execution Lane | Dependency/Evidence Class | 826 Mapping |
|---|---|---|---|---|---|---|---|
| A01 | Verified Forward/Public Track Record | سجل أداء Forward/Public موثّق | CAPABILITY | P0 | W0_0_90D_CORE | LIVE/TIME | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| A02 | Pre-Outcome Timestamp & Anti-Backfill Integrity | ختم زمني قبل النتيجة ومنع الإضافة بأثر رجعي | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| A03 | Prediction–Decision–Outcome Evidence Chain | سلسلة إثبات التوقع–القرار–النتيجة | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| A04 | Automated Multi-Horizon Outcome Evaluator | مقيّم نتائج آلي متعدد الآفاق | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| A05 | Accuracy, Calibration & Regime Analytics | تحليلات الدقة والمعايرة حسب السوق/النظام | CAPABILITY | P0 | W0_0_90D_CORE | LIVE/TIME | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| A06 | Error, Correction, Abstention & Low-Confidence Ledger | سجل الأخطاء والتصحيحات والامتناع والثقة المنخفضة | CAPABILITY | P0 | W0_0_90D_CORE | LIVE/TIME | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| A07 | Public Verification Interface & Methodology | واجهة تحقق عامة ومنهجية السجل | CAPABILITY | P1 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| A08 | Independent Reperformance Readiness | جاهزية إعادة الأداء/التحقق المستقل | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | INDEPENDENT | N/A_NON_CAPABILITY |
| B01 | Proprietary Decision Frameworks | أطر قرار خاصة بـBLACKDARK | ASSET | P0 | FOUNDATION_OR_ACCUMULATE_NOW | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| B02 | Cross-Domain Intelligence Fusion | دمج الذكاء عبر المجالات | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| B03 | Signal Quality & Noise Suppression | جودة الإشارة وفصل الضجيج | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| B04 | Canonical Signal / Oracle Semantics | دلالات حاكمة ثابتة للإشارة/Oracle | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| B05 | Explainable Decision Engine | محرك قرار قابل للتفسير | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| B06 | Contribution / Rule Attribution | نسب مساهمة القواعد والإشارات | CAPABILITY | P0 | W1_3_6M | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| B07 | Confidence & Reason Codes | الثقة وأكواد الأسباب | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| B08 | Why / Why-Not & Conflicting-Evidence Explanation | شرح لماذا/لماذا لا والأدلة المتعارضة | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| B09 | Explanation Fidelity & Provenance | أمانة التفسير ومصدره | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| B10 | Human–AI Trust Calibration | معايرة ثقة المستخدم في الذكاء الآلي | CAPABILITY | P1 | W1_3_6M | USER_DATA/EVIDENCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| C01 | Consent-Controlled User Interaction & Decision Ledger | سجل تفاعل وقرار المستخدم بإذن واضح | CAPABILITY | P0 | W1_3_6M | USER_DATA/EVIDENCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| C02 | Behavioral Adaptation & Context Graph | سجل التكيف والسياق السلوكي | CAPABILITY | P1 | W1_3_6M | USER_DATA/EVIDENCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| C03 | Personalized Workspace, Watchlists & Saved Intelligence | مساحة عمل وقوائم وذكاء محفوظ | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| C04 | Watchlist & Workspace Evolution History | تاريخ تطور القوائم ومساحات العمل | CAPABILITY | P1 | W1_3_6M | USER_DATA/EVIDENCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| C05 | Decision-Linked Alerts | تنبيهات مرتبطة بالقرار | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| C06 | Versioned Decision Playbooks | Playbooks قرار قابلة للإصدار | CAPABILITY | P0 | W1_3_6M | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| C07 | Cognitive Switching-Cost Evidence | دليل تكلفة التبديل المعرفية | METRIC | P2 | MEASURE_NOT_BUILD_AS_FEATURE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| C08 | Workflow Dependency & Migration-Cost Map | خريطة اعتماديات وتكلفة هجرة سير العمل | CAPABILITY | P1 | W2_AFTER_CORE_DEPENDENCIES | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| C09 | Institutional Team Shared Reference Workspace | مساحة مرجعية مشتركة للفرق المؤسسية | CAPABILITY | P0 | W1_3_6M | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| D01 | Collective Outcome Intelligence | ذكاء جماعي من النتائج | CAPABILITY | P1 | W1_3_6M | USER_DATA/EVIDENCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| D02 | Population Benchmark & Calibration Dataset | مجموعة بيانات benchmark ومعايرة جماعية | ASSET | P1 | ACCUMULATE_WITH_USE | USER_DATA/EVIDENCE | N/A_NON_CAPABILITY |
| D03 | Sample Quality & Statistical Confidence Engine | محرك جودة العينة والثقة الإحصائية | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| D04 | Expert Feedback Quality, Bias & Sybil Controls | جودة تغذية الخبراء وضبط التحيز وSybil | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | USER_DATA/EVIDENCE | N/A_NON_CAPABILITY |
| D05 | Privacy-Safe Collective Learning | تعلم جماعي محافظ على الخصوصية | CAPABILITY | P0 | W1_3_6M | USER_DATA/EVIDENCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| D06 | Network-Effect Measurement Framework | إطار قياس تأثير الشبكة | METRIC | P1 | MEASURE_NOT_BUILD_AS_FEATURE | USER_DATA/EVIDENCE | N/A_NON_CAPABILITY |
| E01 | API / SDK Platform Layer | طبقة API/SDK | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| E02 | Enterprise Connector Hub (Excel, Telegram, Webhooks) | مركز تكاملات Excel وTelegram وWebhooks | CAPABILITY | P1 | W1_3_6M | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| E03 | Embedded Analytics & White-Label | تحليلات مدمجة وWhite-Label | CAPABILITY | P1 | W1_3_6M | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| E04 | Connector Compatibility & Version Governance | حوكمة توافق وإصدارات التكاملات | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| E05 | Integration Footprint Registry | سجل بصمة التكاملات الفعلية | ASSET | P1 | ACCUMULATE_WITH_USE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| E06 | User-Confirmed Execution Handoff + Context Pack | تسليم تنفيذ مؤكد من المستخدم مع حزمة سياق | CAPABILITY | P0 | W2_LOCAL_NOW_LIVE_LATER | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| F01 | Decision Latency & Time-to-Insight Engineering | هندسة زمن القرار والوصول للمعلومة | CAPABILITY | P0 | W0_0_90D_CORE | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| F02 | User-Facing Freshness & Performance Evidence | دليل freshness/performance للمستخدم | CAPABILITY | P1 | W1_3_6M | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| G01 | Crypto-Native Ontology / Knowledge Model | أنطولوجيا معرفة أصيلة للكريبتو | CAPABILITY | P0 | W2_AFTER_CORE_DEPENDENCIES | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| G02 | Domain-Specific Models & Rules | نماذج وقواعد متخصصة في الكريبتو | ASSET | P0 | FOUNDATION_OR_ACCUMULATE_NOW | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| G03 | Vertical Benchmarks & Domain Language | Benchmarks ولغة مجال متخصصة | ASSET | P1 | ACCUMULATE_WITH_USE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| G04 | Segment-Specific Workflows | سير عمل خاص بكل شريحة | CAPABILITY | P0 | W1_3_6M | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| G05 | Role-Specific Intelligence & Entitlements | ذكاء وصلاحيات حسب الدور | CAPABILITY | P0 | W1_3_6M | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| G06 | Shared-Core Multi-Segment Adaptation & Fit Matrix | تكييف محرك واحد لشرائح متعددة مع مصفوفة Fit | CAPABILITY | P1 | W2_BUILD_OR_ACCUMULATE_AFTER_W1 | USER_DATA/EVIDENCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| H01 | Regulatory Readiness Layer | طبقة الجاهزية التنظيمية | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| H02 | Jurisdiction & Policy Awareness | وعي الولايات والسياسات | CONTROL_OR_GOVERNANCE | P1 | LIGHTWEIGHT_RISK_BASED | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| H03 | Machine-Readable Compliance Controls | ضوابط امتثال قابلة للقراءة/التنفيذ آليًا | CONTROL_OR_GOVERNANCE | P1 | LIGHTWEIGHT_RISK_BASED | LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| H04 | Market-Access / Permission Matrix | مصفوفة الوصول والصلاحيات السوقية | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| H05 | License / Certification Asset Registry | سجل التراخيص والاعتمادات | CONTROL_OR_GOVERNANCE | P1 | LIGHTWEIGHT_RISK_BASED | INDEPENDENT; LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| H06 | Regulatory Barrier & Replicability Assessment | تقييم الحاجز التنظيمي وصعوبة تقليده | METRIC | P2 | MEASURE_NOT_BUILD_AS_FEATURE | LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| H07 | Regulatory Change Monitoring | مراقبة التغير التنظيمي | CONTROL_OR_GOVERNANCE | P1 | LIGHTWEIGHT_RISK_BASED | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| H08 | Audit-Ready Compliance Evidence & Trust Surface | أدلة امتثال وصفحة ثقة قابلة للتدقيق | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | INDEPENDENT; LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| I01 | Multi-Moat Compounding Operating Model | نموذج تشغيل لتراكم عدة Moats | OPERATING_MODEL_OR_STRATEGY | P0 | LIGHTWEIGHT_STRATEGY_GOVERNANCE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| I02 | Moat Ownership, Routing & Time-Dependency Classification | ملكية الـMoat ومسار التنفيذ وتصنيف الاعتماد على الزمن | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| I03 | Counter-Positioning & Six-Hero Surface Governance | حوكمة التموضع المضاد وسطح الأبطال الستة | OPERATING_MODEL_OR_STRATEGY | P0 | LIGHTWEIGHT_STRATEGY_GOVERNANCE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| I04 | Vertical Positioning & Priority-Segment Portfolio | تموضع عمودي ومحفظة شرائح أولوية | OPERATING_MODEL_OR_STRATEGY | P0 | LIGHTWEIGHT_STRATEGY_GOVERNANCE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| I05 | Moat Strength, Durability & Time-to-Copy Measurement | قياس قوة واستدامة وزمن تقليد الـMoat | METRIC | P1 | MEASURE_NOT_BUILD_AS_FEATURE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| I06 | Moat Evidence Ledger & Dependency Map | سجل أدلة الـMoat وخريطة الترابط | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| I07 | Day-One Accumulation Scheduler & Continuity Evidence | جدولة التراكم من اليوم الأول ودليل الاستمرارية | CAPABILITY | P0 | W2_AFTER_CORE_DEPENDENCIES | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| J01 | Unique Data Coverage, Quality & Provenance | تغطية وجودة ومصدر البيانات | ASSET | P0 | FOUNDATION_OR_ACCUMULATE_NOW | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS | N/A_NON_CAPABILITY |
| J02 | Data Rights & Licensing Registry | سجل حقوق وترخيص البيانات | CONTROL_OR_GOVERNANCE | P0 | FOUNDATION_AS_NEEDED_FOR_W0_W1 | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW | N/A_NON_CAPABILITY |
| J03 | Proprietary Intelligence & IP Registry | سجل الذكاء والملكية الفكرية الخاصة | ASSET | P0 | FOUNDATION_OR_ACCUMULATE_NOW | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| J04 | Vendor Independence & Portability | استقلالية الموردين وقابلية النقل | CAPABILITY | P0 | W2_LOCAL_NOW_LIVE_LATER | LIVE/TIME; EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| J05 | Operational Reliability & Recovery | الاعتمادية التشغيلية والتعافي | CAPABILITY | P0 | W2_LOCAL_NOW_LIVE_LATER | LIVE/TIME | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| J06 | Developer Ecosystem Infrastructure | بنية منظومة المطورين | CAPABILITY | P1 | W2_BUILD_OR_ACCUMULATE_AFTER_W1 | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| J07 | Distribution Infrastructure | بنية التوزيع | CAPABILITY | P1 | W2_AFTER_CORE_DEPENDENCIES | EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| J08 | Research & Content Compounding Engine | محرك تراكم الأبحاث والمحتوى | ASSET | P1 | ACCUMULATE_WITH_USE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| J09 | Acquisition Readiness & Living Evidence Room | جاهزية الاستحواذ وغرفة الأدلة الحية | CAPABILITY | P0 | W2_AFTER_CORE_DEPENDENCIES | NONE_KNOWN_FROM_SOURCE | UNVERIFIED_PENDING_CURRENT_826_SSOT |
| J10 | Rare-Skills Knowledge Continuity | استمرارية معرفة المهارات النادرة | ASSET | P1 | ACCUMULATE_WITH_USE | NONE_KNOWN_FROM_SOURCE | N/A_NON_CAPABILITY |
| J11 | Learning Velocity & Outcome Feedback Loop | سرعة التعلم وحلقة النتائج | CAPABILITY | P0 | W1_3_6M | USER_DATA/EVIDENCE; LIVE/TIME | UNVERIFIED_PENDING_CURRENT_826_SSOT |

## 6. Reconciliation فعلي من المصدر إلى السجل Canonical

### 6.1 الأربعون Feature/Capability في المصدر

| Source # | Source Feature/Capability | Canonical disposition |
|---:|---|---|
| 1 | Immutable Public Track Record | A01 |
| 2 | Pre-Outcome Timestamping | A02 |
| 3 | Independent Track-Record Verification | A07/A08 |
| 4 | Prediction-to-Outcome Proof Chain | A03/A04 |
| 5 | Historical Accuracy by Market/Regime/Asset | A05 |
| 6 | User Workflow Persistence | C03/C04 |
| 7 | Personalized Workspace / Watchlists / Saved Intelligence | C03 |
| 8 | User Learning Lock-in | C02/C07 |
| 9 | Consistent Signal/Oracle Semantics | B04 |
| 10 | Behavioral Adaptation History | C02 |
| 11 | Collective Outcome Intelligence | D01 |
| 12 | Population-Level Accuracy Benchmarking | D02/D03 |
| 13 | Community/Population Calibration Dataset | D02 |
| 14 | Network-Effect Measurement Engine | D06 |
| 15 | Deep Excel Integration | E02 |
| 16 | Telegram Integration | E02 |
| 17 | API / SDK Integration Layer | E01 |
| 18 | Embedded Analytics / White-Label Integration | E03 |
| 19 | Persistent External Workflow Connections | E02/E05 |
| 20 | Integration Migration Cost Mapping | C08/E05 |
| 21 | Rapid Intelligence / Low-Latency Delivery | F01 |
| 22 | Time-to-Insight Optimization | F01/F02 |
| 23 | First-Mover Compounding Mechanism | I07 |
| 24 | Explainable Decision Engine | B05 |
| 25 | Decomposable Intelligence | B06/B08 |
| 26 | Signal Contribution Breakdown | B06 |
| 27 | Confidence + Reason Codes | B07 |
| 28 | Why / Why Not Decision Explanation | B08 |
| 29 | Crypto-Native Vertical Intelligence | G01/G02/G03 |
| 30 | Deep Segment-Specific Workflows | G04 |
| 31 | Role-Specific Intelligence | G05 |
| 32 | Domain-Specific Models and Rules | G02 |
| 33 | Regulatory Readiness Layer | H01 |
| 34 | Machine-Readable Compliance Controls | H03 |
| 35 | Jurisdiction/Policy Awareness | H02/H04 |
| 36 | Audit-Ready Compliance Evidence | H08 |
| 37 | License / Certification Asset Registry | H05 |
| 38 | Regulatory Barrier Classification | H06 |
| 39 | Compliance ≠ Moat Classification | H06/I05 |
| 40 | Moat Strength Measurement Framework | I05/I06 |

### 6.2 الإضافات الاستراتيجية السبع

| # | Strategic construct | Canonical coverage |
|---:|---|---|
| 1 | Verifiable Reputation Moat | A01–A08 |
| 2 | Cognitive Switching Cost | C02–C08 |
| 3 | Data Network Effect | D01–D06 |
| 4 | Integration Lock-in | E01–E05 + C08 |
| 5 | Explainability Moat | B05–B10 |
| 6 | Vertical Intelligence Moat | G01–G06 |
| 7 | Regulatory Asset Moat | H01–H08 + I05 |

### 6.3 تصنيف العوامل الثمانية

| Source factor | Canonical coverage |
|---|---|
| Track Record | A01–A08 |
| Switching Costs | C02–C08 |
| Network Effects | D01–D06 |
| Integration Depth | E01–E05 |
| Speed | F01–F02 |
| Explainability | B05–B10 |
| Vertical Specialization | G01–G06 |
| Regulatory Compliance | H01–H08 |

### 6.4 أهم خمس أولويات في المصدر

| # | Source priority | Canonical coverage |
|---:|---|---|
| 1 | Immutable Verified Track Record | A01/A02/A03/A04/A05/A06/A07/A08 |
| 2 | Cognitive + Workflow Switching Costs | C02/C03/C04/C07/C08 |
| 3 | Data Network Effect / Collective Outcome Intelligence | D01/D02/D03/D04/D05/D06 |
| 4 | Deep API/Workflow Integration Lock-in | E01/E02/E03/E04/E05 |
| 5 | Explainable Decision Intelligence | B05/B06/B07/B08/B09/B10 |

> هذا الـreconciliation يثبت تغطية **بنية المصدر المتاحة فعليًا**. لا يثبت تنفيذ هذه السجلات في repo ولا mapping إلى IDs 1–826.

## 7. بوابة الربط بالكتالوج التقني 1–826

النسخة السابقة كانت تضع سجلًا استراتيجيًا موازيًا بلا ربط تقني. التصحيح المؤسسي هنا هو **عدم اختلاق IDs**:

- كل Record من نوع `CAPABILITY` = `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` حتى يُقارن بالـ826 canonical inventory الحالي.
- المطلوب عند التنفيذ داخل repo: `Strategic Record → 826 ID(s) → canonical requirement → implementation → actual consumer path → oracle → tests → tested SHA → evidence`.
- نتائج المطابقة المسموح بها: `EXISTING_CANONICAL_MATCH | PARTIAL_MATCH | NEW_GAP | DUPLICATE_ALIAS | NOT_A_826_CAPABILITY`.
- لا يُسمح بتحويل التشابه الاسمي إلى mapping. المطابقة دلالية على requirement/input/logic/output/user outcome/canonical role.

### سجل الـ40 Capability المطلوب Reconcile لها

| ID | Capability | 826 reconciliation state |
|---|---|---|
| A01 | Verified Forward/Public Track Record | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| A03 | Prediction–Decision–Outcome Evidence Chain | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| A04 | Automated Multi-Horizon Outcome Evaluator | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| A05 | Accuracy, Calibration & Regime Analytics | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| A06 | Error, Correction, Abstention & Low-Confidence Ledger | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| A07 | Public Verification Interface & Methodology | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| B02 | Cross-Domain Intelligence Fusion | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| B03 | Signal Quality & Noise Suppression | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| B05 | Explainable Decision Engine | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| B06 | Contribution / Rule Attribution | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| B07 | Confidence & Reason Codes | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| B08 | Why / Why-Not & Conflicting-Evidence Explanation | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| B10 | Human–AI Trust Calibration | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| C01 | Consent-Controlled User Interaction & Decision Ledger | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| C02 | Behavioral Adaptation & Context Graph | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| C03 | Personalized Workspace, Watchlists & Saved Intelligence | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| C04 | Watchlist & Workspace Evolution History | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| C05 | Decision-Linked Alerts | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| C06 | Versioned Decision Playbooks | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| C08 | Workflow Dependency & Migration-Cost Map | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| C09 | Institutional Team Shared Reference Workspace | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| D01 | Collective Outcome Intelligence | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| D05 | Privacy-Safe Collective Learning | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| E01 | API / SDK Platform Layer | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| E02 | Enterprise Connector Hub (Excel, Telegram, Webhooks) | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| E03 | Embedded Analytics & White-Label | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| E06 | User-Confirmed Execution Handoff + Context Pack | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| F01 | Decision Latency & Time-to-Insight Engineering | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| F02 | User-Facing Freshness & Performance Evidence | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| G01 | Crypto-Native Ontology / Knowledge Model | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| G04 | Segment-Specific Workflows | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| G05 | Role-Specific Intelligence & Entitlements | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| G06 | Shared-Core Multi-Segment Adaptation & Fit Matrix | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| I07 | Day-One Accumulation Scheduler & Continuity Evidence | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| J04 | Vendor Independence & Portability | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| J05 | Operational Reliability & Recovery | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| J06 | Developer Ecosystem Infrastructure | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| J07 | Distribution Infrastructure | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| J09 | Acquisition Readiness & Living Evidence Room | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |
| J11 | Learning Velocity & Outcome Feedback Loop | UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION |

## 8. بوابات الإثبات الفردية — لا نص قالبي موحد

> كل بوابة أدناه مرتبطة بمعنى السجل نفسه. لا يوجد `E2/E3 + canonical-path` كنص بديل عن الإثبات. مستوى الدليل النهائي يُحدد حسب claim والمخاطر، مع الفصل بين local/CI وlive وindependent.

### A01 — Verified Forward/Public Track Record
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** سجل زمني حقيقي قابل لإعادة التحقق، يفصل backtest/simulation/shadow/live ويمنع خلط فئات الدليل.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `LIVE/TIME`
- **بوابة الإثبات المحددة:** ثبت timestamp قبل النتيجة، append-only/tamper-evident lineage، فصل BACKTESTED/SIMULATED/FORWARD_SHADOW/VERIFIED_PRODUCTION، وعينة forward قابلة لإعادة الحساب؛ لا claim حي قبل تراكم E4 فعلي.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### A02 — Pre-Outcome Timestamp & Anti-Backfill Integrity
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** يثبت أن التوقع سُجل قبل معرفة النتيجة، مع tamper-evident lineage.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** اختبار يمنع إنشاء/تعديل توقع بعد outcome cutoff؛ تحقق monotonic timestamps، audit lineage، وحالات clock skew/replay/tampering.

### A03 — Prediction–Decision–Outcome Evidence Chain
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** ربط كل signal/prediction/decision بالمدخلات والإصدار والنتيجة والدليل.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** إعادة أداء سلسلة signal→prediction→decision→outcome من inputs/versioned rules إلى النتيجة، مع referential integrity وعدم وجود orphan links.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### A04 — Automated Multi-Horizon Outcome Evaluator
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** يقيم النتيجة تلقائيًا على horizons معرفة مسبقًا مع evaluator/version lineage.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Golden cases متعددة horizons تثبت تعريف outcome مسبقًا، evaluator versioning، الحدود الزمنية، وتصحيح late/missing outcomes بدون إعادة كتابة التاريخ.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### A05 — Accuracy, Calibration & Regime Analytics
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** دقة ومعايرة حسب asset/regime/horizon مع denominator واضح وعدم cherry-picking.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `LIVE/TIME`
- **بوابة الإثبات المحددة:** حساب accuracy/calibration حسب asset/regime/horizon على dataset مؤرشف مع denominator ثابت، confidence intervals/coverage، ومنع cherry-picking أو future leakage.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### A06 — Error, Correction, Abstention & Low-Confidence Ledger
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** إظهار الفشل وI-don't-know والتصحيحات بجانب النجاحات لثقة قابلة للدفاع.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `LIVE/TIME`
- **بوابة الإثبات المحددة:** حالات فشل/abstain/low-confidence/correction تُسجل alongside successes؛ اختبار أن correction لا تمحو النسخة الأصلية وأن معدلات الامتناع/الخطأ قابلة للحساب.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### A07 — Public Verification Interface & Methodology
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** واجهة/API توضح المنهج والعينة والإصدارات والأدلة القابلة للفحص.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** مستخدم مستقل يستطيع من الواجهة/API الوصول إلى methodology، sample definition، version، timestamps، وevidence links وإعادة حساب مثال منشور.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### A08 — Independent Reperformance Readiness
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** حزمة تسمح لمراجع مستقل بإعادة التحقق دون ادعاء assurance قبل حدوثه.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `INDEPENDENT`
- **بوابة الإثبات المحددة:** حزمة reperformance مستقلة تحتوي requirement، code/model/rule/config versions، inputs/snapshot، oracle، expected/actual، SHA/build، exceptions؛ E5 لا يُعلن إلا بتحدٍ مستقل فعلي.

### B01 — Proprietary Decision Frameworks
- **Record Class:** ASSET
- **القيمة/الغرض:** قواعد تجميع، gates/vetoes، risk caps، scoring ومنطق القرار كـIP قابل للإصدار.
- **Execution Lane:** `FOUNDATION_OR_ACCUMULATE_NOW`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Versioned decision rules/gates/vetoes/risk caps لها owner/provenance واختبارات decision-table تُظهر أن تغيير rule يغير outcome كما هو مصمم.

### B02 — Cross-Domain Intelligence Fusion
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** دمج market/derivatives/on-chain/macro/sentiment وغيرها في قرار واحد مع معالجة التعارض.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** سيناريوهات cross-domain تثبت دمج market/derivatives/on-chain/macro/sentiment ومعالجة conflict/missing domain؛ output يختلف منطقيًا عند تغير evidence.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### B03 — Signal Quality & Noise Suppression
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** فلترة/ranking تقاس بـprecision/recall/calibration بدل وصف تسويقي.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Benchmark معلن يقيس precision/recall أو metric مناسب قبل/بعد suppression على labeled sample، مع false-positive/false-negative analysis وعدم استخدام نفس function كـoracle.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### B04 — Canonical Signal / Oracle Semantics
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** تعريف مركزي للمعنى والقواعد والإصدار يمنع اختلاف معنى نفس الإشارة بين الأسطح.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Contract tests تثبت أن signal/oracle semantics موحدة عبر كل consumers والأسطح وأن version change لا يحدث silently أو يخلق split-brain.

### B05 — Explainable Decision Engine
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** تفسير ناتج القرار من نفس المنطق الفعلي لا post-hoc marketing explanation.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** اختبار fidelity يربط explanation بنفس rules/evidence التي أنتجت القرار؛ perturbation/ablation تكشف explanation لا يتبع قرارًا لم ينتجه.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### B06 — Contribution / Rule Attribution
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** عرض contributions/rules/weights فقط عندما تكون authoritative فعليًا.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Contribution values/rules المعروضة تطابق authoritative computation؛ لا تعرض weights تقريبية كحقائق؛ اختبارات sum/ordering/invariance حسب التصميم.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### B07 — Confidence & Reason Codes
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** ثقة معايرة وأسباب قابلة للتتبع مع حدود وعدم يقين.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Confidence calibration على holdout/forward evidence مع reason codes traceable إلى causal/decision evidence؛ اختبار حدود low-confidence وabstain.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### B08 — Why / Why-Not & Conflicting-Evidence Explanation
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** يوضح سبب القرار وما الذي كان سيغيّره وكيف عولجت الإشارات المتعارضة.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Golden scenarios لكل why/why-not/conflict تثبت شروط القرار والـcounterfactual material؛ تغيير decisive input ينعكس في explanation والقرار المتوقع.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### B09 — Explanation Fidelity & Provenance
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** اختبار fidelity وربط التفسير بالبيانات والقواعد والإصدارات.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Automated fidelity/provenance checks تربط explanation→decision→rule/data/model versions وتكشف stale/mismatched explanation.

### B10 — Human–AI Trust Calibration
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** تصميم الثقة بحيث لا يفرط المستخدم في الاعتماد ولا يرفض النظام بلا سبب.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** User study/behavioral evidence يقيس over-reliance/under-reliance، comprehension، override/abstain behavior حسب context؛ لا claim قبل بيانات مستخدم فعلية.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### C01 — Consent-Controlled User Interaction & Decision Ledger
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** يسجل signal seen/action confirmed/decision context بصورة purpose-limited وprivacy-controlled.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** Consent/purpose tests تثبت أن interaction/decision events تُجمع فقط عند الإذن المناسب، مع minimization، deletion/export، purpose tags، وtenant isolation.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### C02 — Behavioral Adaptation & Context Graph
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** سياق تراكمي للأهداف/المخاطر/السلوك/التفضيلات دون جمع زائد.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** اختبارات personalization تثبت أن context history يغيّر recommendation/presentation المسموح به بطريقة قابلة للتفسير، مع opt-out/reset وعدم تسرب بين المستخدمين.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### C03 — Personalized Workspace, Watchlists & Saved Intelligence
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** يجعل المنتج مكان عمل متكرر ويحتفظ بسياق المستخدم القابل للتصدير.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** E2E يحفظ/يسترجع workspace/watchlist/intelligence عبر sessions والأجهزة المسموح بها، مع export/delete وconflict/version handling.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### C04 — Watchlist & Workspace Evolution History
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** نسخ تاريخية مفيدة للمراجعة والرجوع، وليست مجرد snapshot.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** Version-history tests تثبت snapshots/diffs/restore وعدم فقد chronology، مع retention policy وuser-scoped access.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### C05 — Decision-Linked Alerts
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** تنبيه مرتبط بالthesis/state/outcome لا threshold منفصل فقط.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** E2E يربط alert بـthesis/state/outcome؛ dedupe/rate-limit/staleness/acknowledgement tested، وتصل القناة المقصودة في sandbox أو live حسب claim.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### C06 — Versioned Decision Playbooks
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** workflow متكرر له trigger/inputs/decision/evidence/outcome/version.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Playbook contract يثبت trigger→inputs→decision→evidence→outcome→version؛ replay على نسخة سابقة يعطي نفس النتيجة ضمن نفس inputs.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### C07 — Cognitive Switching-Cost Evidence
- **Record Class:** METRIC
- **القيمة/الغرض:** يقيس قيمة التعلم المتراكم دون تصميم حبس تعسفي للمستخدم.
- **Execution Lane:** `MEASURE_NOT_BUILD_AS_FEATURE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Metric specification يعرّف switching-cost construct بدون dark patterns؛ يقاس من user learning/dependency evidence مع portability guardrails؛ لا يُعامل كـfeature.

### C08 — Workflow Dependency & Migration-Cost Map
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** يعرف ماذا يعتمد على BLACKDARK وما يلزم لنقل workflow مع الحفاظ على portability.
- **Execution Lane:** `W2_AFTER_CORE_DEPENDENCIES`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Dependency graph ومخرجات migration estimate قابلة لإعادة الحساب من integrations/workflows الفعلية؛ لا تضخيم متعمد لتكلفة الخروج.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### C09 — Institutional Team Shared Reference Workspace
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** سياق ولوحات وقرارات مشتركة مع RBAC/audit/provenance.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Multi-user E2E يثبت shared references، RBAC، audit trail، tenant boundaries، concurrent updates، وprovenance للقرارات المشتركة.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### D01 — Collective Outcome Intelligence
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** استخدام outcomes المسموح بها لتحسين calibration والbenchmarks بصورة مجمعة.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** Pipeline من consented outcomes إلى aggregate intelligence يثبت aggregation rules، cohort definitions، minimum sample/confidence، وعدم leakage لهوية فردية.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### D02 — Population Benchmark & Calibration Dataset
- **Record Class:** ASSET
- **القيمة/الغرض:** مقارنات إحصائية مع تعريف population/selection bias/coverage.
- **Execution Lane:** `ACCUMULATE_WITH_USE`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** Dataset contract يثبت population definition، selection/coverage bias، versioning، consent/rights، cohort lineage، وstatistical representativeness limits.

### D03 — Sample Quality & Statistical Confidence Engine
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** يفصل حجم العينة عن جودتها ويقيس uncertainty/coverage/independence.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Synthetic/golden samples تختبر sample size، independence، missingness، confidence interval/uncertainty، وتمنع تحويل n الكبير إلى ثقة زائفة.

### D04 — Expert Feedback Quality, Bias & Sybil Controls
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** لا يعامل كل feedback بالتساوي؛ يضبط abuse/bias/identity-quality حيث ينطبق.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** Adversarial tests لSybil/duplicate/low-quality feedback، weighting rules، identity-quality signals، bias monitoring، وabuse response.

### D05 — Privacy-Safe Collective Learning
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** aggregation/minimization/permissions تمنع تحويل data network effect إلى مخاطرة خصوصية.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** Privacy threat model + aggregation/minimization/access tests؛ منع reconstruction/linkage قدر الإمكان حسب التصميم، مع retention/deletion وconsent enforcement.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### D06 — Network-Effect Measurement Framework
- **Record Class:** METRIC
- **القيمة/الغرض:** يفصل direct/indirect effects ويمنع claim قبل إثبات أن زيادة المشاركين تحسن قيمة الآخرين.
- **Execution Lane:** `MEASURE_NOT_BUILD_AS_FEATURE`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** Metric framework يعرّف direct/indirect network effect، unit of analysis، counterfactual أو baseline، ويمنع claim causal قبل evidence سوقي كافٍ.

### E01 — API / SDK Platform Layer
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** contracts/versioning/auth/entitlements/metering/observability للمستهلكين الخارجيين.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Contract tests للAPI/SDK تشمل versioning، authn/authz، entitlement، rate limits/metering، idempotency حيث يلزم، error semantics، docs examples وbackward compatibility.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### E02 — Enterprise Connector Hub (Excel, Telegram, Webhooks)
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** موصلات ذات قيمة workflow بدل اعتبار كل connector moat منفصلًا.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS`
- **بوابة الإثبات المحددة:** لكل connector contract مستقل للauth/scopes/data mapping/retries/idempotency/version drift؛ dependency/cost/license check قبل اعتماد أي vendor؛ Excel/Telegram/Webhook لا تُعد moat منفصلة.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### E03 — Embedded Analytics & White-Label
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** توزيع intelligence داخل منتجات العملاء مع rights/entitlements/versioning.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Tenant-isolated embedded/white-label E2E يثبت branding config، entitlements، data rights/redistribution، version compatibility، ومخرجات متطابقة مع canonical intelligence.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### E04 — Connector Compatibility & Version Governance
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** إدارة breaking changes/deprecation/contracts وتجنب lock-in هش.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Compatibility matrix + contract tests على supported versions، deprecation window، breaking-change detection، migration path، وrollback.

### E05 — Integration Footprint Registry
- **Record Class:** ASSET
- **القيمة/الغرض:** يعرف consumers/dependencies/usage/criticality بدون تحويله إلى vanity metric.
- **Execution Lane:** `ACCUMULATE_WITH_USE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Registry reconciled against actual consumers/dependencies/usage telemetry؛ orphan/stale integrations flagged؛ لا vanity counts.

### E06 — User-Confirmed Execution Handoff + Context Pack
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** ينقل القرار إلى venue/external workflow بإقرار صريح وبدون تنفيذ خفي أو commission incentive غير معلن.
- **Execution Lane:** `W2_LOCAL_NOW_LIVE_LATER`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Explicit user confirmation before handoff، immutable context pack، destination/amount/action preview، cancellation/audit، legal/venue boundary state؛ لا hidden execution.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### F01 — Decision Latency & Time-to-Insight Engineering
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** قياس event→decision/time-to-insight مع p95/p99/SLO حسب نوع المسار.
- **Execution Lane:** `W0_0_90D_CORE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Performance benchmark لكل workload يعرّف event→decision وtime-to-insight، p50/p95/p99/SLO، load profile، resource envelope، وdegradation behavior.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### F02 — User-Facing Freshness & Performance Evidence
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** يعرض last update/freshness/generation time حيث يهم بدل عداد ms تسويقي دائم.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Displayed freshness/generation time reconciles with authoritative timestamps; stale/degraded states visible; UX test verifies users can interpret recency correctly.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### G01 — Crypto-Native Ontology / Knowledge Model
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** لغة وعلاقات entities/events/assets/venues/protocols كطبقة معرفة حاكمة.
- **Execution Lane:** `W2_AFTER_CORE_DEPENDENCIES`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Ontology tests validate entity/event/asset/venue/protocol relationships، uniqueness/aliases/version migration، provenance، وcompetency questions representative of crypto workflows.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### G02 — Domain-Specific Models & Rules
- **Record Class:** ASSET
- **القيمة/الغرض:** منطق لا يكتفي بنماذج عامة ويخضع للversioning/benchmarking.
- **Execution Lane:** `FOUNDATION_OR_ACCUMULATE_NOW`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Model/rule cards تشمل purpose/data/version/benchmark/limitations؛ holdout/replay tests ومقارنة baseline؛ no generic model claim دون domain evidence.

### G03 — Vertical Benchmarks & Domain Language
- **Record Class:** ASSET
- **القيمة/الغرض:** benchmarks وحالات سوق/domain semantics قابلة لإعادة الاختبار.
- **Execution Lane:** `ACCUMULATE_WITH_USE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Benchmark set versioned وممثل لحالات المجال، domain terminology definitions canonical، scoring rubric reproducible، leakage controls documented.

### G04 — Segment-Specific Workflows
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** Retail/Pro/Fund/Institutional flows مختلفة حسب الحاجة لا مجرد UI skin.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Per-segment E2E proves materially different tasks/decisions for Retail/Pro/Fund/Institutional based on needs—not UI skin—while reusing canonical core.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### G05 — Role-Specific Intelligence & Entitlements
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** مخرجات وعمق وpermissions مناسبة للدور مع canonical core واحد.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Role matrix + entitlement E2E proves authorized depth/output/permissions، negative denial paths، tenant isolation، and no role-to-role leakage.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### G06 — Shared-Core Multi-Segment Adaptation & Fit Matrix
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** يمنع fork لكل شريحة ويربط claims بـsegment fit/WTP/retention لاحقًا.
- **Execution Lane:** `W2_BUILD_OR_ACCUMULATE_AFTER_W1`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE`
- **بوابة الإثبات المحددة:** Fit matrix links segment→job→workflow→evidence→WTP/retention hypothesis; shared-core adaptations validated per segment; market claims remain pending until measured.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### H01 — Regulatory Readiness Layer
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** متطلبات/controls/owners/evidence دون ادعاء ترخيص أو امتثال غير موجود.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Requirements/control/evidence register per applicable jurisdiction with owner/status; legal assertions tagged source/date; readiness never labeled certification/compliance without external basis.

### H02 — Jurisdiction & Policy Awareness
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** يربط feature/data/action بالولاية والسياسات المطبقة وتاريخها.
- **Execution Lane:** `LIGHTWEIGHT_RISK_BASED`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Policy/jurisdiction data has authoritative source/date/version/effective period; tests map feature/data/action to applicable rules and handle unknown/conflict states.

### H03 — Machine-Readable Compliance Controls
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** policy-as-data حيث يكون قابلًا للتحديد والاختبار، دون تضخيم claims.
- **Execution Lane:** `LIGHTWEIGHT_RISK_BASED`
- **Dependency/Evidence:** `LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Machine-readable policy rules have schema/version/owner/test vectors and fail-safe behavior; human/legal review path for ambiguous rules.

### H04 — Market-Access / Permission Matrix
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** ماذا يجوز وأين وتحت أي شرط/دليل/ترخيص.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Permission matrix tested on allow/deny/unknown across jurisdiction/product/action; default behavior and evidence source explicit.

### H05 — License / Certification Asset Registry
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** يسجل scope/version/issuer/validity/evidence؛ لا يحول readiness إلى certification.
- **Execution Lane:** `LIGHTWEIGHT_RISK_BASED`
- **Dependency/Evidence:** `INDEPENDENT; LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Registry records issuer/scope/version/validity/evidence/expiry; only verified external certification/license can be marked active; reminders do not imply compliance.

### H06 — Regulatory Barrier & Replicability Assessment
- **Record Class:** METRIC
- **القيمة/الغرض:** يفصل ticket-to-entry عن barrier/cornered-resource الفعلي.
- **Execution Lane:** `MEASURE_NOT_BUILD_AS_FEATURE`
- **Dependency/Evidence:** `LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Metric distinguishes ticket-to-entry from scarce/exclusive barrier; inputs sourced and dated; output presented as assessment/hypothesis unless market evidence validates defensibility.

### H07 — Regulatory Change Monitoring
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** يربط التغير بالfeatures/data/markets المتأثرة ومسؤول المتابعة.
- **Execution Lane:** `LIGHTWEIGHT_RISK_BASED`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Change-monitoring source inventory, freshness SLA, diff detection, impact mapping، owner/acknowledgement، false-positive handling، and no legal certainty claim from automation alone.

### H08 — Audit-Ready Compliance Evidence & Trust Surface
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** evidence translation + B2B summary + public trust page مع منع false certification.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `INDEPENDENT; LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Evidence package maps control→evidence→period→owner→exceptions and public/B2B trust surface reflects only verified state; SOC2/ISO claims blocked absent attestation/certificate.

### I01 — Multi-Moat Compounding Operating Model
- **Record Class:** OPERATING_MODEL_OR_STRATEGY
- **القيمة/الغرض:** يدير مجموعة moats مترابطة بدل claim واحد منفصل.
- **Execution Lane:** `LIGHTWEIGHT_STRATEGY_GOVERNANCE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Operating model has explicit moat definitions، dependencies، hypotheses، evidence owners، review cadence، kill/continue criteria; not counted as user capability.

### I02 — Moat Ownership, Routing & Time-Dependency Classification
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** يفصل NOW/USER/LIVE/INDEPENDENT ويحدد owner بلا تضخيم bureaucracy.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Every moat record carries owner، build path، dependency class NOW/USER/LIVE/INDEPENDENT، evidence state and next action; governance overhead measured and minimized.

### I03 — Counter-Positioning & Six-Hero Surface Governance
- **Record Class:** OPERATING_MODEL_OR_STRATEGY
- **القيمة/الغرض:** يحمي بساطة تجربة المنتج مع controlled exceptions؛ لا قرار أبدي غير قابل للمراجعة.
- **Execution Lane:** `LIGHTWEIGHT_STRATEGY_GOVERNANCE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Six-Hero mapping has FEED/CONTEXT/NA rationale، exception process، user-surface coherence tests; strategy remains revisable with evidence.

### I04 — Vertical Positioning & Priority-Segment Portfolio
- **Record Class:** OPERATING_MODEL_OR_STRATEGY
- **القيمة/الغرض:** 2-3 شرائح أولوية قابلة للمراجعة مع value proposition واضح ودليل لاحق.
- **Execution Lane:** `LIGHTWEIGHT_STRATEGY_GOVERNANCE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Each priority segment has JTBD/problem، measurable value hypothesis، evidence threshold، acquisition channel hypothesis and review gate; portfolio limited by capacity.

### I05 — Moat Strength, Durability & Time-to-Copy Measurement
- **Record Class:** METRIC
- **القيمة/الغرض:** يقيس defensibility بدل استخدام كلمة moat كادعاء تسويقي.
- **Execution Lane:** `MEASURE_NOT_BUILD_AS_FEATURE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Metric defines strength/durability/time-to-copy dimensions with evidence levels; no 'moat' claim from architecture alone; repeated measurement over time.

### I06 — Moat Evidence Ledger & Dependency Map
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** يربط claim→asset→evidence→version→validity ويبين كيف تتراكم المزايا.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Ledger maps claim→asset→evidence→version→validity→dependency; stale/expired evidence automatically visible; duplicate claims reconciled.

### I07 — Day-One Accumulation Scheduler & Continuity Evidence
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** start date/age/gaps/continuity لكل أصل زمني بمجرد جاهزيته.
- **Execution Lane:** `W2_AFTER_CORE_DEPENDENCIES`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Scheduler proves start date/age/gaps/continuity for each time-dependent asset and flags interruption; cannot backfill live age.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### J01 — Unique Data Coverage, Quality & Provenance
- **Record Class:** ASSET
- **القيمة/الغرض:** تغطية متعددة المصادر مع freshness/quality/reconciliation/provenance، لا مجرد عدد مصادر.
- **Execution Lane:** `FOUNDATION_OR_ACCUMULATE_NOW`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS`
- **بوابة الإثبات المحددة:** Data Asset Contracts cover source/schema/event/ingest time/freshness/completeness/validity/uniqueness/reconciliation/provenance/rights/fallback; data-quality monitors tested.

### J02 — Data Rights & Licensing Registry
- **Record Class:** CONTROL_OR_GOVERNANCE
- **القيمة/الغرض:** storage/use/derivation/training/API/redistribution/resale/retention rights قابلة للفرض.
- **Execution Lane:** `FOUNDATION_AS_NEEDED_FOR_W0_W1`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS; LEGAL/RIGHTS_REVIEW`
- **بوابة الإثبات المحددة:** Rights registry records storage/use/derivation/training/API/redistribution/resale/retention by source and jurisdiction; unknown rights fail closed for external redistribution.

### J03 — Proprietary Intelligence & IP Registry
- **Record Class:** ASSET
- **القيمة/الغرض:** خوارزميات/indices/features/decision logic مع owner/version/provenance/rights/value.
- **Execution Lane:** `FOUNDATION_OR_ACCUMULATE_NOW`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** IP registry records owner/version/provenance/license/dependencies/value classification and links code/model/rule artifacts; unresolved ownership blocks acquisition-ready claim.

### J04 — Vendor Independence & Portability
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** abstraction/fallback/replacement tests/concentration risk/exit path.
- **Execution Lane:** `W2_LOCAL_NOW_LIVE_LATER`
- **Dependency/Evidence:** `LIVE/TIME; EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS`
- **بوابة الإثبات المحددة:** Adapter/fallback/replacement tests prove portability for material vendors؛ concentration and exit-time measured؛ live failover only claimed after production evidence.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### J05 — Operational Reliability & Recovery
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** SLI/SLO/error budget/degradation/observability/capacity/RTO/RPO/restore/failover.
- **Execution Lane:** `W2_LOCAL_NOW_LIVE_LATER`
- **Dependency/Evidence:** `LIVE/TIME`
- **بوابة الإثبات المحددة:** SLI/SLO/error-budget/degradation/observability/capacity/RTO/RPO/restore/failover tests bound to environment and run; restore proof required for stateful components.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### J06 — Developer Ecosystem Infrastructure
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** docs/sandbox/SDK/templates/plugins/integrations مع governance وsupport model.
- **Execution Lane:** `W2_BUILD_OR_ACCUMULATE_AFTER_W1`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS`
- **بوابة الإثبات المحددة:** Docs/sandbox/SDK/templates/plugins have contract/version tests، onboarding completion evidence، support model؛ ecosystem/adoption claim requires external developer usage.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### J07 — Distribution Infrastructure
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** widgets/embeds/shareable intelligence/referrals/partners/content attribution دون claim moat قبل adoption.
- **Execution Lane:** `W2_AFTER_CORE_DEPENDENCIES`
- **Dependency/Evidence:** `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS`
- **بوابة الإثبات المحددة:** Distribution mechanics (widgets/embeds/share/referral/partners) have attribution and abuse controls; adoption/viral/moat claims require measured acquisition/retention contribution.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### J08 — Research & Content Compounding Engine
- **Record Class:** ASSET
- **القيمة/الغرض:** يحوّل البحث الموثق إلى assets قابلة لإعادة الاستخدام والتوزيع والقياس مع provenance/rights.
- **Execution Lane:** `ACCUMULATE_WITH_USE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Research/content assets carry source provenance، rights، version، reuse links، performance attribution؛ generated content not counted as proprietary value without quality/use evidence.

### J09 — Acquisition Readiness & Living Evidence Room
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** clean IP/repo/data rights/security/evidence/contracts/risks/reproducibility مع freshness/completeness.
- **Execution Lane:** `W2_AFTER_CORE_DEPENDENCIES`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Living evidence room has inventory/freshness/owner/completeness/exceptions/residual-risk and reperformability checks؛ stale artifacts flagged before diligence use.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

### J10 — Rare-Skills Knowledge Continuity
- **Record Class:** ASSET
- **القيمة/الغرض:** توثيق/knowledge transfer/bus-factor لتجنب تحويل talent إلى key-person risk.
- **Execution Lane:** `ACCUMULATE_WITH_USE`
- **Dependency/Evidence:** `NONE_KNOWN_FROM_SOURCE`
- **بوابة الإثبات المحددة:** Critical-knowledge map، runbooks، ownership redundancy، handoff drill، bus-factor evidence؛ documentation existence alone does not prove continuity.

### J11 — Learning Velocity & Outcome Feedback Loop
- **Record Class:** CAPABILITY
- **القيمة/الغرض:** Signal→Prediction→Decision→Outcome→Error→Learning→Version مع قياس time-to-evaluate/improvement.
- **Execution Lane:** `W1_3_6M`
- **Dependency/Evidence:** `USER_DATA/EVIDENCE; LIVE/TIME`
- **بوابة الإثبات المحددة:** Versioned loop signal→prediction→decision→outcome→error→learning→new version; measure time-to-evaluate/time-to-improve and prove improvement versus frozen baseline.
- **826 mapping:** `UNVERIFIED_PENDING_CURRENT_826_SSOT_RECONCILIATION` — لا claim تنفيذ حتى المطابقة مع SSOT التقني.

## 9. بوابة الاعتماد الخارجي والمدفوع

لا يُفترض أن أي dependency خارجي مجاني أو مدفوع بدون تحقق. التصنيف الصحيح هو dependency-first:

| الحالة | المعنى | الإجراء |
|---|---|---|
| NONE_KNOWN_FROM_SOURCE | لا يذكر المصدر اعتمادًا خارجيًا ماديًا | لا نفترض غياب dependency من repo؛ يتحقق عند mapping |
| EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS | connector/data/vendor خارجي محتمل | تحقق API/terms/cost/limits/redistribution قبل build claim |
| USER_DATA/EVIDENCE | القيمة تحتاج مستخدمين/عينة/feedback | تبنى البنية فقط؛ outcome claim مؤجل |
| LIVE/TIME | الدليل يحتاج تشغيلًا وزمنًا حقيقيًا | local engineering منفصل عن live proof |
| INDEPENDENT | يحتاج auditor/attestation/challenge خارجي | لا self-attestation |
| LEGAL/RIGHTS_REVIEW | claim يعتمد حقوق/ولاية/ترخيص | fail-closed للـredistribution/market-access عند عدم اليقين |

**قاعدة `PAID_VENDOR_DESIGNED`:** تُستخدم فقط بعد أن يثبت الـrepo/vendor review أن القدرة تعتمد فعليًا على خدمة مدفوعة غير متاحة. لا نضعها بالاسم على D02 أو E02 أو غيرهما بالتخمين؛ بل نضع `EXTERNAL_DEPENDENCY_VERIFY_COST/RIGHTS` إلى أن يُحسم الواقع. عند ثبوت الدفع وعدم وجود بديل معتمد: `PAID_VENDOR_DESIGNED / EXTERNAL_BLOCKED` ولا شراء تلقائي.

## 10. التسلسل التنفيذي القاسي — [POLICY] مشتق من أولويات المصدر والاعتماديات

### W0 — أول 90 يومًا: 15 Capability فقط

هذه هي القدرات التي تتحول مباشرة إلى **قيمة مستخدم + قرار + سجل نتيجة + وضوح + سرعة**. الضوابط والأصول اللازمة لها تُبنى كdependencies ولا تُحسب ضمن الـ15.

| ID | Capability | User-visible outcome | Daily-pull mechanism | Evidence to watch |
|---|---|---|---|---|
| A01 | Verified Forward/Public Track Record | يرى المستخدم سجلًا زمنيًا يمكن فحصه بدل وعود تسويقية. | الثقة المتكررة قبل اتخاذ القرار. | نسبة sessions التي تفتح سجل الدليل + إعادة التحقق الناجح. |
| A03 | Prediction–Decision–Outcome Evidence Chain | يرى كيف انتقل النظام من الإشارة إلى القرار ثم النتيجة. | يعود لمراجعة قراراته ونتائجها بدل فقد السياق. | نسبة القرارات المرتبطة بنتيجة قابلة للتقييم. |
| A04 | Automated Multi-Horizon Outcome Evaluator | يعرف ماذا حدث بعد 1h/4h/1d/… تلقائيًا. | كل قرار يعود بنتيجة لاحقة بدون عمل يدوي. | زمن اكتمال outcome + نسبة outcomes المقيمة. |
| A05 | Accuracy, Calibration & Regime Analytics | يعرف متى النظام دقيق ومتى يضعف حسب regime/asset/horizon. | يفتح المنصة لمعرفة هل البيئة الحالية تناسب إشاراته. | calibration error/coverage + breakdown usage. |
| A06 | Error, Correction, Abstention & Low-Confidence Ledger | يرى الأخطاء والامتناع والتصحيحات بجانب النجاحات. | الثقة تنشأ من الصراحة واستمرار التعلم. | abstention/error/correction visibility + revisit rate. |
| A07 | Public Verification Interface & Methodology | يفحص المنهج والعينة والدليل بنفسه. | التحقق السريع بدل البحث خارج المنصة. | verification completion rate + time-to-verify. |
| B02 | Cross-Domain Intelligence Fusion | يحصل على قرار واحد من market/derivatives/on-chain/macro/sentiment. | يوفر وقت جمع لوحات متعددة. | time-to-decision + reduction in tool switching. |
| B03 | Signal Quality & Noise Suppression | يرى الإشارات المهمة بدل الضجيج. | يفتح المنصة لمعرفة ما تغيّر فعلاً. | precision/recall + alert dismissal rate. |
| B05 | Explainable Decision Engine | يفهم لماذا خرج القرار بهذه النتيجة. | القرار يصبح قابلًا للفهم والدفاع. | explanation fidelity + comprehension success. |
| B07 | Confidence & Reason Codes | يرى الثقة وأسبابها وحدودها. | يعرف متى يعتمد ومتى ينتظر. | calibration + appropriate override/abstain behavior. |
| B08 | Why / Why-Not & Conflicting-Evidence Explanation | يعرف لماذا/لماذا لا وما الأدلة المتعارضة. | يستخدم المنصة لاختبار thesis بدل قراءة نتيجة فقط. | why/why-not interaction + decision-change traceability. |
| C03 | Personalized Workspace, Watchlists & Saved Intelligence | يحفظ سياقه وقوائمه وأبحاثه ويعود لها فورًا. | كل فتح للمنصة يبدأ من مكانه الحقيقي. | return-to-workspace rate + saved-context reuse. |
| C05 | Decision-Linked Alerts | يتلقى تنبيهًا مرتبطًا بقرار وث thesis لا threshold أعمى. | المنصة تستدعيه عند تغير شيء مهم. | actionable-alert rate + false-alert dismissal. |
| E01 | API / SDK Platform Layer | يستطيع إدخال BLACKDARK في workflow أو أداة أخرى. | القيمة تمتد خارج الواجهة. | API activation + successful consumer calls. |
| F01 | Decision Latency & Time-to-Insight Engineering | يحصل على insight بسرعة قابلة للقياس. | تقليل زمن الانتظار في سوق 24/7. | event→decision p95/p99 + time-to-insight. |

### W0 Foundational controls/assets — تُبنى فقط بقدر ما تحمي/تمكّن W0

`A02`, `A08`, `B01`, `B04`, `B09`, `D03`, `D04`, `E04`, `G02`, `H01`, `H04`, `H08`, `I02`, `I06`, `J01`, `J02`, `J03`

لا تُحوّل هذه العناصر إلى برنامج governance منفصل يسبق المنتج؛ كل control/asset يجب أن يكون له consumer/claim/risk واضح.

### W1 — الأشهر 3–6

- **B06 — Contribution / Rule Attribution:** عرض contributions/rules/weights فقط عندما تكون authoritative فعليًا.
- **B10 — Human–AI Trust Calibration:** تصميم الثقة بحيث لا يفرط المستخدم في الاعتماد ولا يرفض النظام بلا سبب.
- **C01 — Consent-Controlled User Interaction & Decision Ledger:** يسجل signal seen/action confirmed/decision context بصورة purpose-limited وprivacy-controlled.
- **C02 — Behavioral Adaptation & Context Graph:** سياق تراكمي للأهداف/المخاطر/السلوك/التفضيلات دون جمع زائد.
- **C04 — Watchlist & Workspace Evolution History:** نسخ تاريخية مفيدة للمراجعة والرجوع، وليست مجرد snapshot.
- **C06 — Versioned Decision Playbooks:** workflow متكرر له trigger/inputs/decision/evidence/outcome/version.
- **C09 — Institutional Team Shared Reference Workspace:** سياق ولوحات وقرارات مشتركة مع RBAC/audit/provenance.
- **D01 — Collective Outcome Intelligence:** استخدام outcomes المسموح بها لتحسين calibration والbenchmarks بصورة مجمعة.
- **D05 — Privacy-Safe Collective Learning:** aggregation/minimization/permissions تمنع تحويل data network effect إلى مخاطرة خصوصية.
- **E02 — Enterprise Connector Hub (Excel, Telegram, Webhooks):** موصلات ذات قيمة workflow بدل اعتبار كل connector moat منفصلًا.
- **E03 — Embedded Analytics & White-Label:** توزيع intelligence داخل منتجات العملاء مع rights/entitlements/versioning.
- **F02 — User-Facing Freshness & Performance Evidence:** يعرض last update/freshness/generation time حيث يهم بدل عداد ms تسويقي دائم.
- **G04 — Segment-Specific Workflows:** Retail/Pro/Fund/Institutional flows مختلفة حسب الحاجة لا مجرد UI skin.
- **G05 — Role-Specific Intelligence & Entitlements:** مخرجات وعمق وpermissions مناسبة للدور مع canonical core واحد.
- **J11 — Learning Velocity & Outcome Feedback Loop:** Signal→Prediction→Decision→Outcome→Error→Learning→Version مع قياس time-to-evaluate/improvement.

### W2 / Evidence-Later

- القدرات المتبقية تُبنى بعد تثبيت W0/W1 أو عند ظهور dependency حقيقي.
- `USER_DATA/EVIDENCE` و`LIVE/TIME` و`INDEPENDENT` لا تُغلق بادعاء مبكر؛ تُبنى البنية الآن فقط إذا كانت dependency حقيقية لمسار W0/W1.
- Metrics/Strategy records تبقى خفيفة: تقيس القرار ولا تصبح مشروعًا برمجيًا موازيًا.

## 11. تجربة المستخدم والانبهار — من assurance إلى outcome

لا يُعرّف هذا الملف "الانبهار" كصفة تسويقية. يُحوّل إلى hypotheses قابلة للقياس بعد وجود مستخدمين:

| Product outcome | القياس المقترح [POLICY/METRIC] | شرط عدم الادعاء |
|---|---|---|
| Time-to-First-Useful-Decision | زمن من فتح المنتج إلى insight/decision مفيد | لا claim قبل telemetry حقيقي |
| Daily Decision Utility | نسبة sessions التي تنتهي بقرار/حفظ/alert/action مفيد | يحتاج event semantics موثوقة |
| Explanation Comprehension | هل يفهم المستخدم لماذا/لماذا لا والثقة؟ | user testing؛ لا proxy من click فقط |
| Evidence Trust | استخدام verification/track-record وإعادة الفحص | لا يساوي ثقة تلقائيًا؛ يقاس مع qualitative feedback |
| Return-to-Context | العودة إلى workspace/watchlist/playbook محفوظ | يقيس workflow value لا dark-pattern lock-in |
| Actionable Alert Quality | alerts المؤدية لإجراء/مراجعة مقابل dismiss/mute | يجب ضبط false positives وsignal fatigue |
| Tool-Switch Reduction | انخفاض الحاجة للجمع اليدوي بين منصات متعددة | يقاس task study/telemetry، لا claim ذاتي |
| Appropriate Reliance | اعتماد/override/abstain المناسب لثقة النموذج | يحتاج user study + calibration evidence |

## 12. Competitive Reality — external research snapshot، لا ادعاء تفوق

**Snapshot date: 2026-09-07.** استخدمت الصفحات الرسمية للمنافسين فقط كأساس factual للـbaseline:

- **Glassnode:** يعرض on-chain + spot + derivatives في Studio، تنبيهات، API، downloads، Excel Add-In، وميزات مؤسسية/Point-in-Time في الخطط المناسبة.
- **Nansen:** يركز على Smart Money/wallet labels، AI conversational workflow، Smart Alerts، وفي 2026 يروج أيضًا لتنفيذ spot/perps داخل التجربة.
- **CryptoQuant:** يقدم on-chain/off-chain data، dashboards، no-code analytics، real-time alerts، API، institutional solutions، وAI-assisted workflows.

**النتيجة الحاكمة:** لا يجوز لـBLACKDARK أن يعتبر API/alerts/dashboard/AI/Excel وحدها تميّزًا؛ هذه قدرات موجودة فعليًا لدى منافسين كبار. هدف التمايز القابل للاختبار هو **decision-first synthesis + faithful why/why-not + explicit uncertainty/abstention + forward public evidence + outcome-linked learning + cross-domain conflict handling**. هذا **هدف Differentiation يجب إثباته** وليس claim أن المنافسين لا يملكون أي جزء منه.

### Anti-copy strategy

- لا نعتمد على شكل Six Heroes وحده؛ الواجهة قابلة للتقليد.
- الدفاعية المقصودة تأتي من assets/loops التي تتراكم: forward evidence، outcome-linked data، canonical semantics، domain models، user context المصرح به، integration footprint، rights/provenance، وreperformable evidence.
- كل moat claim يبقى `HYPOTHESIS` حتى توجد evidence على durability/time-to-copy/value، ويقاس في I05/I06 بدل استخدامه كشعار.

## 13. قواعد البناء — Risk-Based وليست بيروقراطية موحدة

تُطبق على **Capabilities** وعلى الضوابط/الأصول فقط بقدر materiality:

1. Requirement وuser/system outcome واضحان وقابلان للتحقق.
2. Canonical identity/relationship محسومة؛ لا parallel truth غير معروف.
3. Functional completeness/correctness/appropriateness حسب ISO/IEC 25010 كمفاهيم جودة وظيفية، مع بقية خصائص الجودة حسب الانطباق.
4. Quality-in-use تُقاس في context of use عند وجود مستخدمين؛ لا تستبدلها local unit tests.
5. Data contracts/provenance/freshness/rights/PIT controls حسب طبيعة البيانات.
6. اختبار مناسب للمخاطر: unit/contract/integration/negative/boundary/E2E أو subset مبرر؛ لا checklist ميكانيكي لكل Record.
7. Security/privacy controls حسب attack surface والبيانات، مع OWASP/NIST/ISO references حيث تنطبق.
8. Reliability/performance/observability على المسارات المادية؛ SLOs أرقام مشروع وليست أرقام ISO.
9. AI/model: versioning، benchmark، limitations، calibration/uncertainty، abuse/failure handling، drift/outcome monitoring حسب المخاطر.
10. Evidence مربوط بالـtested source/build/commit والـactual consumer path؛ HTTP200 أو `ok=true` لا يكفي.
11. `PASS_ENGINEERING != PASS_LIVE != ASSURANCE_READY`.
12. لا certification/compliance/market/moat claim من وجود design/control فقط.

## 14. فصل Build عن Evidence

| البعد | معنى الإغلاق | أمثلة |
|---|---|---|
| BUILD_NOW | كل ما يمكن هندسيًا/محليًا مع evidence reproducible | core logic, contracts, local path, data schemas |
| START_ACCUMULATING_NOW | البنية تُشغّل مبكرًا لأن القيمة تعتمد على الزمن | forward track record, outcomes, corrections, learning history |
| USER_EVIDENCE_LATER | لا claim قبل مستخدمين/عينة حقيقية | trust calibration, retention, WTP, network effect |
| LIVE_PROOF_LATER | لا PASS_LIVE قبل production evidence | failover, live SLO, vendor behavior, real freshness |
| INDEPENDENT_ASSURANCE_LATER | لا self-signoff | attestation/certification/independent reperformance |

## 15. ما لا يجوز أن يقوله هذا الملف

- لا يقول إن 73 Record منفذة.
- لا يقول إن 40 Capability mapped بالفعل إلى 1–826.
- لا يقول إن W0/W1 تحقق retention/WTP أو moat قبل القياس.
- لا يقول إن BLACKDARK يتفوق حاليًا على Glassnode/Nansen/CryptoQuant دون comparative evidence.
- لا يقول إن أي vendor مجاني/مدفوع قبل التحقق.
- لا يقول ISO/SOC2/compliance/certification من مجرد readiness أو control existence.
- لا يحول metrics/governance/strategy إلى capabilities لزيادة العدد.

## 16. المراجع المعتمدة المستخدمة

### Standards / frameworks

1. ISO/IEC 25010:2023 — Product quality model.
2. ISO/IEC 25019:2023 — Quality-in-use model.
3. ISO/IEC/IEEE 29148:2018 — Requirements engineering (confirmed current by ISO in 2024; a later DIS does not supersede the published IS).
4. ISO/IEC/IEEE 12207:2026 — Software life cycle processes.
5. ISO/IEC/IEEE 29119-2:2021 — Software testing — Test processes.
6. ISO/IEC 25012:2008 — Data quality model.
7. ISO/IEC 27001:2022 — Information security management systems — Requirements.
8. ISO/IEC 27017:2026 — Cloud-service information security controls.
9. ISO/IEC 27018:2025 — Protection of PII in public clouds acting as PII processors.
10. NIST AI RMF 1.0 / NIST AI 100-1 (2023).
11. NIST Privacy Framework 1.0; newer NIST work is tracked separately and is not silently substituted.
12. OWASP ASVS 5.0.0; OWASP API Security Top 10:2023.
13. AICPA Trust Services Criteria (2017; revised points of focus 2022).

### Strategic / academic references retained with limited attribution

- Klemperer (1995) — switching-cost economics.
- Rochet & Tirole (2006) — two-sided/platform markets.
- Katz & Shapiro (1985) — network externalities/compatibility.
- Porter (1980) — competitive strategy/positioning.
- Hamilton Helmer, *7 Powers* — practical strategy reference; **ليس معيارًا هندسيًا**.

### Competitive factual sources — official product pages, snapshot 2026-09-07

- Glassnode Studio / pricing / alerts pages.
- Nansen product, Smart Money, Smart Alerts, and Nansen AI pages.
- CryptoQuant product, institutional, and pricing pages.

## 17. نتيجة المراجعة الخماسية النهائية

| Assertion | Result |
|---|---|
| Source structure matches current source | TRUE — 20 + 40 + 7 + 8 + 5 |
| False `20/20+68/68+42/42+40/40` claim retained | FALSE |
| 73 incorrectly counted as capabilities | FALSE |
| Correct record-class count | 40 Capability + 17 Control/Governance + 9 Asset + 4 Metric + 3 Strategy/Operating Model |
| Generic repeated evidence sentence retained | FALSE |
| Per-record evidence requirement present | 73/73 |
| Product/user-value execution layer present | TRUE |
| Hard W0 capability set | 15 |
| W1 capability set | 15 |
| Live/user/independent evidence separated | TRUE |
| Paid/external dependency handled without guessing | TRUE |
| 826 mapping fabricated | FALSE |
| 826 mapping status transparent | TRUE — pending repo SSOT reconciliation |
| Competitive baseline based on current official pages | TRUE |
| Competitor inferiority claimed without evidence | FALSE |
| Non-capabilities inflate capability count | FALSE |

**Final status:** `STRATEGIC_REGISTER_CORRECTED_AND_SOURCE_VERIFIED=true`

**Implementation status:** `NOT_CLAIMED` — requires current BLACKDARK repo/826 SSOT reconciliation and engineering evidence.

**No-known-omission statement:** ضمن المصدر الفعلي المحدد أعلاه، تمت مراجعة الأقسام الخمسة وعمل source→canonical reconciliation للمحتوى الفريد المعروف. هذا لا يدعي اكتمال repo أو صحة mapping 1–826 حتى يتم التحقق من SSOT التقني الحالي.