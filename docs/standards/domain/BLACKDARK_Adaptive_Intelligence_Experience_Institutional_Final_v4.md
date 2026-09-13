BLACKDARK Adaptive Intelligence Experience

# المواصفة المؤسسية النهائية المنقحة لمكتبة القدرات وتجربة ذكاء القرار

Institutional Final Specification — Design, Decision Safety, Governance & Execution

الإصدار v4 — النسخة المؤسسية التنفيذية المنقحة لـCursor بعد دمج المراجعة السداسية + تقريري العيوب + مخاطر التنفيذ المتبقية + عقيدة التنفيذ المرحلي

حالة الوثيقة: DESIGN / GOVERNANCE SPECIFICATION — لا تعني بذاتها اكتمال التنفيذ أو PASS_LIVE

صيغة الاستخدام في Cursor: هذه النسخة Markdown هي المرجع التشغيلي المقروء آليًا لهذه المواصفة. يجب تنفيذها مع SSOT الحاكم للمشروع، ولا تُستخدم لتحل محل v6 أو v4_v2 أو Temporal Intelligence.

تاريخ الإصدار: 7 سبتمبر 2026



# 0. قرار الاعتماد ونطاق الوثيقة

هذه النسخة تحافظ على الفكرة المركزية للوثيقة الأصلية: واجهة هادئة فوق محرك ضخم من القدرات، بحيث يحدد المستخدم الهدف بينما تختار BLACKDARK الآليات اللازمة. لكنها تعيد صياغة التصور كمواصفة مؤسسية قابلة للتنفيذ، وتغلق العيوب القاتلة التي ظهرت في تقريري العيوب والمراجعة العلمية اللاحقة على مستوى التصميم، مع إبقاء مخاطر التنفيذ الفعلي مصنفة صراحةً وغير مخفية.

| القاعدة الحاكمة — هذه الوثيقة لا تنشئ SSOT أو بنية موازية. أي تنفيذ برمجي يجب أن يُربط أولًا بالمعايير الحاكمة الحالية للمشروع v6 > v4_v2 > Temporal Intelligence، وبالقاموس/RTM/registries الموجودة فعليًا، مع reuse قبل build. |

| --- |





لا يجوز الادعاء بأن هذه الوثيقة “مطابقة لـISO/NIST” لمجرد الاستشهاد بها. المعايير المذكورة توفر مبادئ ونماذج وعمليات مرجعية؛ أما بنية BLACKDARK التفصيلية (Six Heroes، Router، Decision Contract، Data Room...) فهي قرارات تصميم مشروع يجب إثبات جودتها بالاختبار والأدلة.

## 0.1 الأساس المعياري والعلمي المستخدم

| المرجع | ما يدعمه في هذه المواصفة | حدود الاستشهاد |

| --- | --- | --- |

| ISO 9241-210:2019 | عملية التصميم المتمحور حول الإنسان عبر دورة الحياة | لا يفرض شكل Dashboard أو Progressive Disclosure بعينه. |

| ISO 9241-11:2018 | فهم usability كنتيجة استخدام مرتبطة بالسياق والأهداف | لا يفرض مقياسًا بعينه ولا يثبت نجاح UX بدون اختبار مستخدمين. |

| ISO/IEC 25010:2023 | نموذج مرجعي لتحديد وقياس وتقييم جودة منتجات ICT/software | لا يفرض Data Room أو Router أو هيكل BLACKDARK. |

| ISO/IEC 25012:2008 | نموذج عام لجودة البيانات وتحديد/تقييم متطلباتها | لا يثبت جودة بيانات BLACKDARK بدون قياس فعلي. |

| NIST AI RMF 1.0 | valid/reliable, safe, secure/resilient, accountable/transparent, explainable/interpretable, privacy-enhanced وغيرها | إطار طوعي؛ لا يفرض Trust Card أو Confidence formula محددة. |

| ISO/IEC 23894:2023 | إرشاد لإدارة مخاطر AI ودمجها في الأنشطة | لا يحدد وحده آلية Decision Boundary. |

| ISO/IEC 42001:2023 | نظام إدارة للذكاء الاصطناعي والتحسين المستمر | هذه الوثيقة ليست شهادة 42001. |

| WCAG 2.2 | معايير نجاح قابلة للاختبار لإتاحة الويب؛ W3C يوصي بالإصدار 2.2 | هدف التصميم: AA حيث ينطبق؛ يجب إثبات المطابقة باختبارات فعلية. |





# 1. المبادئ غير القابلة للتفاوض

Calm Surface: السطح اليومي يجب أن يجيب “ماذا يهم الآن؟” بدل أن يعرض مئات الأدوات.

Six Heroes يظلون Primary User Decision Surfaces ولا يتحولون إلى قوائم capabilities.

Complexity On Demand: التفاصيل متاحة لكن لا تُفرض على كل مستخدم.

Evidence Always: لا قرار بلا مصدر/زمن/حالة بيانات/قيود جوهرية قابلة للوصول.

Safety Floor Never Hidden: المعلومات التي يمكن أن تغيّر القرار لا يجوز إخفاؤها بسبب Progressive Disclosure.

The user chooses the goal; BLACKDARK chooses the machinery — مع حق المستخدم في الفهم والرفض/التعديل.

No false precision: لا تعرض نسبة ثقة رقمية إلا إذا كان معناها ومعايرتها empirically defined.

No evidence-class promotion: Historical Replay ≠ Forward Shadow ≠ Verified Production ≠ Independent Assurance.

Reuse before build: أي Router/Graph/Data Room/Trust layer يجب أن يستخدم البنية الحالية بدل إنشاء مسارات موازية.

## 1.1 عقيدة التنفيذ الحاكمة — Execution Doctrine

**Deterministic first → Evidence first → Shadow first → Calibration later → Live promotion last.**

هذه القاعدة إلزامية في تنفيذ Router وDecision Contract وConfidence وDecision Boundary، وليست شعارًا تصميميًا. وتُطبق كالتالي:

1. يبدأ Router بمنطق deterministic/transparent قابل للاختبار والشرح، وليس orchestration ذاتي غامض أو AI كامل من اليوم الأول.
2. لا يُسمح للـRouter بإصدار قرار دون evidence/freshness/conflict/dependence controls المطبقة على المسار.
3. أي Decision Contract أو Boundary جديد يعمل أولًا في replay/shadow/evaluation قبل الاعتماد الحي.
4. لا يُعرض numeric confidence أو probabilistic boundary قبل وجود calibration موثقة وoutcome history كافية.
5. أي ترقية من rule-based إلى adaptive/probabilistic behavior تحتاج evidence، regression، human validation، وحدود rollback/abstention.
6. Live promotion هي آخر مرحلة، ولا تُستنتج من PASS_ENGINEERING أو replay أو shadow evidence.
7. إذا لم تتوافر بيانات كافية للمعايرة، يكون السلوك الصحيح هو qualitative uncertainty / Data Limited / ABSTAIN، وليس اختراع نسبة رقمية.

### ترتيب تنفيذ Router/Decision Intelligence المسموح

Intent parsing محدود → Candidate selection بقواعد واضحة → Mandatory risk controls → Freshness/quality filtering → Dependence/conflict detection → Decision Contract qualitative → Rule-based Boundary + validity window → Shadow evaluation → Calibration → Adaptive enhancement عند ثبوت الحاجة → Live promotion فقط بعد استيفاء البوابات الحاكمة.

# 2. المعمارية النهائية للخبرة

المعمارية المنقحة تفصل بوضوح بين “واجهة المستخدم”، “تنسيق الذكاء”، “عقد القرار”، و“طبقات الأدلة/الحوكمة”.

USER → Calm Surface / Universal Command → Intent & Context Resolver → Intelligence Router → Playbook/Capability Selection → Decision Engine → Decision Contract → Six Heroes / Workspaces / Contextual Surfaces → Evidence & Trust Views → Capability Explorer / Graph / Institutional Data Room

لا يجوز أن يقفز أي مسار من الطلب مباشرة إلى نتيجة قرار بدون المرور بالضوابط المطبقة عليه: entitlement، data freshness، evidence class، conflict/uncertainty handling، وruntime canonical binding.

# 3. Surface Calm — الواجهة الرئيسية

يبقى Dashboard اليومي محدودًا في عدد الأسطح الأساسية. لا تظهر مكتبة القدرات كقائمة طويلة. الحد التشغيلي المقترح للسطح اليومي: Six Heroes + Today’s Focus + Top Opportunity/Key Risk + What Changed + Universal Command + My Stack بصورة مختصرة.

| Surface Budget — إضافة Workspace أو Recommendation أو Graph إلى الصفحة الأولى تتطلب إثبات أنها تخفض time-to-insight أو ترفع task success، لا مجرد أنها “مفيدة”. |

| --- |





# 4. Six Heroes — ثابت معماري

يظل الأبطال الستة الواجهة اليومية المبسطة. القدرات يمكن أن تغذي Hero أو تقدم Context أو لا ترتبط به. العلاقة لا تعني causal ownership. أي ربط في Capability Graph يجب أن يكون typed edge.

# 5. Today’s Focus — Decision Snapshot آمن

يعرض ملخصًا قصيرًا مثل Market State / Main Opportunity / Primary Risk / What Changed، لكن كل نتيجة يجب أن تحمل Safety Floor مختصرًا.

| عنصر Safety Floor | الحد الأدنى الظاهر |

| --- | --- |

| Freshness | timestamp أو freshness band |

| Evidence state | Historical/Shadow/Live/Delayed حسب الحقيقة |

| Uncertainty | High/Medium/Low أو calibrated probability إذا ثبتت |

| Critical contradiction | أهم تعارض مادي إن وُجد |

| Critical limitation | أي قيد يمكن أن يغير تفسير النتيجة |

| Invalidation / Next check | متى يعاد التقييم أو متى يصبح الاستنتاج غير صالح |





# 6. Universal Intelligence Command + Intent Search

البحث لا يقتصر على أسماء القدرات. يجب أن يدعم سؤال المستخدم باللغة الطبيعية، والأصول، والـPlaybooks، والـAlerts، والـResearch، والـAPI resources. Intent Search يفكك الطلب إلى Intent Contract بدلاً من استدعاء قدرات بصورة عشوائية.

| Intent Contract | المحتوى |

| --- | --- |

| Goal | ما الذي يحاول المستخدم معرفته/فعله؟ |

| Asset / scope | الأصل، السوق، المحفظة، chain أو universe |

| Horizon | لحظي / intraday / أيام / أسابيع... |

| Decision type | Opportunity / Risk / Due Diligence / Monitoring... |

| Required safety lenses | عوامل لا يجوز إسقاطها لهذا النوع من القرار |

| Evidence minimum | الحد الأدنى المقبول من freshness/coverage/trust |

| Output mode | Answer / Playbook / Alert / Deep Dive |





# 7. Workspaces / Missions

تبقى Workspaces طبقة تنظيمية بين Dashboard والمكتبة، لكن لا تُعامل كل مساحة عمل كنظام مستقل. هي composition views تعيد استخدام القدرات والـPlaybooks والـSSOT الحالية. يفضل إطلاق عدد محدود أولًا ثم التوسع بناءً على الاستخدام.

أمثلة مرشحة: Market Opportunity، Whale Intelligence، Risk Center، Asset Deep Dive، Portfolio Command Center، Derivatives، On-Chain، Narrative/Sentiment، Macro، DeFi، Quant Lab، Institutional Research، Developer/API Center.

# 8. Playbooks — Product Core مع Governance Contract

الـPlaybook ليس checklist جميلًا؛ هو workflow قابل للإصدار والاختبار. BLACKDARK Official Playbooks فقط هي التي تحمل علامة رسمية بعد تحقق محدد.

| Playbook Contract | مطلوب |

| --- | --- |

| Purpose / decision | القرار أو السؤال الذي يخدمه |

| Eligible regimes | الأسواق/الظروف التي يكون صالحًا فيها |

| Required capabilities | المدخلات الإلزامية والاختيارية |

| Dependence model | تجميع الإشارات المشتركة المصدر/النموذج حتى لا تُحسب مستقلة |

| Rules / weights | قواعد الدمج، التعارض، والأولوية |

| Version & lineage | نسخة القواعد والمصادر/النماذج |

| Validation | replay / walk-forward / shadow حسب applicability |

| Failure & abstention | متى يرفض إصدار نتيجة |

| Expiry / revalidation | صلاحية وإعادة تحقق |

| Change history | سبب وأثر التغيير |





# 9. Capability Explorer — المكتبة الصحيحة

الـCapability Library تُعرض كـDiscovery surface غني، لا كجدول 800 صف. كل بطاقة تستخدم metadata من SSOT، ولا تنشئ مصدر حقيقة مستقلًا.

| حقول البطاقة | ملاحظات |

| --- | --- |

| Name + one-line purpose | لغة المستخدم، لا المصطلحات الداخلية |

| When should I use it? | حالة استخدام واحدة واضحة |

| Category / Asset / Chain / Horizon | faceted taxonomy |

| Tier / API availability | من entitlement SSOT |

| Freshness / Coverage | أبعاد مستقلة |

| Assurance / Maturity | أبعاد مستقلة عن freshness |

| Known limitations | ظاهر ويمكن فتح التفاصيل |

| Methodology / Lineage / Evidence | روابط إلى المصدر الحاكم |

| Actions | Open / Add to My Stack / Use in Playbook / Create Alert |





# 10. Multi-dimensional Taxonomy

لا تستخدم شجرة واحدة. capability قد تكون Whale + On-chain + Risk + BTC + Elite. الأبعاد تكون faceted وقابلة للبحث. يمنع إنشاء tags حرة غير محكومة إذا كانت ستتحول إلى SSOT غير منضبط.

# 11. Trust Dimensions — تصحيح جذري لـTrust Status

يُلغى مفهوم “Trust Status واحد” الذي يخلط Verified/New/Live/Delayed/Data Limited. تُعرض الحالة في أبعاد مستقلة؛ يمكن للمستخدم رؤية شارة مختصرة، لكن المصدر يحتفظ بالمتجه الكامل.

| البعد | قيم مثال | ملاحظة |

| --- | --- | --- |

| Assurance | Verified / Experimental / Unverified | لا يعني live. |

| Freshness | Live / Near-live / Delayed / Stale | زمن البيانات فقط. |

| Availability | Healthy / Degraded / Unavailable | حالة الخدمة. |

| Coverage | Full / Partial / Limited | نطاق البيانات. |

| Methodology maturity | Stable / New / Under Review | نضج المنهج. |

| Evidence class | Replay / Forward Shadow / Verified Production / Independent | لا ترقية ضمنية. |





| منع الالتباس — قد تكون القدرة Verified + Delayed + Limited في نفس اللحظة. لذلك لا يجوز اختزال هذه الأبعاد في status واحد. |

| --- |





# 12. Progressive Disclosure مع Safety Floor

المستويات الخمسة تبقى: Answer → Why → Drivers → Evidence → Expert. لكن لا يجوز أن يُخفي المستوى الأول أي معلومة مادية قد تغيّر القرار.

| المستوى | المحتوى |

| --- | --- |

| Level 1 — Answer | النتيجة + uncertainty + freshness + critical contradiction/limitation + invalidation/next check |

| Level 2 — Why | سبب مختصر ومفهوم |

| Level 3 — Drivers | العوامل الحاسمة واتجاه كل عامل |

| Level 4 — Evidence | المصادر، الزمن، lineage، historical/shadow evidence |

| Level 5 — Expert | methodology/formula/model/version/assumptions/limitations/API |





# 13. My Stack

My Stack يحفظ Favorites / Recent / Saved Searches / Playbooks / Alerts ويتيح Dashboard شخصيًا. التخصيص لا يغير الحقيقة الأساسية للقدرة، ولا يسمح بأن يصبح preference دليلاً ماليًا.

# 14. Role-Based Experience — Preference وليس قيدًا

سؤال الدور في onboarding اختياري وقابل للتغيير والتجاوز. دوره ضبط default surfaces والمصطلحات وعمق العرض والتوصيات، وليس منع القدرات أو تثبيت المستخدم في persona.

# 15. Discovery & Recommendation Engine

يجب الفصل معماريًا بين Popularity وRelevance وQuality وTrust وPersonalization حتى لا تتحول الشعبية إلى حلقة تغذية ذاتية.

| Signal | الاستخدام المسموح |

| --- | --- |

| Popularity | اكتشاف اجتماعي فقط؛ لا يعادل جودة أو ملاءمة |

| Relevance | ارتباط بالسياق/الأصل/الهدف الحالي |

| Trust/Quality | هل الدليل كافٍ، حديث، موثوق؟ |

| Personalization | تفضيلات وسلوك بإذن المستخدم؛ لا يُعامل كحقيقة سوق |

| Novelty | يمكن استخدامه للتنوع، لا لرفع الثقة تلقائيًا |





كل توصية ذكية يجب أن تحمل “Why this is being recommended” ومصدر العوامل المؤثرة، مع منع feedback loop الذي يجعل الاستخدام نفسه دليلًا على الملاءمة.

# 16. Contextual Capabilities

القدرات تظهر داخل السياق الطبيعي: asset، position، wallet، opportunity، risk، إلخ. لكن contextual placement لا يغيّر canonical semantics أو entitlement. هو surface إضافي لنفس القدرة.

# 17. ثلاثة أسطح للقدرات

| السطح | الغرض |

| --- | --- |

| Operational Intelligence | قرارات يومية عبر Dashboard/Heroes/Widgets/Workspaces |

| Specialist Intelligence | تحليل عميق عبر Explorer/Deep Dive/Playbooks |

| Institutional Infrastructure | lineage, APIs, models, methodology, controls, SLO/evidence عبر Data Room |





# 18. Capability Graph — Typed Evidence Graph

يحتفظ بالمفهوم، لكن كل edge يجب أن يكون له نوع؛ ممنوع استخدام سهم مبهم يوحي بالسببية.

| Edge Type | المعنى |

| --- | --- |

| DATA_FEEDS | A يزوّد B ببيانات |

| DERIVED_FROM | B مشتق من A |

| SUPPORTS | A يدعم الاستنتاج B دون إثبات سببية |

| CONTRADICTS | A يعارض B |

| USED_BY | A يستخدمه workflow/hero B |

| CANONICAL_REUSE | ID يعيد استخدام canonical owner |

| EVIDENCE_FOR | artifact يدعم claim |

| CAUSES | ممنوع إلا بدليل سببي مصرح ومناسب |





# 19. Institutional Data Room — View فوق SSOT لا 15 نظامًا جديدًا

Data Room لا يبني Registries موازية. هو طبقة بحث وعرض تجمع المصادر الحاكمة الموجودة بالفعل. تظهر فقط registries الفعلية الموجودة، ويضاف أي registry جديد فقط عند وجود متطلب مستقل حقيقي.

الحد الوظيفي المقترح: Capability / Data Source / Lineage / Model or Rule / Methodology / API / Evidence / Version / Freshness & Quality / Reliability / Security Controls / Audit / Limitations / Change History — ويمكن أن تكون هذه Views فوق سجلات مشتركة بدل جداول منفصلة.

# 20. Subscription Discovery

يجوز إظهار teaser للقدرات المدفوعة بما يتوافق مع خطة التسعير، لكن لا يجوز عرض claim حي أو نتيجة مخصصة غير متاحة فعليًا ثم إخفاء الدليل خلف الدفع. Preview يجب أن يكون صادقًا وقابلًا للتفسير ويبيّن ما هو متاح وما يتطلب ترقية.

# 21. Accessibility & Interaction Quality

هدف الإتاحة: WCAG 2.2 AA حيث ينطبق. تشمل الاختبارات الفعلية keyboard navigation، focus visibility وعدم حجبه، target size، predictable navigation، accessible authentication، screen-reader semantics، وعدم الاعتماد على اللون وحده. اختصار Cmd/Ctrl+K يجب ألا يصطدم بقواعد keyboard shortcuts ويجب أن توجد وسيلة بديلة قابلة للاكتشاف.

# 22. BLACKDARK Intelligence Router — عقد اختيار مؤسسي

الـRouter ليس UI helper؛ هو decision-orchestration subsystem. لذلك لا يجوز بناءه كـblack-box “يختار أفضل 8” بدون عقد اختيار واختبارات.

## 22.1 Router Selection Contract

| المرحلة | القاعدة |

| --- | --- |

| 1 Intent | تحويل السؤال إلى goal/scope/horizon/decision type |

| 2 Mandatory controls | إضافة lenses إلزامية حسب نوع القرار؛ لا يمكن حذفها لتحسين السرعة |

| 3 Candidate eligibility | استبعاد ما لا يحقق freshness/coverage/rights/availability/entitlement |

| 4 Dependence clustering | تجميع القدرات ذات source/model ancestry المشترك لمنع عدها كأدلة مستقلة |

| 5 Conflict coverage | ضمان وجود evidence مؤيد ومعارض/مضاد عندما يكون القرار حساسًا |

| 6 Marginal value | إضافة قدرة فقط إذا تضيف information/coverage مادية |

| 7 Budget | حد latency/compute/cost واضح |

| 8 Stop | التوقف عندما تتحقق coverage requirements ولا توجد إضافة مادية ضمن الميزانية |

| 9 Abstain | إذا لم يتحقق minimum evidence أو التعارض غير محسوم أو البيانات متدهورة بصورة مادية |

| 10 Explain | إظهار لماذا اختيرت/استبعدت أهم القدرات |





| تعريف sufficient — لا تستخدم عبارة “minimum sufficient set” إلا إذا كانت sufficiency معرفة بمتطلبات coverage/mandatory controls/independence/quality وstopping criteria قابلة للاختبار. |

| --- |





# 23. Decision Contract Layer — الإضافة الحاكمة

كل نتيجة رئيسية من Router أو Official Playbook تتحول إلى Decision Contract قابل للحفظ والتتبع، لا إلى “حكم” عابر.

| الحقل | المطلوب |

| --- | --- |

| Current stance | Opportunity / Risk / Neutral / Abstain أو domain-specific |

| Decision scope | asset/universe/horizon/user context |

| Confidence vector | Evidence coverage / Data quality / Signal agreement / Calibration / Regime familiarity / Staleness |

| Key drivers | 3–5 عوامل حاسمة |

| Contradictions | أهم عوامل المعارضة ووزنها/أهميتها |

| Decision Boundary | الشروط التي ستغير القرار |

| Invalidation conditions | متى يصبح القرار غير صالح |

| Validity window | إلى متى يبقى القرار قابلًا للاستخدام قبل إعادة التقييم |

| Next check / trigger | زمن أو حدث يعيد الحساب |

| Evidence class | replay/shadow/live/... بدون ترقية |

| Version lineage | rule/model/data/evaluator version |





# 24. Confidence & Uncertainty Contract — منع False Precision

الـConfidence الافتراضي يكون متجهًا متعدد الأبعاد. لا تظهر نسبة مثل 82% إلا إذا كانت probabilistic meaning محددة وتمت معايرتها وقياس calibration error على data غير مستخدمة في توليد التوقع، مع disclosure مناسب.

لا تستخدم agreement count كاحتمال.

لا تعد إشارات مترابطة كأدلة مستقلة.

عند نقص evidence يجب خفض confidence أو abstain، لا تعويضه بلغة واثقة.

إذا عُرض composite confidence فيلزم إبقاء مكوناته قابلة للفحص وعدم إخفاء ضعف بعد واحد خلف متوسط مرتفع.

# 25. Decision Boundary Contract — المواصفة التنفيذية

| الحقل | التعريف |

| --- | --- |

| Variable(s) | المتغير أو مجموعة المتغيرات الحاسمة |

| Direction | above/below/cross/condition change |

| Threshold | قيمة أو قاعدة قابلة لإعادة الإنتاج |

| Uncertainty band | نطاق عدم يقين حول الحد إن وجد |

| Persistence | مدة/عدد مشاهدات قبل اعتبار الكسر حقيقيًا |

| Regime | السياق الذي يكون الحد صالحًا فيه |

| Validity window | صلاحية زمنية للحد |

| Conflict rule | ماذا يحدث إذا تحققت شروط متعارضة |

| Recompute trigger | متى يُعاد حساب الحد |

| Evidence | الدليل/المعايرة/النسخة |





يمنع oscillation غير المفيد عبر hysteresis/persistence عند الحاجة. الحدود غير القابلة للمعايرة لا تُعرض كأرقام دقيقة؛ يمكن عرض qualitative invalidation condition.

# 26. Temporal Validity / Confidence Decay

يُحتفظ بفكرة اضمحلال الثقة، لكن تُزال أي نسبة إلى Grinold Fundamental Law. decay يجب أن يُشتق من predictive horizon، source staleness، regime drift، calibration history أو empirical half-life حيث تتوفر الأدلة. إذا لم تتوفر معايرة، يعرض النظام next recheck/freshness بدل “ساعة علمية” زائفة.

# 27. Silent Confirmation Network — Dependence-aware

لا تعرض “7 تؤيد / 2 تعارض” باعتبارها 9 أصوات مستقلة. تعرض شبكة التأكيد عددًا خامًا + effective independent evidence بعد clustering للمصادر/النماذج/المشتقات المشتركة، مع إبراز contradictions الحقيقية.

# 28. Mirror Ledger — Personal Decision History

يمكن دمج My Stack مع سجل شخصي يقارن قرارات المستخدم بنتائج BLACKDARK، لكن هذا أصل محتمل وليس moat مثبتة. يتطلب consent، privacy، retention policy، portability، outcome linking، ومنع اعتبار سلوك المستخدم ground truth ماليًا.

# 29. Human Validation & Usability Evaluation Loop

هذه الإضافة إلزامية حتى تكون الإشارة إلى ISO 9241-210 عملية وليست تجميلية. التصميم يمر بدورات اختبار مع مستخدمين ممثلين وسياقات حقيقية.

| المقياس | مثال قبول أولي — يحدد المشروع الرقم النهائي قبل الاختبار |

| --- | --- |

| Task success | هل أكمل المستخدم المهمة الصحيحة دون مساعدة؟ |

| Time-to-insight | الوقت للوصول إلى استنتاج قابل للتصرف |

| Comprehension | هل فهم السبب/القيود/عدم اليقين؟ |

| Critical omission rate | هل فاتته limitation أو contradiction مادية؟ |

| Decision reversal after explanation | هل التفسير كشف فهمًا خاطئًا؟ |

| Over-reliance / automation bias indicators | هل اتبع النظام رغم evidence ضعيف أو warning واضح؟ |

| Perceived control | هل يعرف كيف يفتح الأدلة/يغير الهدف/يرفض recommendation؟ |

| Accessibility task completion | keyboard/screen reader/focus/authentication tasks |





| قاعدة المطابقة — لا تدّعي “ISO 9241-210 compliant” اعتمادًا على بنية الصفحات وحدها؛ يلزم عملية human-centred design وأدلة تقييم مناسبة. |

| --- |





# 30. Runtime / Cost / Performance Budget

يجب ألا يتحول Router إلى عنق زجاجة. كل intent/playbook يملك budget: maximum candidate set، maximum selected set، latency class، cache policy، degradation path، cost ceiling، ومتى ينتقل إلى asynchronous/deep analysis. القياس الفعلي يحدد الحدود؛ لا تُفرض أرقام Nielsen أو p95 بلا أساس مادي.

# 31. Integration Contract مع الواقع الهندسي

هذه الوثيقة لا تعيش في عالم موازٍ. قبل تنفيذ أي عنصر، يجب أن يُربط بالـSSOT الحالي للمشروع: capability IDs، canonical decisions، RTM، runtime bindings، entitlement، evidence/Temporal classes، data provenance، active status dimensions. لا يجوز إنشاء “مكتبة جديدة” تنسخ نفس البيانات.

| قاعدة | التطبيق |

| --- | --- |

| Canonical identity | كل UI card/router candidate يستخدم canonical ID/alias من المصدر الحاكم |

| Runtime truth | أي capability يرشحها Router يجب أن تصل فعليًا إلى canonical runtime proven implementation |

| Status truth | واجهة Trust Dimensions تُشتق من الأبعاد الحاكمة ولا تخترع status جديدًا غير قابل للتتبع |

| Evidence truth | Decision Contract يربط artifacts/versions والتصنيف الزمني الصحيح |

| Entitlement | كل surface يستخدم نفس entitlement authority؛ لا bypass |

| Historical preservation | أي تغير status/binding لا يمحو evidence تاريخي لكنه لا يبقيه claim حاليًا |





# 32. خطة التنفيذ المرحلية — منع تضخم النطاق

| المرحلة | المكونات | شرط الانتقال |

| --- | --- | --- |

| P0 — Foundations | Capability metadata contract، Trust Dimensions، typed graph edges، Safety Floor، SSOT adapters | لا stale/parallel truth؛ metadata completeness على العينة المستهدفة |

| P1 — Sellable UX Core | Calm Surface، Six Heroes، Today’s Focus، Universal Command/Intent v1، Capability Explorer | اختبارات مستخدمين + task success/comprehension مقبولة |

| P2 — Guided Intelligence | Official Playbooks، Contextual Capabilities، My Stack، Workspaces محدودة | playbook validation + retention/usage evidence |

| P3 — Router v1 + Decision Contract | deterministic/transparent routing، mandatory controls، conflict handling، abstention، boundaries | runtime semantic proof + calibration/decision safety evaluation |

| P4 — Smart Discovery | recommendations، dependence-aware confirmation، temporal validity | feedback-loop controls + recommendation evaluation |

| P5 — Personal/Institutional Expansion | Mirror Ledger، advanced personalization، Institutional Data Room views | privacy/consent + B2B/user evidence |





لا يبدأ P3 فقط لأن P1/P2 مكتوبة في المواصفة؛ يبدأ عندما تكون foundation evidence والـhuman validation جاهزة. ويمكن تنفيذ بعض البنية تحتية بالتوازي إذا كانت موجودة بالفعل في v4_v2/Temporal، لكن لا يُنشأ بديل جديد.

# 32.1 المخاطر التنفيذية المتبقية — Residual Execution Risks

هذه المخاطر ليست عيوبًا مفتوحة في الوثيقة التصميمية نفسها؛ هي مخاطر تنفيذ/تحقق يجب أن تبقى ظاهرة حتى تثبت بالأدلة.

| الخطر | المستوى | المعالجة الإلزامية | شرط خفض الخطر |
| --- | --- | --- | --- |
| Router + Decision Contract production complexity | عالي | تنفيذ مرحلي deterministic، observability، replay/shadow، rollback، abstention | استقرار سلوك runtime تحت بيانات وتعارضات حقيقية |
| Confidence/Boundary calibration | عالي | لا false precision؛ confidence vector أولًا؛ calibration فقط من outcome history مناسبة | calibration error/coverage/validity موثقة حسب use case |
| Concept/subsystem density | متوسط | الالتزام الصارم بـP0–P2 وعدم بناء P3–P5 قبل بواباتها | عدم تجاوز Surface Budget وroadmap gates |
| Human Validation | متوسط | اختبار مبكر مع مستخدمين ممثلين ومهام واقعية وقياسات comprehension/task success | evidence من دورات اختبار حقيقية + إصلاح وإعادة اختبار |
| Runtime/Cost Budget | متوسط | instrumentation وقياس latency/compute/cache/data/API cost | budgets رقمية مبنية على قياس فعلي لا تقدير |
| Competitive differentiation claims | منخفض–متوسط | اعتبارها hypothesis حتى competitive verification حديث | evidence market/competitor/user validation |

**قاعدة المخاطر:** لا يجوز تحويل أي عنصر في هذا الجدول إلى CLOSED لمجرد أن التصميم يذكر ضابطًا له؛ الإغلاق يحتاج evidence من التنفيذ أو الاختبار المناسب.

# 33. معايير قبول التصميم قبل البناء الواسع

كل surface له هدف مستخدم واضح ومقياس نجاح، وليس مجرد قائمة وظائف.

لا توجد معلومات مادية مخفية في Progressive Disclosure.

كل status ظاهر للمستخدم قابل للتتبع إلى dimension حاكم.

كل Router selection قابل للشرح ويحتوي mandatory controls وabstention.

كل Decision Boundary له contract أو يُعرض qualitative فقط.

لا numeric confidence بلا تعريف ومعايرة.

كل Capability Graph edge typed؛ لا causal implication بلا evidence.

كل Official Playbook versioned ومتحقق ومحدد الصلاحية.

كل recommendation تفصل popularity عن relevance/trust.

Data Room يعرض SSOT ولا ينسخه.

WCAG 2.2 AA target مغطى في design/test plan.

يوجد human validation cycle قبل اعتبار التصميم نهائيًا للاستخدام.

# 34. مصفوفة العيوب القاتلة وإغلاقها

| العيب | الخطورة | المعالجة في v4 | الحالة |

| --- | --- | --- | --- |

| Router “minimum sufficient” بلا تعريف | Critical | Router Selection Contract + mandatory controls + dependence + stop/abstain | CLOSED IN DESIGN |

| Confidence 82% بلا معنى/معايرة | Critical | Confidence vector + numeric only when calibrated | CLOSED IN DESIGN |

| Decision Boundary نظري | Critical | Boundary Contract: threshold/band/persistence/regime/validity | CLOSED IN DESIGN |

| Trust Status أحادي الأبعاد | Critical | Multi-dimensional Trust Dimensions | CLOSED IN DESIGN |

| Progressive Disclosure يخفي مخاطر | Critical | Safety Floor always visible | CLOSED IN DESIGN |

| Graph يوحي بالسببية | Critical | Typed edges؛ CAUSES فقط بدليل | CLOSED IN DESIGN |

| غياب Human Validation Loop | Critical | مقاييس ودورات اختبار مستخدمين | CLOSED IN DESIGN |

| كثافة الطبقات | High | Surface Budget + phased rollout | MITIGATED |

| Router مصنف كـUI بسيط | High | تعريفه كـorchestration subsystem | CLOSED IN DESIGN |

| لا MVP sequencing | High | P0–P5 roadmap | CLOSED IN DESIGN |

| Data Room متضخم | High | Views over existing SSOT؛ لا registries موازية | MITIGATED |

| Popularity feedback loop | High | فصل popularity/relevance/trust/personalization | CLOSED IN DESIGN |

| Playbook credibility | High | Playbook Governance Contract | CLOSED IN DESIGN |

| Confidence Decay misattributed to Grinold | Scientific | إزالة النسبة؛ empirical temporal validity | CLOSED |

| Signal concurrence يعد المترابط مستقلًا | High | Dependence-aware effective evidence | CLOSED IN DESIGN |

| Mirror Ledger اعتبر moat تلقائيًا | Medium | Potential moat فقط + privacy/consent/outcome requirements | CORRECTED |

| فصل الرؤية عن الكود/SSOT | Critical Execution | Integration Contract + reuse-before-build | CLOSED IN DESIGN |

| تكلفة التشغيل غير محددة | High | Runtime/Cost/Performance Budget | MITIGATED |





# 35. نتيجة المراجعة السداسية المستويات

| المستوى | ما تم فحصه | الحكم |

| --- | --- | --- |

| L1 — Completeness | الأقسام 1–20 + الإضافة + الشكل النهائي + المعيار الختامي | كل الأفكار الجوهرية محفوظة أو مصححة صراحة؛ لا إسقاط جوهري. |

| L2 — Defect Reconciliation | تقرير العيوب 1 + تقرير العيوب 2 + العيوب اللاحقة | كل Critical/High defect له معالجة أو قيد تنفيذ واضح. |

| L3 — Standards Attribution | ISO 9241-210/11، ISO 25010/25012، NIST AI RMF، ISO 23894/42001، WCAG 2.2 | تم فصل ما تدعمه المعايير عن Project Design؛ إزالة attribution الخاطئ. |

| L4 — Decision Safety | confidence، boundary، contradictions، abstention، automation-bias risks | أضيف Decision Safety & Orchestration Contract. |

| L5 — Engineering Executability | SSOT، runtime binding، entitlement، reuse، performance/cost، phases | تحولت الرؤية إلى عقود تنفيذ ومرحلية؛ لا تُبنى أنظمة موازية. |

| L6 — Traceability & Acceptance | قبول التصميم، human validation، evidence/status lineage | أضيفت gates واضحة قبل الانتقال والتنفيذ الواسع. |





# 36. الحكم النهائي للنسخة v4

| APPROVED AS INSTITUTIONAL DESIGN SPECIFICATION — هذه النسخة صالحة كمرجع تصميم/حوكمة/تنفيذ مرحلي بعد دمج العيوب المعروفة. ليست إعلانًا بأن كل المكونات مبنية أو مطابقة/معتمدة رسميًا. التنفيذ يحتاج RTM وربط SSOT واختبارات runtime وhuman validation وأدلة فعلية وفق المعايير الحاكمة للمشروع. |

| --- |





العبارة الختامية المعتمدة:

Surface Calm. Intelligence Deep. Discovery Everywhere. Complexity On Demand. Evidence Always. Safety Never Hidden.

The user chooses the goal; BLACKDARK chooses the machinery — and always shows the evidence, uncertainty, limits, and what would change the decision.

# ملحق A — تصحيح العبارات المعيارية والعلمية

| العبارة القديمة/المحتملة | الحكم | الصياغة الصحيحة |

| --- | --- | --- |

| Progressive Disclosure “متوافق مع ISO 9241” | PARTIALLY SUPPORTED | هو قرار HCD/UX متسق مع مبادئ تقليل التعقيد؛ ISO لا يفرض هذه التقنية بعينها. |

| Trust Card “متطلب NIST” | MISATTRIBUTED إذا صيغ كذلك | هو تصميم BLACKDARK يدعم transparency/explainability/validity objectives. |

| Data Room 15 registries “وفق ISO 25010/25012” | PROJECT DESIGN | المعياران يقدمان نماذج جودة؛ لا يفرضان هذه البنية. |

| Confidence Decay تطبيق مباشر لـGrinold | MISATTRIBUTED | يبنى على staleness/horizon/drift/calibration empirical evidence. |

| Decision Boundary فريد ولا منافس يقدمه | UNVERIFIED COMPETITIVE CLAIM | يحتاج بحثًا تنافسيًا حديثًا قبل استخدامه تسويقيًا. |

| 70% معروف / 2 عناصر فقط مميزة | QUALITATIVE | رأي تحليلي وليس قياسًا علميًا. |





# ملحق B — المراجع الرسمية

[S1] ISO 9241-210:2019 — Ergonomics of human-system interaction — Human-centred design for interactive systems. https://www.iso.org/standard/77520.html

[S2] ISO 9241-11:2018 — Usability: Definitions and concepts. https://www.iso.org/standard/63500.html

[S3] ISO/IEC 25010:2023 — SQuaRE — Product quality model. https://www.iso.org/standard/78176.html

[S4] ISO/IEC 25012:2008 — SQuaRE — Data quality model (confirmed current in 2025). https://www.iso.org/standard/35736.html

[S5] NIST AI Risk Management Framework (AI RMF 1.0), NIST AI 100-1. https://www.nist.gov/itl/ai-risk-management-framework

[S6] ISO/IEC 23894:2023 — Artificial intelligence — Guidance on risk management. https://www.iso.org/standard/77304.html

[S7] ISO/IEC 42001:2023 — Artificial intelligence management system. https://www.iso.org/standard/42001

[S8] W3C Web Content Accessibility Guidelines (WCAG) 2.2. https://www.w3.org/TR/WCAG22/