# BLACKDARK Decision Truth System — Institutional Final v1

**Status:** Governing Source of Truth (SSOT) for implementation  
**Purpose:** تحويل Net-Edge + Pre-Impact + Simulation + Trust من Features منفصلة إلى **نظام قرار واحد متكامل** يصعب نسخه كواجهة فقط.  
**Implementation intent:** Full source-driven implementation, integration, verification, and local engineering closure with zero known locally-buildable gaps.

---

# 0. الحكم المؤسسي النهائي

BLACKDARK لا يجب أن تكون منصة بيانات أو منصة إشارات أو Dashboard كثيف فقط.

التميّز المؤسسي المعتمد هو:

> **BLACKDARK must determine whether an opportunity is economically real, executable, risk-compatible, evidence-supported, historically defensible, and sufficiently certain — and must explicitly reject or abstain when those conditions are not met.**

العقد المركزي هو:

```text
WHAT IS HAPPENING?
        ↓
IS THE DATA TRUSTWORTHY?
        ↓
IS THE OPPORTUNITY REAL?
        ↓
IS IT EXECUTABLE?
        ↓
WHAT IS THE TRUE NET EDGE?
        ↓
WHAT CAN GO WRONG?
        ↓
WHAT DOES IT DO TO MY PORTFOLIO?
        ↓
HAS THIS TYPE OF DECISION SURVIVED TESTING?
        ↓
HOW UNCERTAIN ARE WE?
        ↓
PASS / DEGRADE / ABSTAIN / REJECT
        ↓
WHY?
```

المنظومة النهائية يجب أن تجمع فعليًا:

- Net-Edge
- Execution Feasibility
- Opportunity Capacity
- Opportunity Half-Life
- Cost Autopsy
- Pre-Impact Portfolio Protection
- Stress / Reverse Stress
- Simulation
- Evidence Quality
- Strategy Vetting
- Signal Admission Gate
- Decision Contract
- Calibration
- Immutable Outcome Tracking
- Rejection / Why NOT
- Decision Change Detection
- Explicit Uncertainty
- Abstention
- Safety Floor
- User Agency

ولا يجوز تنفيذها كـwidgets أو صفحات منفصلة غير مترابطة.

---

# 1. العقود غير القابلة للتفاوض

## DTS-001 — No opportunity without economic reality
أي Opportunity/Signal قابل لاتخاذ قرار يجب ألا يظهر كمخرج موصى به قبل حساب Gross Edge + Expected Net Edge + Cost decomposition + Execution feasibility + Liquidity/Capacity + Uncertainty. الـraw spread أو raw signal وحده غير كافٍ.

## DTS-002 — No signal without risk, grade, evidence and freshness
أي مخرج قرار حرج يجب أن يحتوي على الأقل: Net Edge, Risk, Grade, Evidence Class, Freshness, Uncertainty/Confidence Context, Invalidation Condition, Decision State.

## DTS-003 — Explicit abstention
إذا كانت البيانات materially stale/partial/conflicting/suspect/insufficient/unverified فلا يجوز إخراج قرار كامل بثقة مصطنعة. النتيجة يجب أن تكون واحدة من: AVAILABLE / DEGRADED / ABSTAINED / REJECTED / UNAVAILABLE.

## DTS-004 — User agency
BLACKDARK يعرض السياق والنتيجة المنهجية، لكنه لا يدّعي أنه يقرر نيابة عن المستخدم. كل decision surface يجب أن يحافظ على User Agency واضح.

## DTS-005 — No hidden assumptions
أي رقم حرج يجب أن يحدد المصدر، timestamp/freshness، assumptions، methodology version، confidence/uncertainty، scope/applicability.

## DTS-006 — No false precision
لا يجوز عرض single-point Net Edge أو impact أو confidence أو historical accuracy كأنها حقيقة يقينية عندما تكون النتيجة احتمالية أو حساسة للسيولة/الزمن/التكلفة.

## DTS-007 — Calm default, optional density
الواجهة الافتراضية تبقى هادئة ومركزة على Six Heroes / Progressive Disclosure. Command View كثيف يكون اختياريًا، وليس الواجهة الافتراضية للجميع.

## DTS-008 — Evidence before marketing claims
يحظر في المنتج أو الوثائق المؤسسية ادعاءات مثل “الوحيدون” أو “كل المنافسين سيئون” أو نسب خسارة عامة بلا benchmark/evidence قابل للتدقيق.

---

# 2. النظام المركزي — Decision Truth Pipeline

كل Opportunity/Signal/Decision يجب أن يمر على Pipeline واحد:

```text
SOURCE INGESTION
→ DATA INTEGRITY
→ FRESHNESS
→ QUALITY
→ EVIDENCE CLASS
→ ECONOMIC REALITY
→ EXECUTION FEASIBILITY
→ PORTFOLIO IMPACT
→ SIMULATION / HISTORICAL VALIDATION
→ UNCERTAINTY / CALIBRATION
→ SIGNAL ADMISSION GATE
→ DECISION CONTRACT
→ PASS / DEGRADE / ABSTAIN / REJECT
→ EXPLANATION / WHY / WHY NOT
→ USER ACTION CONTEXT
→ OUTCOME LEDGER
→ RECALIBRATION
```

لا يجوز bypass لأي مرحلة إلزامية حسب نوع القرار.

---

# 3. Economic Reality Engine

## DTS-009 — Formal Net-Edge Specification
يجب إنشاء Product/Calculation Contract رسمي لـNet Edge:

```text
Gross Edge
- Trading Fees
- Expected Slippage
- Price Impact
- Gas / Network Fees
- Funding
- Borrow Cost
- Withdrawal / Deposit Fees
- Bridge Costs
- FX / Conversion Costs
- Expected Opportunity Decay
- Execution Latency Cost
- Failed / Partial Fill Cost
- Hedging Cost
= Expected Net Edge
```

المكونات غير المنطبقة = N/A with reason، وليس zero افتراضي بلا دليل.

## DTS-010 — Cost Autopsy
كل opportunity يجب أن يتيح تفصيلًا واضحًا لكل cost component، ولا يجوز إخفاؤه في مسار غامض.

## DTS-011 — Net-Edge uncertainty interval
لا يكتفى بالرقم المتوقع. يجب دعم uncertainty/confidence interval عندما تسمح المنهجية، أو التصريح بوضوح إذا لم يمكن تقديره دفاعيًا.

## DTS-012 — Realizable vs theoretical edge
يجب فصل Theoretical Edge / Expected Net Edge / Realizable Net Edge، حيث Realizable Net Edge يأخذ execution probability/capacity/timing في الاعتبار.

---

# 4. الإضافات المؤسسية الإلزامية الـ12

## DTS-013 — 1) Execution Feasibility Score
Score مستقل عن Net Edge يقيس spread, depth, liquidity, expected fill, venue availability, network state, latency, transfer time, route complexity, bridge availability, slippage sensitivity, counterparty/venue health. Output 0..100 + explainable reason codes.

## DTS-014 — 2) Opportunity Capacity
تقدير الحجم القابل للتنفيذ قبل أن يتآكل الـedge، مع limiting factor + confidence + timestamp.

## DTS-015 — 3) Opportunity Half-Life
تقدير عمر/اضمحلال الفرصة حيث تكون المنهجية صالحة. لا يعرض تقدير مصطنع عند نقص الدليل.

## DTS-016 — 4) Reverse Stress Testing
ليس فقط “ماذا لو تكرر FTX؟” بل: ما السيناريو الذي يجعل المحفظة تتجاوز حد الخسارة/المخاطرة؟ Inputs قد تشمل price shock, depeg, venue failure, liquidity evaporation, funding spike, correlation convergence, oracle/bridge failure.

## DTS-017 — 5) Signal Admission Gate
كل signal يمر على Freshness, Data Quality, Evidence, Liquidity, Execution Feasibility, Net Edge, Risk, Uncertainty gates. Output: ADMITTED / DEGRADED / REJECTED / ABSTAINED.

## DTS-018 — 6) Decision Contract
كل قرار يحمل: decision_state, time_horizon, entry_assumptions, invalidation_condition, review_time, net_edge, execution_feasibility, risk, grade, evidence_class, freshness, uncertainty, capacity, why, why_not.

## DTS-019 — 7) Opportunity Rejection Engine
يقيس ويشرح عدد الفرص التي تم رفضها قبل عرض ما يستحق الانتباه. الأرقام يجب أن تكون مشتقة من pipeline حقيقي.

## DTS-020 — 8) Why NOT Engine
لكل rejected/abstained opportunity سبب machine-readable + شرح مستخدم واضح، مع Gross Edge / Expected Net Edge / Execution Risk / Liquidity / Freshness / Confidence Context.

## DTS-021 — 9) Decision Calibration Ledger
لا يكتفى بـAccuracy. يدعم confidence buckets, realized frequency, calibration error, Brier score أو equivalent حيث ينطبق، base-rate comparison, abstention-adjusted results.

## DTS-022 — 10) Pre-Registered Outcome Ledger
قبل النتيجة يسجل prediction/decision + timestamp + evidence + confidence + methodology version + invalidation condition + horizon. بعد النتيجة يسجل realized outcome وcalibration impact. Append-only/auditable لمنع cherry-picking.

## DTS-023 — 11) Decision Change Detector
إذا تغير القرار بعد تغير facts، يكشف previous state, new state, changed inputs, timestamp, materiality, reason.

## DTS-024 — 12) Safety Floor
كل decision surface الحرج يظهر data freshness, data quality, evidence class, uncertainty, limitations, invalidation trigger, execution feasibility. إذا انهار شرط أساسي يتحول القرار إلى DEGRADED/ABSTAINED/REJECTED.

---

# 5. Calm Command Surface

## DTS-025 — Six Heroes default
الواجهة الافتراضية تساعد المستخدم خلال ~30 ثانية على فهم: My Capital / Market State / Best Verified Opportunity / Main Risk / Smart Money or Evidence / Today's Decision Brief.

## DTS-026 — Optional Command View
للمحترف/Pro+/Institutional: Portfolio + Market + Opportunities + Risk + Evidence + Alerts في شاشة موحدة اختيارية، دون فرض high-density على الجميع.

---

# 6. Pre-Impact Portfolio Protection

## DTS-027 — Risk Budget / Risk Envelope
لا يختزل في loss slider فقط. يشمل حيث ينطبق max tolerated loss, drawdown, concentration, leverage, liquidity, venue exposure, stablecoin exposure, counterparty exposure.

## DTS-028 — Pre-impact alerts
تحذير قبل تجاوز الحدود، مع current risk use / configured max / projected after decision.

## DTS-029 — Exchange Health protection
عند تدهور venue health بشكل مادي: alert + السبب + exposure الحالي + سياق مراجعة/خفض exposure دون ادعاء قرار إلزامي.

## DTS-030 — Stablecoin de-peg protection
لا threshold عالمي ثابت. يجب أن تكون thresholds methodology-driven, volatility-aware, liquidity-aware, source-aware, configurable عند الحاجة.

---

# 7. Smart Money Context

## DTS-031 — Context, not standalone moat
Wallet/Whale/Cluster intelligence مهمة لكنها ليست differentiator مستقل. تربط بالسياق: funding, exchange flows, price reaction, liquidity, sentiment when defensible, prior behavior.

## DTS-032 — Attribution confidence
أي attribution مثل Exchange Cold Wallet / Fund / Whale Cluster يحمل confidence + source + provenance.

## DTS-033 — No unsupported causality
يحظر “impact +2.1%” أو “السعر ارتفع بسبب whale” دون causal methodology. استخدم association/temporal context عند غياب السببية المثبتة.

---

# 8. Daily Evidence Autopsy

## DTS-034
Daily Brief = WHAT CHANGED / WHY IT MATTERS / RISKS OR INVALIDATION. كل نقطة مرتبطة بدليل قابل للفتح. لا AI generic prose غير grounded.

## DTS-035 — Evidence-backed sentences
كل claim مادي يرتبط بـsource + timestamp + freshness + evidence class.

## DTS-036 — User-local delivery
يحترم Global Timezone. 08:00 ليس إلزاميًا؛ يكون user-configurable أو default opt-in حسب المنتج.

---

# 9. Institutional Simulation

## DTS-037 — Simulation beside decision
كل signal/decision مؤهل يتيح “Test on simulated portfolio” دون real-money execution.

## DTS-038 — Simulation methodology
لا تعتمد على آخر 30 يوم فقط. تشمل حيث ينطبق: in-sample, out-of-sample, walk-forward, realistic costs/slippage, liquidity/capacity, latency, regime segmentation, parameter stability, sensitivity, sample adequacy, uncertainty, multiple-testing awareness, overfitting controls.

## DTS-039 — Simulation disclosures
Historical/simulated nature + no future guarantee + methodology version + sample period + assumptions + cost model + evidence class.

## DTS-040 — Portfolio-aware simulation
Output يدعم expected PnL, drawdown, Sharpe/equivalent where valid, breakeven, risk budget impact, capacity limit, uncertainty.

---

# 10. Trust & Vetting Layer

## DTS-041 — Evidence Grade methodology
Grade A–F مبني على Data Integrity, Sample Adequacy, OOS Performance, Walk-Forward Stability, Multiple-Testing Penalty, Regime Robustness, Cost Realism, Liquidity/Capacity, Calibration, Live/Shadow Evidence.

## DTS-042 — Explainable Grade
overall grade + component scores + reason + methodology version + last evaluation timestamp.

## DTS-043 — Evidence Class
BACKTESTED / SIMULATED / SHADOW_LIVE / PRODUCTION_VERIFIED أو canonical equivalents. لا خلط بينها.

---

# 11. نقاط الإبهار الحقيقي — Mandatory Wow Layer

## DTS-044 — Wow #1: Reject bad opportunities
أقوى لحظة إبهار: فرصة raw تبدو رائعة ثم يرفضها BLACKDARK بعد حساب economic/execution reality.

مثال:
```text
RAW OPPORTUNITY +4.7%
BLACKDARK REJECTED IT
Expected Net Edge: +0.8%
Fill Probability: 41%
Expected Realized Edge: -0.2%
Verdict: REJECT
```

## DTS-045 — Wow #2: Portfolio pre-impact
يكشف أن الفرصة قد تبدو مربحة منفردة لكنها ترفع احتمال تجاوز Risk Budget بشكل مادي.

## DTS-046 — Wow #3: NO DECISION
إظهار NO DECISION عند تعارض المصادر أو نقص الأدلة. هذه capability مؤسسية وليست فشلًا.

## DTS-047 — Wow #4: Full Evidence Trail
من أي قرار يصل المستخدم إلى Source, Timestamp, Freshness, Calculation, Cost Autopsy, Net Edge, Execution Feasibility, Capacity, Risk, Evidence Class, Uncertainty, Simulation, Calibration, Invalidation Condition.

## DTS-048 — Wow #5: 30-second truth
خلال ~30 ثانية يعرف المستخدم وضع رأس المال، أهم خطر، أهم فرصة موثوقة، هل تستحق الانتباه، ما الذي تغير، وهل النظام واثق أم abstaining.

---

# 12. العيوب المستبعدة نهائيًا

## DTS-049
يحظر تنفيذ/اعتماد التالي:
1. “كل المتداولين يخسرون 2–5%” بلا evidence.
2. “BLACKDARK هي الوحيدة” بلا benchmark موثق.
3. “كل المنافسين بائعي أوهام”.
4. God View مفروض على الجميع.
5. Net Edge نقطة واحدة بلا uncertainty.
6. Net Edge بلا execution feasibility.
7. محاكاة 30 يوم فقط كدليل جودة.
8. Grade A–F بلا methodology.
9. Accuracy منفردة كدليل trust.
10. causal whale impact بلا causal evidence.
11. fixed depeg threshold عالمي.
12. stress scenario واحد فقط.
13. push الساعة 08:00 إجباري للجميع.
14. recommendation language يقيني بلا uncertainty.
15. لون وحده للدلالة على risk/quality.
16. raw BUY/SELL بلا Decision Contract.
17. عرض cache/stale كأنه live.
18. إخفاء data conflicts.
19. عرض opportunity غير قابلة للتنفيذ كفرصة حقيقية.
20. استخدام backtest performance كضمان مستقبل.

---

# 13. ما هو موجود بالفعل وما يجب ترقيته

> هذه نقطة بدء للفحص وليست تصريحًا بافتراض completion. Cursor يجب أن يثبت الحالة الحالية من repository.

Likely reusable/related capabilities:
- Net-Edge capability (#417)
- Capital Protection Controls (#410)
- Strategy Simulator (#411/#421)
- Daily Market Brief (#474)
- Unified/Dashboard capability (#614)
- Wallet Profiler (#620)
- Whale Tracker (#408)
- Strategy Vetting (#492)
- Data freshness primitives
- Failure/degraded-mode architecture
- Timezone system
- 38-locale i18n
- Identity/Profile
- Billing
- Evidence / abstention primitives
- audit/ledgers

كل عنصر يصنف KEEP / REUSE / IMPROVE / REPLACE / BUILD بعد evidence حقيقي.

---

# 14. ما يجب بناؤه/ترقيته — Priority Matrix

## P0 — Mandatory before strategic closure
1. Formal Net-Edge Spec
2. Cost Autopsy completeness
3. Execution Feasibility Score
4. Opportunity Capacity
5. Net-Edge uncertainty interval
6. Signal Admission Gate
7. Decision Contract
8. Safety Floor
9. Real abstention wiring
10. Evidence/freshness visibility
11. Institutional simulation methodology
12. Outcome/calibration ledger
13. Pre-Registered Outcome Ledger
14. Realizable-vs-theoretical edge separation

## P1 — High differentiation / Wow
15. Opportunity Rejection Engine
16. Why NOT Engine
17. Portfolio Pre-Impact Engine
18. Reverse Stress Testing
19. Decision Change Detector
20. Daily Evidence Autopsy
21. Full Evidence Trail
22. 30-second truth surface

## P2 — Valuable but not primary moat
23. Smart Money narrative
24. Cluster context
25. Optional Command View
26. Whale behavior context
27. Advanced causal analytics only after methodology validation

---

# 15. Decision Truth Scorecard

كل admitted decision ينتج scorecard موحدًا:

```text
Decision State
Net Edge
Realizable Net Edge
Execution Feasibility
Capacity
Opportunity Half-Life
Risk
Portfolio Impact
Evidence Grade
Evidence Class
Freshness
Data Quality
Uncertainty
Simulation Result
Calibration Status
Invalidation Condition
Review Time
Why
Why Not
```

أي field غير قابل للحساب = Unavailable/Not applicable + reason.

---

# 16. Decision Truth API Contract

Minimum conceptual schema:

```text
decision_id
decision_state
detected_at
source_timestamp
freshness_state
data_quality_state

gross_edge
expected_net_edge
realizable_net_edge
net_edge_interval

execution_feasibility_score
fill_probability
capacity
opportunity_half_life

risk_score
portfolio_impact
risk_budget_before
risk_budget_after

evidence_grade
evidence_class
source_count
conflict_state

simulation_summary
calibration_summary

time_horizon
entry_assumptions
invalidation_condition
review_time

admission_state
rejection_reasons
abstention_reasons

why
why_not

methodology_versions
```

---

# 17. Methodology, provenance, integrity

## DTS-050 — Methodology Versioning
كل calculation/grade/simulation/calibration/risk model يحمل methodology version.

## DTS-051 — Evidence Provenance
كل material decision input يدعم source, source timestamp, ingestion timestamp, transformation, methodology version, freshness, quality state.

## DTS-052 — No-Silent-Fallback Rule
إذا استخدم fallback/cached/secondary source يجب أن يعرف Decision Truth Pipeline ذلك، ولا تستمر decision quality كأن المصدر الأصلي live.

## DTS-053 — Failure Integration
يجب دمج STALE/PARTIAL/DEGRADED/UNAVAILABLE/INDETERMINATE من Failure System فعليًا مع admission/decision state.

## DTS-054 — Timezone Integration
كل user-facing time في resolved user timezone؛ كل canonical evidence UTC-aware؛ لا duplicate authority.

## DTS-055 — I18N Integration
كل decision explanation/rejection/abstention/risk copy يستخدم canonical 38-locale i18n architecture؛ لا hard-coded English.

## DTS-056 — Accessibility
WCAG 2.2 AA engineering requirements؛ لا يعتمد على اللون وحده؛ text/symbol/accessible label/keyboard/screen-reader semantics.

## DTS-057 — User-specific risk without false personalization claims
Portfolio-aware context يعتمد فقط على user-configured risk budget + legitimately available portfolio data + transparent assumptions.

## DTS-058 — Anti-cherry-picking
كل performance claim reproducible من ledger. يحظر حذف الخسائر أو تغيير horizon/threshold بعد outcome أو عرض أفضل subset فقط دون disclosure.

## DTS-059 — Calibration-aware confidence
Confidence يقيم مقابل realized calibration. إذا ضعيف/غير كافٍ يظهر CALIBRATION_WEAK أو CALIBRATION_INSUFFICIENT_DATA ولا يعرض كرقم ثقة قوي بلا caveat.

## DTS-060 — Decision history integrity
كل material state change append-only/auditable مع previous state, new state, timestamp, cause, evidence delta, methodology version.

---

# 18. Final strategic principle

التميّز ليس more signals.

```text
Detect more
Reject more bad opportunities
Admit fewer but better decisions
Explain exactly why
Quantify uncertainty
Show portfolio impact before action
Prove historical integrity afterward
```

---

# 19. Cursor Execution Requirements

Cursor MUST:
1. Read this entire file before coding.
2. Audit repository against DTS-001 → DTS-060.
3. Build a requirement ledger.
4. Map real existing capabilities, including #410/#411/#417/#421/#474/#492/#614/#620/#408 where present, to these requirements.
5. Classify each requirement KEEP / REUSE / IMPROVE / REPLACE / BUILD.
6. Implement all locally-buildable missing requirements.
7. Wire each capability into real intended runtime paths.
8. Do not accept helper/module/registry existence as completion.
9. Add behavior-level tests.
10. Add stale/conflict/insufficient-evidence/failure tests.
11. Add anti-bypass tests for Signal Admission Gate.
12. Add calibration/outcome-integrity tests.
13. Add portfolio pre-impact tests.
14. Add realistic cost/execution tests.
15. Add Decision Change Detector tests.
16. Add i18n/timezone/accessibility integration tests.
17. Run targeted tests first.
18. Run one final relevant regression after local green.
19. Perform a second complete source pass DTS-001 → DTS-060.
20. Produce final institutional closure report.

---

# 20. Mandatory Anti-Bypass Gates

```text
SIGNAL_ADMISSION_BYPASS_PATHS=[]
DECISION_CONTRACT_BYPASS_PATHS=[]
NET_EDGE_BYPASS_PATHS=[]
EXECUTION_FEASIBILITY_BYPASS_PATHS=[]
SAFETY_FLOOR_BYPASS_PATHS=[]
ABSTENTION_BYPASS_PATHS=[]
EVIDENCE_GRADE_BYPASS_PATHS=[]
OUTCOME_LEDGER_BYPASS_PATHS=[]
```

أي قائمة غير فارغة = لا Final Engineering Closure.

---

# 21. Mandatory Acceptance Flags

لا claim closure إلا إذا:

```text
NET_EDGE_FORMAL_SPEC_PASS=true
COST_AUTOPSY_PASS=true
NET_EDGE_UNCERTAINTY_PASS=true
REALIZABLE_EDGE_PASS=true

EXECUTION_FEASIBILITY_PASS=true
OPPORTUNITY_CAPACITY_PASS=true
OPPORTUNITY_HALF_LIFE_PASS=true

RISK_BUDGET_PASS=true
PRE_IMPACT_PROTECTION_PASS=true
REVERSE_STRESS_PASS=true

SMART_MONEY_CONTEXT_PASS=true
NO_UNSUPPORTED_CAUSALITY_PASS=true

DAILY_EVIDENCE_AUTOPSY_PASS=true
SIMULATION_INSTITUTIONAL_METHODOLOGY_PASS=true

EVIDENCE_GRADE_PASS=true
EVIDENCE_CLASS_PASS=true

SIGNAL_ADMISSION_GATE_PASS=true
DECISION_CONTRACT_PASS=true
SAFETY_FLOOR_PASS=true

OPPORTUNITY_REJECTION_ENGINE_PASS=true
WHY_NOT_ENGINE_PASS=true

DECISION_CALIBRATION_LEDGER_PASS=true
PRE_REGISTERED_OUTCOME_LEDGER_PASS=true
DECISION_CHANGE_DETECTOR_PASS=true

FULL_EVIDENCE_TRAIL_PASS=true
THIRTY_SECOND_TRUTH_SURFACE_PASS=true

FAILURE_DEGRADED_INTEGRATION_PASS=true
TIMEZONE_INTEGRATION_PASS=true
I18N_38_LOCALES_INTEGRATION_PASS=true
ACCESSIBILITY_WCAG_2_2_AA_PASS=true

ANTI_CHERRY_PICKING_PASS=true
METHODOLOGY_VERSIONING_PASS=true
PROVENANCE_PASS=true
NO_SILENT_FALLBACK_PASS=true

SOURCE_REQUIREMENTS_ACCOUNTED_FOR=100%

KNOWN_LOCAL_DTS_GAPS=[]
KNOWN_LOCAL_DTS_DEFECTS=[]
KNOWN_LOCAL_DTS_INTEGRATION_GAPS=[]
KNOWN_LOCAL_DTS_TEST_GAPS=[]

LOCAL_BUILDABLE_DTS_REQUIREMENTS_REMAINING=0
PARTIALLY_IMPLEMENTED_LOCAL_DTS_REQUIREMENTS=0
UNIMPLEMENTED_LOCAL_DTS_REQUIREMENTS=0
UNVERIFIED_LOCAL_DTS_REQUIREMENTS=0

PASS_ENGINEERING_DECISION_TRUTH_SYSTEM=true
READY_FOR_INTENDED_LOCAL_USE=true
PASS_LIVE_NOT_CLAIMED=true
```

---

# 22. Live Gate

Local engineering closure لا يساوي production/live verification.

Do NOT claim PASS_LIVE without intended-production evidence for applicable areas such as:
- real market latency
- real slippage
- real order-book depth
- live fill probability calibration
- live opportunity decay
- live venue availability
- live stale/partial handling
- live alert delivery
- real portfolio integration
- live calibration updates
- live incident/degraded behavior
- real user timezone/i18n rendering

هذه ليست ذريعة لترك repository-buildable implementation ناقصًا.

---

# 23. Final Closure Rule

Final institutional closure مسموح فقط إذا:
- DTS-001 → DTS-060 كلها accounted for
- كل locally-buildable requirements كاملة
- كل integrations حقيقية
- anti-bypass arrays كلها فارغة
- لا known local material gaps
- لا regression في subsystems الصحيحة
- لا false PASS flags

Allowed closure wording:

> **All requirements in BLACKDARK Decision Truth System — Institutional Final v1 (DTS-001 → DTS-060) are fully accounted for and all locally-buildable requirements are implemented, integrated into intended runtime paths, regression-verified, and reconciled against the governing source. No known local material Decision Truth implementation, integration, methodology, safety, evidence, accessibility, localization, or test gaps remain. Production/live verification remains separately gated and has not been falsely claimed.**

---

# 24. Final Product Principle

BLACKDARK must not win by showing the largest number of opportunities.

It must win by showing:

> **which opportunities survive costs, liquidity, execution, risk, evidence, uncertainty, simulation and historical accountability — and by confidently saying REJECT or NO DECISION when that is the truthful answer.**

# BLACKDARK Decision Truth System
