# BLACKDARK — دراسة تصميم لوحة التحكم النفسية والتجارية

> **Status:** Binding design research (internal) · English-only on public UI  
> **Date:** 2026-08-06  
> **Lens:** Marketing psychology · Commercial product design · Habit loops  
> **Constraint (UI):** Six Heroes + Section Z — **no seventh retail button**  
> **Constraint (Product — أعلى):** Constitution **D1–D8** + **Eight Capabilities** — ملزمان  
> **Goal:** لوحة «أقصى درجة سهولة» تخلق اعتماداً ذهنياً مستمراً دون تشتت

---

## 0) الحكم التنفيذي (ما نبنيه ولماذا)

المنافسون يبيعون **لوحات مزدحمة**. نحن نبيع **قرار واحد مثبت**.

### 0.1 طبقات ملزمة — لا تُخلط (تصحيح مهم)

| طبقة | العدد | المصدر | ماذا تعني للوحة |
|------|-------|--------|------------------|
| **D1–D8 Differentiators** | **8** | `PRODUCT_CONSTITUTION_AR.md` §2 — ما طوّره المفوض كأصل فريد | يجب أن يظهر أثرها في التجربة (إثبات، فيتو، Net-Edge، Half-Life، Regime، Evidence، Persona، Registry) — حتى لو لم يكن لكل واحدة «تاب» منفصل |
| **Eight Capabilities** | **8** | الدستور §3 | كل زر/قسم في اللوحة يُصنَّف تحت قدرة واحدة فقط أو يُحذف |
| **Six Heroes + Section Z** | 6 + 5 تعميقات | `HEROES_STRATEGY_BINDING.md` | **تغليف الواجهة** فقط — صقل ما يراه المستخدم؛ ليست بديلاً عن الـ 8 |

> جملة «مربوط بالأبطال الستة فقط» كانت تعني: **لا نفتح زراً تجزئة سابعاً يشتت الواجهة**.  
> **لا تعني** أن المنتج اختُزل إلى 6 أو أن D1–D8 أُلغيت. عند التعارض: الدستور يعلو.

| مبدأ | المعنى التشغيلي |
|------|------------------|
| One Composition | أول شاشة = علامة BLACKDARK + جملة Oracle واحدة + CTA واحد + حالة الثقة (Ledger) |
| Anti–Dashboard Tourism | لا تبويبات لا نهائية؛ العمق عبر 6 أبطال تغلف D1–D8 بصمت |
| Comfort → Habit → Dependence | راحة بصرية أولاً، ثم حلقة يومية، ثم اعتماد ذهني على النموذج |
| Prove-it Loop | كل جلسة تنتهي بـ Certificate قابل للمشاركة → فيروس إثبات لا فيروس ضوضاء |
| Four Tiers · One Ladder | Free → Observer → Pro → Whale (سلم واضح بلا تشتيت) |

**التعريف التجاري للنجاح:** المستخدم يعود دون تذكير، يفهم القيمة في 60 ثانية، ويدفع عندما يلمس «حافة» واضحة — لا عندما يرى 40 زراً.

---

## 1) التشخيص النفسي للوضع الحالي (فجوة)

| ظاهرة حالية | أثر نفسي | علاج تصميمي |
|-------------|----------|-------------|
| Scroll طويل بلا محطات | إرهاق معرفي / هروب | Shell ثابت + منطقة قرار واحدة + أدراج ثانوية |
| Audience ≠ UX mode | ارتباك هوية | وضع جمهور واحد يظهر في الشريط (Free/Observer/Pro/Whale) |
| ألوان hardcoded بلا tokens موحدة | عدم اتساق = قلق لا واعٍ | Design System واحد لكل الصفحات |
| لا Contact / Complaints / Model Info | غياب الأمان المؤسسي | Utility Rail ثابت (معلومات · تواصل · شكوى · اجتماعي) |
| 3 مستويات فقط في الكود | سلم تحويل ناقص | إضافة **Observer** كطبقة مجانية مدفوعة جزئياً / منخفضة السعر |
| Footer قانوني ناقص في Dashboard | فقدان ثقة | Compliance + Legal دائماً أسفل أي ناتج AI |

---

## 2) دراسة أقوى 20 نموذجاً — لماذا يرتبط المستخدم ذهنياً؟

معيار الاختيار: **ارتباط يومي + راحة + عادة** — لا «أجمل موقع».

| # | النموذج | حلقة العادة | درس لـ BLACKDARK |
|---|---------|-------------|------------------|
| 1 | **Bloomberg Terminal** | شاشة افتراضية ثابتة + رموز سريعة | ثبات مكان القرار؛ لا تتحرك عناصر القرار |
| 2 | **TradingView** | رسم بياني كموقع عاطفي + تنبيهات | الرسم خلف القرار لا أمامه؛ تجنب حد التنبيهات المسرحي |
| 3 | **Discord** | مجتمع + إشعارات ناعمة | Inbox داخل التطبيق كـ «منزل» يومي |
| 4 | **Telegram** | إشعار قصير → فتح فوري | 3 تنبيهات مجانية = خطاف عودة، ليس ضوضاء |
| 5 | **Notion** | فراغ هادئ + تقدم مرئي | مساحات سلبية كبيرة؛ كثافة منخفضة |
| 6 | **Linear** | سرعة + حالة واضحة | حالات النظام (Live / Degraded / Proof) ظاهرة دائماً |
| 7 | **Stripe Dashboard** | تسلسل دفع بسيط | Pricing كسلم لا ككتالوج |
| 8 | **Coinbase** | طمأنة بصرية + لغة بسيطة | Act/Wait بلغة بشرية لا jargon |
| 9 | **Nansen** | هوية «Smart Money» | نحن نعكسها: Signal vs Noise بدل label أعمى |
| 10 | **Arkham** | فضول تحقيقات | Curiosity داخل Whale — لا في الواجهة الأولى |
| 11 | **Glassnode** | تقارير دورية | Glass Box cadence = عادة أسبوعية عامة |
| 12 | **Binance** | كثافة عالية = إدمان قصير ثم إرهاق | **لا ننسخ الكثافة** — ننسخ فقط سرعة التنفيذ |
| 13 | **Robinhood** | بساطة مفرطة | البساطة عند الدخول؛ العمق عند الطلب |
| 14 | **Duolingo** | Streak + خسارة مؤلمة | Discipline Mirror = streak انضباط لا streak تداول متهور |
| 15 | **Strava** | مشاركة الإنجاز | مشاركة Decision Certificate لا P&L |
| 16 | **Spotify** | Discover Weekly | «Today’s Oracle» = طقس يومي ثابت الساعة |
| 17 | **Apple Fitness** | حلقات إكمال | حلقات: Ask → Decide → Certificate → Review |
| 18 | **Revolut** | طبقات اشتراك واضحة | 4 طبقات بصرية متدرجة اللون لا بعدد الميزات |
| 19 | **Figma** | Multiplayer presence | Fund Terminal = حضور مؤسسي هادئ |
| 20 | **ChatGPT** | صندوق واحد مهيمن | Oracle box = البطل البصري الوحيد في الـ viewport الأول |

### خلاصة الـ 20 نموذجاً (قانون واحد)

> **العادة تُبنى حول «مكان ثابت + نتيجة قصيرة + إثبات قابل للمشاركة» — لا حول قائمة ميزات.**

---

## 3) علم نفس الألوان والراحة (نظام بصري ثوري وهادئ)

### 3.1 لماذا لا نستخدم بنفسج AI الافتراضي؟

الأسواق المالية تربط البنفسج المتوهج بـ «hype». نحن نبيع **إثباتاً**. الاتجاه: **Deep Obsidian + Soft Cyan trust + Warm amber فقط للتحذير**.

### 3.2 لوحة BLACKDARK Comfort System (CSS tokens مقترحة)

| Token | قيمة مقترحة | وظيفة نفسية |
|-------|-------------|-------------|
| `--void` | `#07070C` | خلفية عميقة تقلل إجهاد الشاشة الطويلة |
| `--surface` | `#101018` | ألواح ناعمة بلا بطاقات مكدسة |
| `--elev` | `#171722` | تمييز خفيف للمناطق التفاعلية |
| `--line` | `#262633` | حدود همسية — لا أقفاص |
| `--ink` | `#E8E8ED` | نص أساسي مريح (أقل بياضاً من #fff) |
| `--mute` | `#8B8B97` | نص ثانوي دون اختفاء |
| `--trust` | `#2DD4BF` | لون الثقة (teal) بدل cyan الصارخ |
| `--prove` | `#5EEAD4` | تمييز الإثبات / Ledger |
| `--calm` | `#34D399` | نجاح هادئ (ليس أخضر نيون) |
| `--hold` | `#FBBF24` | Wait / Caution |
| `--stop` | `#F87171` | خطر مخفف التشبع |
| `--focus-ring` | `rgba(45,212,191,.35)` | تركيز لوحة المفاتيح |

**قواعد راحة:**
1. لا Glow متعدد الطبقات على الأزرار.  
2. لا Cards في الـ Hero.  
3. تباين نص ≥ WCAG AA.  
4. حركة = fade/slide 180–280ms فقط على دخول القرار والحالة.  
5. خط عرض: **IBM Plex Sans** أو **Söhne/Geist**-class — تعبيري لكن مؤسسي (لا Inter كافتراضي وحيد على كل السطح إن أمكن تمييز الهوية).

### 3.3 إيقاع بصري يطيل الجلسة

| تقنية | تطبيق |
|-------|--------|
| Progressive disclosure | المبتدئ يرى Oracle فقط؛ Pro يكشف Radar؛ Whale يكشف Stealth |
| Soft persistence | الشريط العلوي ثابت؛ المحتوى يتنفس |
| Ambient status | نقطة Live خضراء هادئة + آخر تحديث |
| Empty states دافئة | «Ask the Oracle» لا شاشات رمادية فارغة |
| Micro-reward | بعد القرار: شهادة تظهر بلطف (لا confetti) |

---

## 4) معمارية لوحة التحكم «أقصى سهولة» (Information Architecture)

### 4.1 الهيكل الثلاثي (Shell)

```
┌─────────────────────────────────────────────────────────────┐
│ BRAND · Audience Chip · Trust Pulse · Utility (ⓘ ✉ ⚠ 🔗) │
├──────────────┬──────────────────────────────┬───────────────┤
│              │                              │               │
│  RITUAL RAIL │     DECISION STAGE           │  CONTEXT DOCK │
│  (اليوم)     │     (بطل واحد)               │  (عند الطلب)  │
│              │                              │               │
│  · Oracle    │   Act / Wait + Why Top-3     │  Chart        │
│  · Ledger    │   Certificate                │  Radar        │
│  · Mirror    │   Compliance Footer          │  Whale S/N    │
│  · Inbox     │                              │  Stealth*     │
│  · Portfolio │                              │  MEV*         │
│              │                              │  (*Whale)     │
└──────────────┴──────────────────────────────┴───────────────┘
│ Legal · Social · Contact · Status · Model Capabilities     │
└─────────────────────────────────────────────────────────────┘
```

\* Stealth / MEV تظهر لجمهور Whale فقط — ليست أزراراً تجزئة للمنتج.

### 4.2 قانون الشاشة الأولى (Hero Budget)

مسموح فقط:
1. اسم العلامة **BLACKDARK** بحجم بطولي  
2. جملة Oracle واحدة (Act/Wait)  
3. جملة دعم قصيرة  
4. مجموعة CTA واحدة (Ask / Upgrade إن لزم)  
5. مؤشر ثقة واحد (Ledger hit أو «Proof live»)

ممنوع في أول viewport: إحصائيات متعددة · جداول · بطاقات ميزات · شارات عائمة · جداول أسعار.

### 4.3 أوضاع الجمهور (بدون سابع منتج)

| Audience | أول ما يراه | ما يُخفى حتى الطلب |
|----------|-------------|---------------------|
| Free | Oracle 10/day + Radar ملخص + Ledger رابط | Arb / Chat / Stealth |
| Observer | Oracle موسّع + Inbox + Mirror خفيف | Arb كامل / Evidence |
| Pro | OQS + Explain + Whale S/N + Portfolio | B2B Evidence |
| Whale | Stealth Advisor + Half-Life + MEV + Evidence | — |
| Fund | Emerging Terminal entry + Ledger | أدوات التجزئة |

---

## 5) حلقة الإدمان الصحي (Habit Loop) — ليس تلاعباً ضاراً

نفرّق بين **اعتماد على الإثبات** و**إدمان القمار**.

| مرحلة | محفز | فعل روتيني | مكافأة | استثمار |
|-------|------|------------|--------|---------|
| يوم 0 | Telegram / Share Certificate | أول Oracle | Act/Wait واضح | حساب مجاني |
| يوم 1–3 | تنبيه صباحي ناعم | نفس الرمز يومياً | مقارنة مع Ledger | Streak انضباط |
| يوم 4–7 | Glass Box / Locked | قفل توقع | ترقب عام | مشاركة اجتماعية |
| أسبوع 2 | Discipline Mirror | مراجعة سلوك | «كنت منضبطاً» | ترقية Observer/Pro |
| مستمر | Inbox + Certificate | جلسة قصيرة يومياً | ثقة متراكمة | Whale عند الحاجة التنفيذية |

**حارس أخلاقي (Binding):** Discipline Mirror يعاقب المبالغة في التداول — لا يكافئ عدد الصفقات.

---

## 6) أربعة مستويات اشتراك (واجهة تجارية)

### 6.1 السلم المقترح

| Tier | سعر إرشادي | وعد عاطفي | حدود واضحة |
|------|------------|-----------|------------|
| **Free** | $0 | «جرّب القرار» | 10 Oracle/day · Radar · Ledger عام · TG 3/day |
| **Observer** | $9–12/mo | «تابع بلا ضوضاء» | Oracle 50/day · Inbox كامل · Discipline Mirror · Alerts خفيفة |
| **Pro** | $29/mo | «حافة يومية» | Unlimited Oracle · AI Chat · Arb · Whale S/N · Portfolio AI · Trial 7d |
| **Whale** | $199/mo | «تنفيذ حذر» | + Stealth · Voice · B2B API · Evidence Pack · Priority |

> الكود الحالي: Free / Pro / Whale. **Observer** = طبقة تحويل مفقودة يجب إضافتها في المنتج + الفوترة حتى يكتمل السلم النفسي (تقليل قفزة $0→$29).

### 6.2 قواعد عرض Pricing (ثوري وبسيط)

1. بطاقة واحدة «مُوصى بها» فقط (Pro) — بدون شارات متعددة.  
2. مقارنة بـ **3 أسئلة** لا 20 ميزة:  
   - هل تريد قرارات غير محدودة؟  
   - هل تريد تصفية الحيتان من الضوضاء؟  
   - هل تريد حافة تنفيذ + إثبات للصناديق؟  
3. CTA: Free = Start · Observer = Observe · Pro = Trial · Whale = Apply / Checkout.  
4. أسفل كل بطاقة: رابط Ledger («نحن نثبت — لا نعد»).  
5. لا Emoji كثيف؛ أيقونات خطية هادئة.

### 6.3 شاشة Checkout Success النفسية

رسالة: «Your edge is unlocking» + خطة ظاهرة + روابط Legal + زر Dashboard — بدون احتفال صاخب.

---

## 7) Utility Rail — الأزرار التي «لا تُنسى»

شريط ثابت يمين/يسار أو قائمة `⋯` في الهيدر — **دائماً موجود في كل صفحة عامة**:

| زر | وظيفة | مسار مقترح |
|----|--------|------------|
| **Model Info / Capabilities** | ماذا يستطيع النموذج / ماذا لا يدّعي | `/capabilities` أو Drawer `#capabilities` |
| **Contact** | مبيعات / دعم | `/contact` + `mailto:support@…` / `sales@…` |
| **Complaints** | مسار شكوى رسمي (ثقة مؤسسية) | `/complaints` + رقم تذكرة |
| **Social** | روابط الملفات الرسمية | X · Telegram · (اختياري Discord لاحقاً) |
| **Legal** | Terms · Privacy · Disclaimer | موجودة — تُثبَّت في Dashboard أيضاً |
| **Status** | صحة النظام | `/health` ملخص أو صفحة status |
| **Accuracy** | Ledger | `/oracle-accuracy` |
| **Upgrade** | السلم | `/#pricing` أو modal tiers |

### 7.1 محتوى Drawer: Model Capabilities (Anti-Hype)

يجب أن يجيب بصراحة:
- يقدّم: Act/Wait + Explain + Certificate + Ledger  
- لا يقدّم: ضمان ربح · نصيحة استثمارية مرخّصة · DEX live بلا تكامل  
- مصدر الثقة: Public Accuracy Ledger + Compliance Footer  

### 7.2 قسم الشكاوى (مهم نفسياً)

وجود مسار شكوى **يزيد** الارتباط المؤسسي: المستخدم يشعر أن المنصة «تتحمل المسؤولية» — خاصة قبل الإطلاق الفيروسي.

حقول: البريد · نوع المشكلة (Billing / Accuracy / Abuse / Other) · الوصف · مرفق اختياري · رقم تذكرة فوري.

---

## 8) روابط التواصل الاجتماعي (عرض احترافي)

| قناة | دور | موضع |
|------|-----|------|
| Telegram Bot | عادة يومية مجانية | Landing + Dashboard Inbox + Footer |
| X (Twitter) | توزيع Certificates / Glass Box | Footer + Share على Certificate |
| (Later) Discord | مجتمع Pro/Whale | بعد وجود مشرفين |
| LinkedIn | مسار الصناديق | B2B / Emerging Terminal فقط |

**قاعدة:** أيقونات هادئة في Footer + زر Share على الشهادة — لا شريط أيقونات صاخب في الـ Hero.

---

## 9) قائمة المهام والمميزات — تقسيم تنفيذي

### P0 — أساس الراحة والاكتمال (قبل فيروس)

| # | مهمة | يعمّق |
|---|------|-------|
| P0.1 | Dashboard Shell ثلاثي (Ritual / Decision / Context) | Anti-tourism |
| P0.2 | توحيد Design Tokens على كل القوالب | راحة |
| P0.3 | Utility Rail: Capabilities · Contact · Complaints · Social · Legal | اكتمال |
| P0.4 | Pricing UI لأربع طبقات (+ Observer في المنتج) | تحويل |
| P0.5 | Audience chip متزامن مع الصلاحيات الفعلية | وضوح |
| P0.6 | Compliance Footer تحت كل ناتج AI في Dashboard | D7/Z5 |
| P0.7 | Footer قانوني + اجتماعي في Dashboard | ثقة |

### P1 — عادة يومية

| # | مهمة | يعمّق |
|---|------|-------|
| P1.1 | طقس «Today’s Oracle» في Ritual Rail | Habit |
| P1.2 | Inbox كمنزل إشعارات | Telegram loop |
| P1.3 | Discipline Mirror entry واضح | Z2 |
| P1.4 | Locked Predictions / Glass Box panel | Z1 |
| P1.5 | Share Certificate one-tap → X/TG | Viral proof |

### P2 — عمق الجمهور

| # | مهمة | يعمّق |
|---|------|-------|
| P2.1 | Whale: Stealth + MEV في Context Dock | Audience Whale |
| P2.2 | Fund: Emerging Terminal CTA | Z4 |
| P2.3 | Portfolio AI plain-language panel | Hero 4 |
| P2.4 | Signal vs Noise label بارز في Whale panel | Z3 |

### P3 — صقل فيروسي عالمي

| # | مهمة |
|---|------|
| P3.1 | Motion system (2–3 حركات فقط) |
| P3.2 | Empty/Loading/Error states موحدة |
| P3.3 | صفحة `/capabilities` عامة قابلة للفهرسة |
| P3.4 | صفحة `/contact` + `/complaints` |
| P3.5 | مواءمة Landing Pricing مع TIER_FEATURES الحقيقية |

---

## 10) خريطة الميزات → D1–D8 × الأبطال × القدرات (لا اختزال)

### 10.1 المميزات الثماني (D1–D8) — كيف تظهر في اللوحة دون زر سابع

| ID | الميزة الفريدة | أين يعيش في اللوحة (بدون تاب منفصل إجباري) | بطل / تعميق |
|----|----------------|---------------------------------------------|-------------|
| **D1** | Proof-Native Oracle | Certificate + رابط Ledger بعد كل قرار | Hero 3·6 |
| **D2** | Contradiction Veto | حالة Wait / Do Not Touch عند التعارض (داخل نتيجة Oracle) | Hero 5 |
| **D3** | Net-Edge Truth | شارة/سطر صافي الحافة في Arb وفرص Pro | Hero 1 |
| **D4** | Opportunity Half-Life | عدّاد عمر الفرصة في Context / Stealth (Whale) | Whale path |
| **D5** | Regime-Conditional | شريحة نظام السوق الهادئة فوق Decision Stage | Hero 1·5 |
| **D6** | Evidence Pack | CTA للصناديق داخل Fund/Whale — ليس صفحة تجزئة سابعة | Z4 |
| **D7** | Persona Clarity EN | وضع Beginner/Pro + جملة Act/Wait | Hero 5 |
| **D8** | Signal Registry | مصادر/أوزان مطوية تحت Explain («Why») | Hero 1·2 |

### 10.2 سطح الواجهة → بطل (تغليف فقط)

| ميزة سطح | البطل | D يُعزَّز | تظهر لـ |
|----------|-------|-----------|---------|
| Single-Sentence Oracle | Hero 5 | D1·D2·D7 | الجميع |
| Opportunity Score + Top-3 | Hero 1 | D3·D5·D8 | Observer+ |
| Whale + Signal vs Noise | Hero 2 / Z3 | D8 | Pro+ |
| Public Accuracy Ledger | Hero 3 | D1 | الجميع (عام) |
| Portfolio AI | Hero 4 | D7 | Free ملخص / Pro كامل |
| Decision Certificate | Hero 6 | D1 | الجميع بعد القرار |
| Locked Predictions | Z1 | D1 | الجميع (عرض) / Pro قفل |
| Discipline Mirror | Z2 | D7 | Observer+ |
| Stealth Advisor | Whale | D4 | Whale |
| Emerging Fund Terminal | Z4 | D6 | Fund/Whale |
| Compliance Footer | Z5 | D7 | الجميع دائماً |

أي فكرة جديدة تُرفض إن لم تُصنَّف تحت **قدرة من الثماني** وتعزّز **D1–D8**، ويُفضَّل ربطها ببطل/ز — لا يكفي «تاب جديد».

---

## 11) مواصفات تفاعل «سهل مبهر»

1. **Ask Oracle:** حقل رمز + زر واحد؛ Enter يرسل.  
2. **نتيجة:** جملة واحدة كبيرة؛ لماذا (3 عوامل) مطوية افتراضياً للمبتدئ.  
3. **Certificate:** زر Download/Share بجانب النتيجة.  
4. **Upgrade friction:** عند حد Free — modal هادئ يعرض Observer ثم Pro (لا حظر عدائي).  
5. **Keyboard:** `/` يركز Oracle؛ `Esc` يغلق الأدراج.  
6. **Mobile:** Decision Stage كامل العرض؛ Ritual تصبح شريط سفلي؛ Context = bottom sheet.

---

## 12) ما يجعل الإطلاق «فيروسياً عالمياً» من اللوحة نفسها

| آلية | لماذا تعمل |
|------|------------|
| Certificate share card | إثبات اجتماعي قابل للتحقق |
| Glass Box قبل حدث كبير | Hook جماعي متزامن |
| Ledger عام بلا تسجيل | إزالة حاجز الشك |
| Anti-Hype صريح | تمييز ضد موجة AI-washing |
| Observer tier | توسيع القمع قبل $29 |

الفيروس هنا = **انتشار الثقة** لا انتشار الضوضاء.

---

## 13) معايير قبول التصميم (Definition of Done)

- [ ] مستخدم جديد يصل لـ Act/Wait في ≤ 60 ثانية دون شرح  
- [ ] لا بطاقات في Hero؛ لا شارات عائمة على الوسائط  
- [ ] Utility: Capabilities + Contact + Complaints + Social ظاهرة من أي صفحة  
- [ ] 4 بطاقات تسعير متسقة مع الصلاحيات الحقيقية  
- [ ] Compliance Footer تحت كل ناتج AI  
- [ ] وضع Whale لا يضيف «منتجاً سابعاً» — فقط يكشف Context Dock  
- [ ] اختبار راحة: جلسة 20 دقيقة دون إجهاد بصري (مراجعة بشرية)  
- [ ] لغة الواجهة العامة English LTR فقط  

---

## 14) القرار المطلوب من المالك (بشري)

| قرار | خيارات | أثر |
|------|--------|-----|
| سعر Observer | $9 vs $12 vs «Free+» | شكل القمع |
| قنوات اجتماعية رسمية | روابط نهائية X/TG | Footer + Share |
| بريد الدعم/الشكاوى | support@ / complaints@ | صفحات Contact |
| تنفيذ Shell الآن | نعم / بعد الإطلاق التجريبي | أولوية هندسية |

حتى تُحسم هذه، تبقى الدراسة **ملزمة للاتجاه** ويمكن تنفيذ P0.2–P0.3 وP0.6–P0.7 دون انتظار.

---

## 15) الخلاصة الحادة

اللوحة الثورية ليست أكثر أزرار — بل **مسرح قرار واحد** محاط بـ:
- طقس يومي هادئ  
- إثبات عام  
- سلم اشتراك من 4 درجات  
- منافذ ثقة (تواصل / شكوى / قدرات النموذج)  
- ألوان مؤسسية مريحة تُطيل البقاء  

بهذا يتحول الاستخدام من «زيارة موقع» إلى **عادة اعتماد ذهني على النموذج** — وهذا هو شرط الإطلاق الفيروسي العالمي لمنصة تحليل مالي بالذكاء الاصطناعي.
