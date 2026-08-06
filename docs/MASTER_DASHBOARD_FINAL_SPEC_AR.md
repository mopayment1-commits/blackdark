# BLACKDARK — التقرير النهائي للوحة التحكم (Master Dashboard Spec)

> **الحالة:** وثيقة تصميم **ملزمة** لبناء لوحة التحكم في النموذج  
> **التاريخ:** 2026-08-06  
> **المصدر:** التصورات الأربعة المرفوعة من المالك + الدستور + الملف المرجعي الملزم + أبطال الواجهة  
> **لغة الواجهة العامة:** English-only (LTR) — حتى لو كُتبت هذه الدراسة بالعربية  
> **عند التعارض:** `PRODUCT_CONSTITUTION_AR.md` + `الملف_المرجعي_الملزم.md` + `HEROES_STRATEGY_BINDING.md` تعلو على أي بند من التصورات الأربعة  
> **قاعدة المنتج:** Decision Intelligence — **ليس** Cryptocurrency Dashboard سياحي

---

## 0) الحكم التنفيذي (ماذا نبني؟)

| سؤال | الجواب النهائي |
|------|----------------|
| ما هو المنتج؟ | **Calm Intelligence Operating System for Crypto** — قرارات موثّقة (ACT/WAIT) + دليل + سجل دقة |
| ماذا ليس المنتج؟ | لوحة مؤشرات مزدحمة · محطة Bloomberg مقلّدة · كازينو ألوان · إدمان بصري مصطنع |
| بطل الشاشة؟ | **ما يهم الآن** (Since You Left / Oracle Decision) — **ليس** رصيد المحفظة |
| قانون الواجهة؟ | **Calm Surface — Infinite Depth** + Progressive Disclosure حسب Audience |
| عدد أسطح التجزئة؟ | **Six Heroes + Section Z** — **ممنوع زر تجزئة سابع** |
| معادلة النجاح | (راحة نفسية × بساطة) × (إثبات + وضوح قرار) — بدون تصنيع إدمان ضار |

**جملة الشمال للوحة:**

> BLACKDARK يراقب → يفلتر → يكتشف → يرتب → يفسر → يقدّم الدليل.  
> المستخدم يفتح فيجد: **Here is what matters.**

---

## 1) منهجية المراجعة

تمت مراجعة التصورات الأربعة **قسمًا بقسم** واستخراج كل ميزة قابلة للتنفيذ، ثم تصنيفها:

| رمز | المعنى |
|-----|--------|
| **KEEP** | تدخل المنتج النهائي كما هي (أو بصيغة إنجليزية ملزمة) |
| **ADAPT** | تُؤخذ الفكرة بعد إعادة صياغتها لتطابق الدستور/الأبطال |
| **REJECT** | تُرفض صراحة (تتعارض مع الهوية أو تخلق Dashboard Tourism أو إدمانًا بصريًا) |

---

## 2) تحليل التصور 1 — «التصميم الذي يختفي» + اللوحة التي تتنفس

### 2.1 جوهر التصور
فلسفة Fukasawa (Without Thought) · Cognitive Load · Flow · Market Breathing · Pricing 4 tiers · Viral · Help/About.

### 2.2 مراجعة الأقسام

| قسم | الحكم | ملاحظة ملزمة |
|-----|-------|--------------|
| فلسفة Design that Disappears | **KEEP** | تطابق هوية Calm Surface |
| Cognitive Load / Shneiderman | **KEEP** | Overview → zoom → details |
| Flow State | **ADAPT** | تدفق عبر وضوح القرار — لا عبر تحريك الصفحة |
| دراسة 20 نموذجًا / D’CENT | **ADAPT** | نأخذ دروس التخصيص والتوقيت؛ لا نقلّد Wallet GNB كمنتجنا |
| «أقل ألوان = أسرع قرار» | **KEEP** | لون وظيفي فقط |
| Market Breathing / Weight Whisper / Silence on Leave / Session Warmth / Chart Overshoot | **REJECT** | حركة بلا معلومة + دفء الجلسة = تلاعب حسي — يرفضها التصور 4 والدستور |
| تدرج بنفسجي #7C5CFC كـ Highlight | **REJECT** | تحيز بصري مرفوض + يوحي بـ AI hype |
| تسلسل معلومات بمحفظة كبطل أول | **REJECT** | يتعارض مع Intelligence-first Home |
| Pricing 4 مستويات | **ADAPT** | نثبت سلم Free→Plus→Pro→Institutional (أسعار لاحقًا) |
| Help / About / Social / Viral share | **KEEP/ADAPT** | مشاركة Certificate لا لقطة لوحة صاخبة |
| Habit عبر إنجازات/confetti ذهني | **ADAPT** | اعتماد على إثبات — لا شارات قمار |
| ISO/WCAG/Gestalt/BID | **KEEP** | معايير ملزمة للجودة |
| Role layers (Exec/Manager/Analyst) | **ADAPT** | عندنا Audience: Free/Observer/Pro/Whale/Fund |
| Iron Man modular data | **ADAPT** | مصدر حقيقة واحد + أسطح بسيطة |
| خطة أسابيع 1–10 + CoinGecko كمصدر وحيد | **REJECT كخطة** | لدينا مصادر متعددة + Oracle/Hub؛ الجدول الزمني ليس ملزمًا للتنفيذ الحالي |

### 2.3 حصر مميزات التصور 1

| # | الميزة | التصنيف |
|---|--------|---------|
| 1.01 | Design that Disappears | KEEP |
| 1.02 | Reduce Extraneous Cognitive Load | KEEP |
| 1.03 | Manage Intrinsic Load via hierarchy | KEEP |
| 1.04 | Germane Load / deep thinking cues | ADAPT → Evidence Drawer |
| 1.05 | Shneiderman Mantra | KEEP |
| 1.06 | Flow: challenge/skill balance | ADAPT via UX mode |
| 1.07 | Immediate visual feedback | KEEP |
| 1.08 | Clear single purpose per section | KEEP |
| 1.09 | Immersion / remove distraction | KEEP |
| 1.10 | Customizable metrics | ADAPT (بعد Default ممتاز) |
| 1.11 | Hide sensitive assets | ADAPT → Privacy Shield |
| 1.12 | Gesture control (swipe/long-press) | ADAPT للموبايل لاحقًا |
| 1.13 | Multi timeframe 1D/7D/1M/1Y | KEEP (داخلي + UI Pro) |
| 1.14 | Bottom nav GNB | ADAPT للموبايل فقط |
| 1.15 | AI insights + sentiment | KEEP عبر الأبطال |
| 1.16 | Minimal functional color | KEEP |
| 1.17 | Market Breathing borders | REJECT |
| 1.18 | Chart settle overshoot | REJECT |
| 1.19 | Weight Whisper hover density | REJECT |
| 1.20 | Silence on Leave opacity | REJECT |
| 1.21 | Session Warmth color drift | REJECT |
| 1.22 | Palette: deep blue bg / emerald / soft red / gold alert / purple | ADAPT (بدون purple) |
| 1.23 | L1: portfolio total + best/worst + main chart | REJECT as Home hero |
| 1.24 | L2: Markets / Portfolio / News / AI signals | ADAPT → Six Heroes map |
| 1.25 | L3: details on demand | KEEP |
| 1.26 | Pricing max 4 tiers | KEEP architecture |
| 1.27 | Highlight most popular plan | KEEP |
| 1.28 | Monthly/Annual toggle + savings | KEEP |
| 1.29 | Clear feature list in plain language | KEEP (English UI) |
| 1.30 | Strong CTA per plan | KEEP |
| 1.31 | Free / Beginner / Pro / Enterprise naming | ADAPT → Free/Plus/Pro/Institutional |
| 1.32 | Testimonials under pricing | KEEP |
| 1.33 | Pricing FAQ | KEEP |
| 1.34 | Contact sales for enterprise | KEEP |
| 1.35 | Help Center + search | KEEP |
| 1.36 | Popular topics | KEEP |
| 1.37 | Contact form (name/email/type/message/file) | KEEP |
| 1.38 | Expected response time | KEEP |
| 1.39 | Emergency phone for premium | ADAPT Institutional only |
| 1.40 | About: vision video 30s | ADAPT |
| 1.41 | About: big vanity stats | ADAPT — فقط أرقام قابلة للتحقق من Ledger |
| 1.42 | Tech stack icons | ADAPT → Model Transparency |
| 1.43 | Team / partners | ADAPT لاحقًا |
| 1.44 | Social: X/LinkedIn/YouTube/Telegram/Discord | KEEP |
| 1.45 | Wow in first 5 seconds | ADAPT → decision + proof pulse |
| 1.46 | Auto screenshot share + watermark | ADAPT → Decision Certificate share card |
| 1.47 | Default share copy with hashtags | ADAPT English proof-first |
| 1.48 | Streak achievements / badges | REJECT كمحرك إدمان |
| 1.49 | Referral program | KEEP (منفصل عن Dashboard core) |
| 1.50 | Educational content series | KEEP (Research/Help) |
| 1.51 | Basic: live prices, basic chart, RSI/MA, portfolio, price alerts | ADAPT تحت الأبطال |
| 1.52 | Advanced: MACD/BB/Fib, sentiment, MTF, AI signals, custom reports | ADAPT — لا تُباع كمؤشرات مجزأة |
| 1.53 | Pro: predictive AI, portfolio optimize, API, 2FA, account manager | ADAPT ضمن Free/Pro/Whale/Fund |
| 1.54 | A/B color tests | KEEP process |
| 1.55 | Eye-tracking / 20-user tests | KEEP process |
| 1.56 | CoinGecko as primary | REJECT كقيد معماري |
| 1.57 | Gestalt principles | KEEP |
| 1.58 | Cognitive bias countermeasures (multi anchors) | KEEP → Evidence multi-source |
| 1.59 | Change blindness cues | ADAPT pulse مرة واحدة للتغيير المهم |
| 1.60 | BID framework | KEEP process |
| 1.61 | ISO 9241 | KEEP |
| 1.62 | WCAG 2.2 AA + 24×24 targets | KEEP |
| 1.63 | Role-based views | ADAPT Audience |
| 1.64 | Iron Man modular platform | ADAPT |
| 1.65 | Measure decision time / adoption / accuracy | KEEP KPIs |

---

## 3) تحليل التصور 2 — Neural Flow Architecture / 4-Zone

### 3.1 جوهر التصور
Calm Control بدل Financial Anxiety · 4 مناطق · AI OmniSearch · Prediction Canvas · Track Record · Conversion mechanics · Privacy Shield.

### 3.2 مراجعة الأقسام

| قسم | الحكم | ملاحظة |
|-----|-------|--------|
| مسار إلغاء التوتر → Calm Control | **KEEP** | هوية نفسية صحيحة |
| Obsidian / Deep Space Navy | **KEEP/ADAPT** | قريب من Comfort System الحالي |
| Desaturated bull/bear | **KEEP** | |
| Micro-Glow Focus | **ADAPT** | focus-ring خفيف — لا نيون |
| Progressive Disclosure 3 أرقام | **ADAPT** | 3–5 عناصر على Home |
| Micro-anim 300ms ease | **KEEP** | |
| 4-Zone Master Dashboard | **KEEP كهيكل** | Top / Nav / Command / Bottom |
| Live AI Accuracy Index | **KEEP** | مربوط بـ Ledger حقيقي |
| Omni-Search Ctrl+K | **KEEP** | يصبح Command Layer |
| Icon-only sidebar | **KEEP** | |
| Market Mood / Fear | **ADAPT** | Intelligence State لا مقياس خوف تقليدي فقط |
| AI Prediction Canvas | **ADAPT** | Scenario Engine (احتمالات) لا رقم هدف واحد |
| Crypto Playlists | **ADAPT** | داخل Radar/Opportunities — ليست منتجًا سابعًا |
| Emotion-filtered news | **ADAPT** | Anti-Hype news في Research |
| Explain the Market | **KEEP** | |
| Decoy pricing + 4 tiers | **ADAPT** | أسعار لا تُثبَّت الآن |
| 24h Feature Pass بلا بطاقة | **KEEP** | |
| Pause Subscription | **KEEP** | |
| Algorithm Spec + Verified Track Record | **KEEP** | Core Trust |
| Screenshot ticket + progress | **KEEP** | |
| Privacy Shield / Drag-drop / Smart Alerts / PDF / Feature vote | **KEEP** | |
| Dark/Ultra-Dark | **ADAPT** | وضع واحد ممتاز أولًا |

### 3.3 حصر مميزات التصور 2

| # | الميزة | التصنيف |
|---|--------|---------|
| 2.01 | Cancel financial anxiety path | KEEP |
| 2.02 | Calm Control outcome | KEEP |
| 2.03 | Obsidian / Deep Navy background | KEEP |
| 2.04 | Soft emerald up / warm soft red down | KEEP |
| 2.05 | Micro-glow on active element | ADAPT |
| 2.06 | Show only 3 core numbers initially | ADAPT (3–5) |
| 2.07 | Hover/progressive complexity | KEEP |
| 2.08 | 300ms ease-in-out transitions | KEEP |
| 2.09 | 2-Click Rule to any feature | KEEP target |
| 2.10 | Neural Top-Bar | KEEP |
| 2.11 | Logo | KEEP |
| 2.12 | Ctrl+K Omni-Search | KEEP |
| 2.13 | Network + AI status | KEEP |
| 2.14 | Notifications | KEEP |
| 2.15 | Profile | KEEP |
| 2.16 | Live AI Accuracy Index | KEEP (Ledger-backed) |
| 2.17 | Natural language search | KEEP |
| 2.18 | Collapsible icon sidebar | KEEP |
| 2.19 | Overview | KEEP → TODAY |
| 2.20 | AI Signal Lab | ADAPT → Oracle/Signals |
| 2.21 | Market Radar | KEEP (Hero) |
| 2.22 | Smart Portfolio Guard | KEEP → Portfolio AI |
| 2.23 | Neuro-Academy short videos | ADAPT → Help/Research |
| 2.24 | Market Mood Meter | ADAPT → Market Pulse State |
| 2.25 | AI Dynamic Prediction Canvas | ADAPT → Scenario Engine |
| 2.26 | Smart Signals & Playlists | ADAPT |
| 2.27 | Bottom live bar | ADAPT (غير مزدحم) |
| 2.28 | Emotion-filtered news | ADAPT Anti-Hype |
| 2.29 | Explain Market button | KEEP |
| 2.30 | Instant support entry | KEEP |
| 2.31 | Community links | KEEP |
| 2.32 | Free forever useful tier | KEEP |
| 2.33 | Pro popular individual | ADAPT naming |
| 2.34 | Enterprise recommended | ADAPT |
| 2.35 | Instinct institutional | ADAPT Institutional |
| 2.36 | Coin limits per tier | ADAPT later pricing research |
| 2.37 | Update cadence per tier | ADAPT |
| 2.38 | AI horizon per tier | ADAPT |
| 2.39 | Alert channels per tier | KEEP ladder |
| 2.40 | Support SLAs per tier | KEEP |
| 2.41 | 1-Click 24h Pro Pass no card | KEEP |
| 2.42 | Pause Subscription | KEEP |
| 2.43 | About / AI Engine Transparency | KEEP |
| 2.44 | Algorithm Spec Sheet | KEEP |
| 2.45 | Verified Track Record | KEEP (Core) |
| 2.46 | Instant screen-capture ticket | KEEP |
| 2.47 | Ticket progress bar | KEEP |
| 2.48 | Social + Help footer map | KEEP |
| 2.49 | Dark / Ultra-Dark toggle | ADAPT |
| 2.50 | Privacy Shield | KEEP |
| 2.51 | Drag & drop customize | ADAPT after strong default |
| 2.52 | Smart Alert (sentiment/structure not only price) | KEEP |
| 2.53 | Export PDF report | KEEP |
| 2.54 | AI/Human support chat | KEEP |
| 2.55 | Feature request voting | KEEP |
| 2.56 | Security & encryption specs | KEEP |

---

## 4) تحليل التصور 3 — التصور الثوري / Maximum Ease

### 4.1 جوهر التصور
3 ثوانٍ ذهبية · State/Action/Outcome · HOOK · 6 شاشات · Card system · Pricing Goldilocks · FAB Model Info · Unique motion (Pulse/Aura/Breathe/Particles).

### 4.2 مراجعة الأقسام

| قسم | الحكم | ملاحظة |
|-----|-------|--------|
| Maximum Ease + 3-second law | **KEEP** | |
| Zero Distraction / 3 questions | **KEEP كمبدأ** | ليس مطلقًا يمنع العمق |
| Therapeutic palette (teal/gold/orange) | **ADAPT** | Teal trust نعم؛ ذهب محدود؛ لا أرجواني سطحي كافتراضي |
| HOOK loop | **ADAPT** | محفز = Since You Left / Smart Alert — لا إشعارات اجتماعية مضللة |
| One-click actions | **KEEP** | |
| Variable rewards | **ADAPT** | مكافأة = Insight + Proof — لا مفاجآت قمار |
| Investment via customization | **KEEP** | |
| Benchmarks 20 models | **KEEP كمرجع** | |
| Wallet-First / Label-Value-Action | **KEEP** | |
| Progressive Disclosure / Real-time state awareness | **KEEP** | |
| 6 screens structure | **ADAPT** → Navigation النهائي في §6 |
| Right AI panel | **ADAPT** → Context Dock عند الطلب |
| Card system | **ADAPT** | Cards للتفاعل فقط — لا Cards في Hero |
| Notification taxonomy | **KEEP** | |
| Motion system incl. confetti | **ADAPT/REJECT** | confetti REJECT |
| Pricing Free/Growth/Pro/Enterprise | **ADAPT** | |
| Contact modal / Complaints workflow | **KEEP** | |
| FAB Model Info | **KEEP** | |
| Fixed social bar | **ADAPT** | في Utility/Footer لا شريط يشتت |
| Feature checklist مجموعات 1–6 | **ADAPT** | يُصفّى عبر الأبطال والقدرات |
| Unique: Pulse/Aura/Breathe/Particles/Visual Sound | **Aura KEEP خفيف** · الباقي **REJECT** |
| Nothing Idle | **KEEP** | |
| Inverse vs competitors | **KEEP** | رؤى لا بيانات خام |
| KPIs + A/B | **KEEP** | |

### 4.3 حصر مميزات التصور 3

| # | الميزة | التصنيف |
|---|--------|---------|
| 3.01 | Visual Safety in 1s | KEEP |
| 3.02 | Answer main question in 2s | KEEP |
| 3.03 | Subconscious retention in 3s | ADAPT via value not trick |
| 3.04 | State / Action / Outcome only | KEEP filter |
| 3.05 | Calm Mystery palette | ADAPT |
| 3.06 | Contrast rules high/mid/low | KEEP |
| 3.07 | HOOK trigger/action/reward/investment | ADAPT |
| 3.08 | Smart support-level notification | KEEP |
| 3.09 | Daily performance summary | KEEP |
| 3.10 | Social proof notifications | REJECT إن مضللة |
| 3.11 | One-click actions | KEEP |
| 3.12 | No long forms | KEEP |
| 3.13 | Intent prediction | ADAPT |
| 3.14 | Unexpected opportunity reward | ADAPT |
| 3.15 | Data update reward | KEEP |
| 3.16 | Peer percentile reward | ADAPT بحذر (Anti-Hype) |
| 3.17 | Customize dashboard investment | ADAPT |
| 3.18 | Watchlists investment | KEEP |
| 3.19 | Connect wallets investment | ADAPT |
| 3.20 | Flow state checklist | KEEP |
| 3.21–3.40 | 20 global benchmarks lessons | KEEP as research |
| 3.41 | Wallet-First UX | ADAPT |
| 3.42 | Label-Value-Action | KEEP |
| 3.43 | Progressive Disclosure | KEEP |
| 3.44 | Real-Time State Awareness | KEEP |
| 3.45 | Navigation Rail | KEEP |
| 3.46 | Overview screen | ADAPT → TODAY |
| 3.47 | Oracle screen | KEEP (Hero) |
| 3.48 | Market Radar | KEEP |
| 3.49 | Portfolio AI | KEEP |
| 3.50 | Opportunities | ADAPT تحت Radar/Signals |
| 3.51 | Signals | KEEP |
| 3.52 | Top bar search/quick/network/time | KEEP |
| 3.53 | Bottom status bar | KEEP |
| 3.54 | Right AI assistant panel | ADAPT Context Dock |
| 3.55 | Portfolio Health Card | ADAPT ليس بطل Home |
| 3.56 | Total Balance hero number | REJECT as Home hero |
| 3.57 | 24h change | KEEP secondary |
| 3.58 | Top movers | ADAPT → Needs Your Attention |
| 3.59 | AI daily summary | KEEP |
| 3.60 | Buy/Sell/Transfer quick actions | **REJECT** كأفعال تجزئة بطولية — نحن ACT/WAIT قرار تحليلي (تنفيذ عبر مسارات منفصلة/Whale) |
| 3.61 | Fear/Greed visual | ADAPT Market Pulse |
| 3.62 | AI insights feed | KEEP |
| 3.63 | Prediction cards + confidence | ADAPT Scenario + Evidence |
| 3.64 | Risk heatmap | ADAPT Pro/Whale |
| 3.65 | Correlation matrix | ADAPT depth layer |
| 3.66 | Sentiment analysis | KEEP |
| 3.67 | Screener / Heatmap / Trending / New / Volume | ADAPT Markets/Radar |
| 3.68 | Allocation / performance / rebalance / tax / diversification | ADAPT Portfolio tiers |
| 3.69 | Opportunity cards / arb / yield / airdrop / early | ADAPT — Arb عبر Net-Edge لا Yield casino |
| 3.70 | Signal feed / performance / alerts / backtesting | ADAPT |
| 3.71 | Card header/body/footer pattern | ADAPT |
| 3.72 | Notification types S/W/E/I/AI | KEEP |
| 3.73 | Entrance/hover/click/count-up/shimmer | KEEP |
| 3.74 | Confetti success | REJECT |
| 3.75 | Goldilocks 4 tiers | ADAPT |
| 3.76 | Explorer free tier | ADAPT Free |
| 3.77 | Growth recommended | ADAPT Plus |
| 3.78 | Pro analyst | ADAPT Pro |
| 3.79 | Enterprise contact | KEEP |
| 3.80 | Monthly/Annual + trust badges | KEEP |
| 3.81 | Comparison table collapsible | KEEP |
| 3.82 | Money-back guarantee copy | ADAPT قانونيًا لاحقًا |
| 3.83 | Contact slide-over 3 fields | KEEP |
| 3.84 | Complaint tabs + priority + status | KEEP |
| 3.85 | Auto reply with ticket id | KEEP |
| 3.86 | FAB Model capabilities | KEEP |
| 3.87 | Fixed left social bar | ADAPT footer/utility |
| 3.88 | Auth OAuth+Web3 | ADAPT حسب الموجود |
| 3.89 | Multi-network / multi-exchange | ADAPT engines quiet |
| 3.90 | WebSocket realtime | KEEP |
| 3.91 | Multi-channel notifications | KEEP |
| 3.92 | Encrypted storage | KEEP |
| 3.93 | i18n many languages | **REJECT للعامة الآن** — English-only ملزم |
| 3.94 | Dark/light | ADAPT dark-first |
| 3.95 | Customizable overview widgets | ADAPT |
| 3.96 | Keyboard shortcuts | KEEP |
| 3.97 | Focus Mode | KEEP |
| 3.98 | Presentation Mode | KEEP |
| 3.99 | Export PDF/CSV/Excel | KEEP |
| 3.100 | Share dashboards | ADAPT share Certificate/Analysis |
| 3.101 | Paper trading | ADAPT لاحقًا — ليس بطلًا |
| 3.102 | Community/follow/chat/forum/reputation/contests | ADAPT → ARENA منفصل |
| 3.103 | Help/AI chat/tickets/videos/webinars/API docs/blog/FAQ | KEEP |
| 3.104 | The Pulse continuous | REJECT continuous |
| 3.105 | The Aura | KEEP subtle |
| 3.106 | The Breathe cards | REJECT |
| 3.107 | Particles background | REJECT |
| 3.108 | Visual Sound waves | REJECT |
| 3.109 | Nothing Idle | KEEP |
| 3.110 | Inverse competitor principle | KEEP |
| 3.111 | KPI Time-to-Value <30s | KEEP |
| 3.112 | Session/Return/NPS/Churn targets | KEEP as goals |
| 3.113 | A/B culture | KEEP |

---

## 5) تحليل التصور 4 — رؤية المالك (Decision Intelligence)

### 5.1 جوهر التصور (الأعلى وزنًا في الدمج)
من Dashboard إلى Decision Intelligence · خمس أسئلة دائمة · Calm Surface Infinite Depth · Since You Left · Evidence Drawer · Arena منفصل · رفض الإدمان الحركي.

### 5.2 مراجعة الأقسام (قبول افتراضي أعلى)

| قسم | الحكم |
|-----|-------|
| 5 أسئلة دائمة | **KEEP — هوية** |
| Calm Surface — Infinite Depth | **KEEP — قاعدة تصميم** |
| Home ≠ Portfolio Balance | **KEEP** |
| Since You Left | **KEEP — بطل Home** |
| Market Pulse as Intelligence State | **KEEP** |
| Needs Your Attention | **KEEP** |
| Ask BLACKDARK رئيسي | **KEEP** |
| Navigation TODAY…ARENA | **KEEP** |
| ⌘K Universal AI Bar | **KEEP** |
| Asset Intelligence + AI Thesis | **KEEP** |
| Scenario Engine | **KEEP** |
| Evidence Drawer WHY | **KEEP — D1/Glass** |
| Verified Track Record (incl. misses) | **KEEP — Core** |
| Smart Alerts structure-aware | **KEEP** |
| Privacy Shield | **KEEP** |
| Customize after strong default + density modes | **KEEP** |
| Quiet Luxury visual | **KEEP** |
| Motion 20% only / no particles/confetti/breathing | **KEEP** |
| ARENA viral separation | **KEEP** |
| Free useful + Pass + Pause | **KEEP** |
| Support & Trust hub + Data Delayed honesty | **KEEP** |
| دمج انتقائي من 1/2/3 | **KEEP كمنهج** |
| توصية: النظام يعمل أولًا ثم يعرض ما يهم | **KEEP — شمال** |

### 5.3 حصر مميزات التصور 4

| # | الميزة | التصنيف |
|---|--------|---------|
| 4.01 | Decision Intelligence positioning | KEEP |
| 4.02 | Not clone TradingView/Nansen | KEEP |
| 4.03 | Q1 What happened? | KEEP |
| 4.04 | Q2 Why? | KEEP |
| 4.05 | Q3 What matters to me? | KEEP |
| 4.06 | Q4 What may happen next? | KEEP |
| 4.07 | Q5 What is the evidence? | KEEP |
| 4.08 | Calm Surface | KEEP |
| 4.09 | Infinite Depth layers | KEEP |
| 4.10 | One product two depths | KEEP |
| 4.11 | Depth: on-chain→history evidence stack | KEEP quiet engines |
| 4.12 | Greeting + since you left | KEEP |
| 4.13 | Since You Left AI top-3 changes | KEEP |
| 4.14 | Show me why | KEEP |
| 4.15 | Market Pulse states table | KEEP |
| 4.16 | Explain Market 30s | KEEP |
| 4.17 | Show Evidence | KEEP |
| 4.18 | Needs Your Attention personalized | KEEP |
| 4.19 | Ask BLACKDARK main module | KEEP |
| 4.20 | Suggested prompts by regime | KEEP |
| 4.21 | Nav: TODAY | KEEP |
| 4.22 | Nav: MARKETS | KEEP |
| 4.23 | Nav: RADAR | KEEP |
| 4.24 | Nav: ORACLE | KEEP |
| 4.25 | Nav: SIGNALS | KEEP |
| 4.26 | Nav: PORTFOLIO | KEEP |
| 4.27 | Nav: RESEARCH | KEEP |
| 4.28 | Nav: ALERTS | KEEP |
| 4.29 | Nav: ARENA | KEEP (viral, not 7th retail hero) |
| 4.30 | Saved / Help / Settings | KEEP |
| 4.31 | ⌘K command layer | KEEP |
| 4.32 | Asset page header metrics | KEEP |
| 4.33 | Asset tabs depth | KEEP |
| 4.34 | AI Thesis | KEEP |
| 4.35 | Why / Invalidate / What changed | KEEP |
| 4.36 | Scenario Engine bull/base/bear | KEEP |
| 4.37 | Scenario fields range/time/drivers/risks/invalidation/confidence/evidence | KEEP |
| 4.38 | Evidence Drawer weights + sources | KEEP |
| 4.39 | AI that shows its work | KEEP |
| 4.40 | BLACKDARK RECORD page | KEEP |
| 4.41 | Publish misses | KEEP |
| 4.42 | Smart structure alerts | KEEP |
| 4.43 | Alert actions Why/Open/Mute/Sensitivity | KEEP |
| 4.44 | Privacy Shield | KEEP |
| 4.45 | Strong default then Customize | KEEP |
| 4.46 | Density Beginner/Standard/Analyst | KEEP |
| 4.47 | Quiet Luxury + Institutional Intelligence | KEEP |
| 4.48 | Functional color only | KEEP |
| 4.49 | Selective motion only | KEEP |
| 4.50 | Reject particles/breathing/confetti/session warmth/overshoot | KEEP |
| 4.51 | ARENA as product-in-product | KEEP |
| 4.52 | Shareable scenario cards + deep link | KEEP |
| 4.53 | Tier architecture Free/Plus/Pro/Institutional | KEEP |
| 4.54 | 24h Pro Pass | KEEP |
| 4.55 | Pause Subscription | KEEP |
| 4.56 | Never sell basic security as paid | KEEP |
| 4.57 | Full Trust Hub | KEEP |
| 4.58 | Data Delayed honest indicator | KEEP |
| 4.59 | Selective KEEP lists from visions 1–3 | KEEP method |
| 4.60 | Final equation Calm Intelligence OS | KEEP |
| 4.61 | System works first: monitor→filter→detect→rank→explain→evidence | KEEP |

---

## 6) التعارضات المحسومة (Conflict Resolution)

| تعارض | الغالب | القرار النهائي |
|-------|--------|----------------|
| Portfolio Balance كبطل Home vs Since You Left | تصور 4 + الدستور | **Since You Left / Decision** هو البطل |
| ACT/WAIT vs Buy/Sell أزرار بطولية | الدستور D7 | **ACT/WAIT** — التنفيذ مسار منفصل/Whale |
| English-only vs Arabic UI في التصورات | قرار المالك الملزم | **English public UI** |
| حركة تنفسية/جسيمات vs Motion محدود | تصور 4 | **Motion معلوماتي فقط** |
| بنفسج highlight vs Quiet Luxury | قواعد التصميم + تصور 4 | **لا بنفسج افتراضي** |
| 6 شاشات vs Six Heroes | الأبطال الملزمون | الشاشات **تغلف** الأبطال — لا تستبدلهم |
| ARENA vs منع زر سابع | أبطال + تصور 4 | ARENA **سطح فيروسي منفصل** — ليس بطل تجزئة سابع |
| Pricing أرقام مختلفة بين 1/2/3 | تصور 4 | **Architecture فقط** — الأسعار بعد Pricing Research |
| i18n واسع الآن | الملزم | English-first الآن |
| Fear&Greed meter vs Intelligence State | تصور 4 | **Market Pulse State** |
| Prediction رقم هدف vs Scenarios | تصور 4 + Anti-Hype | **Scenario Engine** |
| إدمان إيجابي مصطنع vs اعتماد على إثبات | دستور + تصور 4 | **Prove-it Loop** فقط |

---

## 7) التصور النهائي المدمج — BLACKDARK Master Dashboard

### 7.1 الهوية

**BLACKDARK = Calm Intelligence Operating System for Crypto**

تجيب اللوحة دائمًا عن:

1. **What happened?**  
2. **Why did it happen?**  
3. **What matters to me?**  
4. **What may happen next?**  
5. **What is the evidence?**

### 7.2 قاعدة التصميم

**Calm Surface — Infinite Depth**

- السطح: 3–5 عناصر، لا خوف، لا سياحة لوحات.  
- العمق: On-chain · Derivatives · Liquidity · Order Flow · Sentiment · Technical · Macro · News · Correlation · Model reasoning · Historical evidence — عند الطلب.  
- كثافة العرض: **Beginner / Standard / Analyst** — نفس المنتج.

### 7.3 الهيكل الرباعي (من تصور 2 + صقل 4)

```
┌──────────────────────────────────────────────────────────────────────────┐
│ [Z1] NEURAL TOP-BAR                                                      │
│ Brand · ⌘K Ask BLACKDARK · AI Accuracy · Network/Data status · Bell · Me │
│ + Privacy Shield · Audience chip                                         │
├────────────┬─────────────────────────────────────────────┬───────────────┤
│ [Z2] NAV   │ [Z3] COMMAND CENTER (one job)               │ [Z4] CONTEXT  │
│ Rail       │ TODAY / ORACLE / … content                  │ Dock (on      │
│ icon-first │                                             │ demand)       │
│            │                                             │ Evidence ·    │
│ TODAY      │                                             │ Chart · Why · │
│ MARKETS    │                                             │ Chat          │
│ RADAR      │                                             │               │
│ ORACLE     │                                             │               │
│ SIGNALS    │                                             │               │
│ PORTFOLIO  │                                             │               │
│ RESEARCH   │                                             │               │
│ ALERTS     │                                             │               │
│ ARENA*     │                                             │               │
│ ───        │                                             │               │
│ Saved      │                                             │               │
│ Help       │                                             │               │
│ Settings   │                                             │               │
├────────────┴─────────────────────────────────────────────┴───────────────┤
│ Status: LIVE or DATA DELAYED · Legal · Contact · Complaints · Social     │
└──────────────────────────────────────────────────────────────────────────┘
```

\* ARENA = سطح فيروسي/اجتماعي منفصل عن Six Heroes التشغيلية.

### 7.4 ربط Six Heroes (ملزم)

| Hero | أين يظهر في اللوحة |
|------|---------------------|
| 1 Public Accuracy Ledger | Top AI Accuracy · RECORD · footer trust |
| 2 Whale Radar / S/N | RADAR + Context Dock (Pro+) |
| 3 Portfolio AI | PORTFOLIO |
| 4 Opportunity Quality Score | ORACLE / SIGNALS / Asset header |
| 5 Single-Sentence Oracle | ORACLE + TODAY decision strip |
| 6 Decision Certificate | بعد كل قرار · Share · ARENA cards |

Section Z تبقى تعميقات هادئة (Glass Box cadence, Discipline Mirror, …) — بلا زر تجزئة جديد.

### 7.5 ربط D1–D8 في الواجهة

| ID | ظهور واجهي إلزامي |
|----|-------------------|
| D1 Proof-Native | Certificate + RECORD + prediction_id |
| D2 Contradiction Veto | يظهر كـ WAIT/Abstain + سبب |
| D3 Net-Edge Truth | Pro/Whale على الفرص القابلة للتنفيذ |
| D4 Half-Life | Whale / opportunity cards |
| D5 Regime | Market Pulse + model context |
| D6 Evidence Pack | Fund/B2B + Export |
| D7 Persona Clarity | ACT/WAIT English + density modes |
| D8 Signal Registry | Evidence Drawer sources/weights |

---

## 8) الشاشات النهائية — Card / زر / حالة

### 8.1 TODAY (Home / Command Center)

**هدف 3 ثوانٍ:** يعرف المستخدم ماذا تغير وماذا يفعل.

| منطقة | المحتوى | أزرار |
|-------|---------|-------|
| Greeting | Good morning, {Name} · Here’s what changed since you left | — |
| **Since You Left** | N meaningful changes · AI top 3 cards (asset · event · importance) | `Show me why` · `Open` |
| **Market Pulse** | Trend / Risk / Liquidity / Volatility / Sentiment / Smart Money | `Explain Market (30s)` · `Show Evidence` |
| **Needs Your Attention** | 3 personalized items (not top movers dump) | `Review` · `Mute` |
| **Ask BLACKDARK** | Primary input + regime-aware suggestions | Submit · suggestion chips |
| Decision strip (إن وُجد سياق) | Last ACT/WAIT + score | `Certificate` · `Mirror` |

**ممنوع في TODAY:** رصيد محفظة كرقم بطولي · جداول 50 عملة · بطاقات ميزات تسويقية · confetti.

### 8.2 ORACLE

| عنصر | وظيفة |
|------|--------|
| Symbol input + Audience/UX mode | Retail/Pro… · Beginner/Pro |
| `Get Decision` | ACT أو WAIT + جملة واحدة |
| Opportunity Score | 0–100 |
| Why Top-3 | عوامل |
| Evidence Drawer trigger `WHY?` | أوزان المصادر |
| Decision Certificate | Copy / Download JSON / Share card |
| Discipline Mirror | Followed? Yes/No |
| Compliance footer | Anti-Hype |

### 8.3 MARKETS

Screener هادئ · فرز/تصفية · فتح Asset Intelligence — بلا ضوضاء.

### 8.4 RADAR

Anomalies · Whale S/N · السيولة غير العادية · Playlists كمجموعات اكتشاف (ليست منتجًا منفصلًا).

### 8.5 SIGNALS

Feed إشارات مُسجَّلة (Registry) · أداء تاريخي · لا إشارات بلا تعريف.

### 8.6 PORTFOLIO

صحة/توزيع/مخاطر · Privacy Shield · اقتراحات — ليست بطل Home.

### 8.7 RESEARCH

Anti-Hype news · Explain · تقارير · أكاديمية قصيرة.

### 8.8 ALERTS

Smart Alerts (structure/sentiment/regime) · Why · Open Analysis · Mute · Sensitivity.

### 8.9 Asset Intelligence (صفحة أصل)

Header: Price · Change · Risk · AI State · Confidence  
Chart  
Tabs: Overview · AI Analysis · Technical · On-chain · Derivatives · Sentiment · News · Scenarios · Signals · History  

**AI Thesis** + Why / Invalidate / What changed  
**Scenario Engine:** Bull / Base / Bear + range/time/drivers/risks/invalidation/confidence/evidence

### 8.10 RECORD (Verified Track Record)

صحيح · خاطئ · confidence · actual · model version · regime — بما فيه الخسائر.

### 8.11 ARENA (فيروس منفصل)

Human vs AI · challenges · shareable scenario cards · deep links — **لا يحوّل Dashboard إلى لعبة**.

### 8.12 Trust & Support Hub

Help · AI support · Human support · Complaints (+ screenshot diagnostics) · Ticket progress · Feature vote · Status · Model docs · Security · Privacy · **DATA DELAYED** honesty.

### 8.13 Pricing (Architecture)

| Tier | الدور النفسي |
|------|-------------|
| FREE | مفيدة فعلًا للانتشار |
| PLUS | المستخدم النشط |
| PRO | المحلل الجاد (موصى به بصريًا) |
| INSTITUTIONAL | شركات — Contact |

Extras ملزمة: **24h Pro Pass بلا بطاقة** · **Pause Subscription** · لا بيع الأمن الأساسي.

---

## 9) النظام البصري والحركة (النهائي)

### 9.1 Tokens (Quiet Luxury)

| Token | قيمة | دور |
|-------|------|-----|
| `--void` | `#080B10` | خلفية |
| `--surface` | `#10161F` | سطح |
| `--elev` | `#161D28` | رفع خفيف |
| `--ink` | `#E8EDF5` | نص |
| `--mute` | `#8892A6` | ثانوي |
| `--trust` | `#2DD4BF` | ثقة/Brand accent |
| `--calm` | `#00C853` @ ~85% | صعود هادئ |
| `--stop` | `#FF5252` دافئ مخفف | هبوط بلا ذعر |
| `--hold` | `#FDB813` | Wait/تحذير |
| `--prove` | `#5EEAD4` | إثبات |

**مرفوض:** بنفسج افتراضي · نيون · Glow متعدد · Particles · Session Warmth.

### 9.2 Motion المسموح

Aura خفيف على العنصر النشط · State transition · Hover · Loading · Panel open · **نبضة واحدة** للتغيير المهم.

**مرفوض:** breathing مستمر · particles · confetti · chart overshoot · silence-on-leave كحيلة.

---

## 10) حلقة العادة الصحية (Prove-it Loop)

| مرحلة | تطبيق BLACKDARK |
|-------|-----------------|
| Trigger | Since You Left · Smart Alert · Daily summary |
| Action | نقرة واحدة: Get Decision / Explain / Open Why |
| Reward | جملة قرار + Evidence + Certificate |
| Investment | Mirror · Watchlist · Saved views · Density preference |

**نرفض:** شارات streak قمارية · إشعارات اجتماعية خادعة · مكافآت عشوائية بلا دليل.

---

## 11) ما نأخذه من كل تصور (خلاصة الدمج)

| من | نأخذ |
|----|------|
| **1** | العقل النفسي · البساطة · Accessibility · Progressive Disclosure · Pricing clarity · Help/FAQ · Share proof · Referrals · معايير ISO/WCAG |
| **2** | 4-Zone · Calm Control · ⌘K · Accuracy live · Prediction→Scenarios · Track Record · Pass/Pause · Privacy · Screenshot tickets · Smart Alerts · Feature vote |
| **3** | Maximum Ease · 3s orientation · State/Action/Outcome · Label/Value/Action · Benchmarks · IA العميقة · Focus/Presentation · Complaints workflow · Model FAB · Nothing Idle · KPIs |
| **4 (مالك)** | Decision Intelligence · 5 أسئلة · Since You Left · Needs Attention · Evidence Drawer · Scenario Engine · AI Thesis · ARENA فصل · Motion صارم · Data Delayed · النظام يعمل أولًا |

---

## 12) قائمة رفض صريحة (لا تُنفَّذ)

1. Portfolio balance كبطل الشاشة الأولى  
2. زر Buy/Sell بطولي في Home/Oracle (نستخدم ACT/WAIT)  
3. زر تجزئة سابع خارج Six Heroes + Z  
4. Market Breathing / Session Warmth / Particles / Confetti / Chart overshoot  
5. Highlight بنفسجي افتراضي  
6. Vanity stats غير قابلة للتحقق  
7. Arabic-first على الواجهة العامة (ملغى)  
8. بيع الأمن الأساسي كباقة  
9. ادعاء Live مع بيانات متأخرة  
10. تحويل اللوحة كلها إلى لعبة إنجازات  

---

## 13) معايير قبول التنفيذ (Definition of Done للوحة)

1. المستخدم الجديد يفهم **ما يهم الآن** خلال **≤ 30 ثانية**.  
2. كل قرار Oracle = **ACT/WAIT** + جملة + طريق إلى **Evidence** + **Certificate**.  
3. Home يعرض **Since You Left** قبل أي رصيد.  
4. لا عنصر في Hero Budget خارج: Brand · قرار/ما يهم · جملة دعم · CTA · إثبات.  
5. ⌘K يفتح Command Layer حقيقي (navigate + ask + alert + export).  
6. RECORD يعرض إصابات **وأخطاء**.  
7. DATA DELAYED يظهر عند التأخر.  
8. كل PR للوحة يُربط بـ: قدرة من الثماني · D1–D8 · وبطل أو Section Z.

---

## 14) الخطوة التالية الهندسية

هذه الوثيقة = **Master Dashboard Spec** جاهزة للمصمم والمبرمج.

التسلسل التنفيذي المقترح (تقني لا زمني بالأسابيع):

1. **Shell:** Top-bar + Nav rail + Context dock + tokens  
2. **TODAY:** Since You Left + Market Pulse + Needs Attention + Ask  
3. **ORACLE polish:** Evidence Drawer + Certificate share card  
4. **RECORD + Data Delayed**  
5. **Asset Intelligence + Scenario Engine**  
6. **Smart Alerts + Privacy Shield**  
7. **Trust Hub (Help/Contact/Complaints/Model)**  
8. **Pricing architecture UI + Pass/Pause**  
9. **ARENA v1** (بعد ثبات نواة القرار)

---

## 15) الخلاصة بجملة واحدة

> نبني لوحة **تختفي** بصريًا، و**تعمل** قبل أن يسأل المستخدم، و**تُظهر عملها** بالدليل، و**ترفض** أن تتحول إلى معرض مؤشرات أو كازينو حركة — لأن BLACKDARK يبيع **قرارًا موثوقًا**، لا لوحة مزدحمة.
