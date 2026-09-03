# BATCH03_INSTITUTIONAL_PENTAGONAL_COMPLETE

**Generated:** 2026-09-03T11:41:25.588810+00:00 | **Commit:** `651f8e0dbeee` | **Scope:** Batch03 IDs 101–150
**Classification:** LOCAL_GOVERNANCE_COMPLETE — items 1–27 engineering evidence

---

## أ) المبدأ الحاكم (البنود 1–5)

| # | المصدر | التطبيق على Batch03 | الدليل |
|---|--------|---------------------|--------|
| 1 | ISO/IEC 25010 | لا قبول «الكود شغّال» فقط — كل قدرة بخماسي + expected output | `docs/BATCH03_PENTAGONAL_TEMPLATE_101_150.json` |
| 2 | ISO/IEC 25059 + OECD AI | تصنيف rule-based vs ML لكل قدرة | `docs/BATCH03_AI_CAPABILITY_REVIEW.json` — 0 true ML |
| 3 | ISO/IEC/IEEE 29148 | Expected Output مسبق لكل قدرة | قسم ج أدناه + JSON |
| 4 | Google SRE PRR | عمود مراجعة جماعية لكل صف | PRR reference per row |
| 5 | ITIL Service Validation | العمود 8 = AWAITING_DEPLOY حتى Railway | `docs/BATCH03_GATE_ZERO_PRODUCTION.json` |

---

## ط) ترتيب التنفيذ (البند 30) — حالة

| خطوة | الحالة | الدليل |
|------|--------|--------|
| (1) قاموس حالة + RTM 101–150 | ✅ | `docs/BATCH03_RTM.json` |
| (2) قالب خماسي + Expected Output | ✅ | هذا الملف + JSON |
| (3) MECE + عقود 01/02 | ✅ | `docs/BATCH03_MECE_AUDIT.json` + ADRs |
| (4) خريطة أبطال + أوزان + سيناريوهات | ✅ | `docs/BATCH03_HERO_SIX_BINDING_101_150.json` |
| (5) أمان entitlement | ✅ | gateway contract tests + GET proof |
| (6) pytest آخر commit | ✅ | `docs/BATCH03_LOCAL_PYTEST_PROOF.json` |
| (7) بوابة حية + E2E + latency | ⏳ AWAITING_DEPLOY | Gate Zero FAILED |

---

## (1) قاموس حالة RTM — كل 101–150

| ID | Status | Spine | Binding |
|----|--------|-------|---------|
| 101 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap101 |
| 102 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap102 |
| 103 | OVERLAP-PARTIAL | batch01 | cap646/batch01_production.py:cap646.batch01_production.cap_103 |
| 104 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap104 |
| 105 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap105 |
| 106 | REUSED-LINK | batch03 | cap646/batch03_dedicated.py:_cap106 |
| 107 | REUSED-LINK | batch03 | cap646/batch03_dedicated.py:_cap107 |
| 108 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap108 |
| 109 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap109 |
| 110 | REUSED-LINK | batch03 | cap646/batch03_dedicated.py:_cap110 |
| 111 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap111 |
| 112 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap112 |
| 113 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap113 |
| 114 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap114 |
| 115 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap115 |
| 116 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap116 |
| 117 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap117 |
| 118 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap118 |
| 119 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap119 |
| 120 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap120 |
| 121 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap121 |
| 122 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap122 |
| 123 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap123 |
| 124 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap124 |
| 125 | REUSED-LINK | batch03 | cap646/batch03_dedicated.py:_cap125 |
| 126 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap126 |
| 127 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap127 |
| 128 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap128 |
| 129 | OVERLAP-PARTIAL | batch01 | cap646/batch01_production.py:cap646.batch01_production.cap_129 |
| 130 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap130 |
| 131 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap131 |
| 132 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap132 |
| 133 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap133 |
| 134 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap134 |
| 135 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap135 |
| 136 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap136 |
| 137 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap137 |
| 138 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap138 |
| 139 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap139 |
| 140 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap140 |
| 141 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap141 |
| 142 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap142 |
| 143 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap143 |
| 144 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap144 |
| 145 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap145 |
| 146 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap146 |
| 147 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap147 |
| 148 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap148 |
| 149 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap149 |
| 150 | PRODUCTION-ALIGNED | batch03 | cap646/batch03_dedicated.py:_cap150 |

---

## ب) القالب الخماسي — 44 قدرة مستقلة (البنود 6–10)

### ID 101 — AI Data Analyst / Ask AI

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'AI Data Analyst / Ask AI' served via surface 'ai_data_analyst_ask_ai'; Cor:success=True surface matches expected_surface=ai_data_analyst_ask_ai; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap101 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=101; surface=ai_data_analyst_ask_ai; binding_source=explicit_option_a | ACT:success=True; surface=ai_data_analyst_ask_ai; backend=cap646.batch03_production.cap_101 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/101 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 1.0ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 102 — AI-Generated Reporting

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'AI-Generated Reporting' served via surface 'ai_generated_reporting'; Cor:success=True surface matches expected_surface=ai_generated_reporting; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap102 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=102; surface=ai_generated_reporting; binding_source=explicit_option_a | ACT:success=True; surface=ai_generated_reporting; backend=cap646.batch03_production.cap_102 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/102 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 104 — High-Resolution / Block-Level Data Delivery

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'High-Resolution / Block-Level Data Delivery' served via surface 'high_resolution_block_level_data_delivery'; Cor:success=True surface matches expected_surface=high_resolution_block_level_data_delivery; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap104 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=104; surface=high_resolution_block_level_data_delivery; binding_source=explicit_option_a | ACT:success=True; surface=high_resolution_block_level_data_delivery; backend=cap646.batch03_production.cap_104 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/104 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 5.7ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 105 — Historical Full-Data Layer

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Historical Full-Data Layer' served via surface 'historical_full_data_layer'; Cor:success=True surface matches expected_surface=historical_full_data_layer; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap105 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=105; surface=historical_full_data_layer; binding_source=explicit_option_a | ACT:success=True; surface=historical_full_data_layer; backend=cap646.batch03_production.cap_105 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/105 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 2.0ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 108 — Institutional Data & API Delivery

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Institutional Data & API Delivery' served via surface 'institutional_data_api_delivery'; Cor:success=True surface matches expected_surface=institutional_data_api_delivery; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap108 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=108; surface=institutional_data_api_delivery; binding_source=explicit_option_a | ACT:success=True; surface=institutional_data_api_delivery; backend=cap646.batch03_production.cap_108 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/108 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 109 — White-Label Research & Reporting

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'White-Label Research & Reporting' served via surface 'white_label_research_reporting'; Cor:success=True surface matches expected_surface=white_label_research_reporting; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap109 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=109; surface=white_label_research_reporting; binding_source=explicit_option_a | ACT:success=True; surface=white_label_research_reporting; backend=cap646.batch03_production.cap_109 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/109 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 743.7ms / limit 2000ms (analysis) | within:True | PROD: AWAITING_DEPLOY |

### ID 111 — Exchange Flow Actionability Score

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Exchange Flow Actionability Score' served via surface 'exchange_flow_actionability_score'; Cor:success=True surface matches expected_surface=exchange_flow_actionability_score; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap111 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=111; surface=exchange_flow_actionability_score; binding_source=explicit_option_a | ACT:success=True; surface=exchange_flow_actionability_score; backend=cap646.batch03_production.cap_111 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/111 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.9ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 112 — Flow-to-Price Explanation Engine

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Flow-to-Price Explanation Engine' served via surface 'flow_to_price_explanation_engine'; Cor:success=True surface matches expected_surface=flow_to_price_explanation_engine; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap112 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=112; surface=flow_to_price_explanation_engine; binding_source=explicit_option_a | ACT:success=True; surface=flow_to_price_explanation_engine; backend=cap646.batch03_production.cap_112 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/112 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 113 — Asset Intelligence Profiles

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Asset Intelligence Profiles' served via surface 'asset_intelligence_profiles'; Cor:success=True surface matches expected_surface=asset_intelligence_profiles; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap113 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=113; surface=asset_intelligence_profiles; binding_source=explicit_option_a | ACT:success=True; surface=asset_intelligence_profiles; backend=cap646.batch03_production.cap_113 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/113 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 114 — Asset Classification & Taxonomy

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Asset Classification & Taxonomy' served via surface 'asset_classification_taxonomy'; Cor:success=True surface matches expected_surface=asset_classification_taxonomy; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap114 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=114; surface=asset_classification_taxonomy; binding_source=explicit_option_a | ACT:success=True; surface=asset_classification_taxonomy; backend=cap646.batch03_production.cap_114 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/114 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 115 — Asset Screener

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Asset Screener' served via surface 'asset_screener'; Cor:success=True surface matches expected_surface=asset_screener; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap115 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=115; surface=asset_screener; binding_source=explicit_option_a | ACT:success=True; surface=asset_screener; backend=cap646.batch03_production.cap_115 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/115 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 116 — Market Pair Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Market Pair Intelligence' served via surface 'market_pair_intelligence'; Cor:success=True surface matches expected_surface=market_pair_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap116 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=116; surface=market_pair_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=market_pair_intelligence; backend=cap646.batch03_production.cap_116 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/116 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 2.8ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 117 — Real Volume / Quality-Adjusted Volume

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Real Volume / Quality-Adjusted Volume' served via surface 'real_volume_quality_adjusted_volume'; Cor:success=True surface matches expected_surface=real_volume_quality_adjusted_volume; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap117 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=117; surface=real_volume_quality_adjusted_volume; binding_source=explicit_option_a | ACT:success=True; surface=real_volume_quality_adjusted_volume; backend=cap646.batch03_production.cap_117 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/117 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 118 — VWAP Price Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'VWAP Price Intelligence' served via surface 'vwap_price_intelligence'; Cor:success=True surface matches expected_surface=vwap_price_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap118 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=118; surface=vwap_price_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=vwap_price_intelligence; backend=cap646.batch03_production.cap_118 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/118 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.8ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 119 — Market Cap & FDV Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Market Cap & FDV Intelligence' served via surface 'market_cap_fdv_intelligence'; Cor:success=True surface matches expected_surface=market_cap_fdv_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap119 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=119; surface=market_cap_fdv_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=market_cap_fdv_intelligence; backend=cap646.batch03_production.cap_119 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/119 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 622.7ms / limit 2000ms (analysis) | within:True | PROD: AWAITING_DEPLOY |

### ID 120 — Supply Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Supply Intelligence' served via surface 'supply_intelligence'; Cor:success=True surface matches expected_surface=supply_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap120 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=120; surface=supply_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=supply_intelligence; backend=cap646.batch03_production.cap_120 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/120 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 1.3ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 121 — ROI & ATH Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'ROI & ATH Intelligence' served via surface 'roi_ath_intelligence'; Cor:success=True surface matches expected_surface=roi_ath_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap121 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=121; surface=roi_ath_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=roi_ath_intelligence; backend=cap646.batch03_production.cap_121 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/121 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.8ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 122 — Volatility Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Volatility Intelligence' served via surface 'volatility_intelligence'; Cor:success=True surface matches expected_surface=volatility_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap122 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=122; surface=volatility_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=volatility_intelligence; backend=cap646.batch03_production.cap_122 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/122 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 1.9ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 123 — Sharpe Ratio Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Sharpe Ratio Intelligence' served via surface 'sharpe_ratio_intelligence'; Cor:success=True surface matches expected_surface=sharpe_ratio_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap123 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=123; surface=sharpe_ratio_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=sharpe_ratio_intelligence; backend=cap646.batch03_production.cap_123 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/123 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 124 — Futures Funding Rate Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Futures Funding Rate Intelligence' served via surface 'futures_funding_rate_intelligence'; Cor:success=True surface matches expected_surface=futures_funding_rate_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap124 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=124; surface=futures_funding_rate_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=futures_funding_rate_intelligence; backend=cap646.batch03_production.cap_124 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/124 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 126 — Futures Volume Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Futures Volume Intelligence' served via surface 'futures_volume_intelligence'; Cor:success=True surface matches expected_surface=futures_volume_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap126 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=126; surface=futures_volume_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=futures_volume_intelligence; backend=cap646.batch03_production.cap_126 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/126 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 127 — Multi-Factor Market Overview

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Multi-Factor Market Overview' served via surface 'multi_factor_market_overview'; Cor:success=True surface matches expected_surface=multi_factor_market_overview; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap127 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=127; surface=multi_factor_market_overview; binding_source=explicit_option_a | ACT:success=True; surface=multi_factor_market_overview; backend=cap646.batch03_production.cap_127 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/127 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 128 — Momentum Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Momentum Intelligence' served via surface 'momentum_intelligence'; Cor:success=True surface matches expected_surface=momentum_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap128 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=128; surface=momentum_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=momentum_intelligence; backend=cap646.batch03_production.cap_128 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/128 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 3.0ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 130 — Mindshare Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Mindshare Intelligence' served via surface 'mindshare_intelligence'; Cor:success=True surface matches expected_surface=mindshare_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap130 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=130; surface=mindshare_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=mindshare_intelligence; backend=cap646.batch03_production.cap_130 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/130 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 131 — Narrative & Sector Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Narrative & Sector Intelligence' served via surface 'narrative_sector_intelligence'; Cor:success=True surface matches expected_surface=narrative_sector_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap131 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=131; surface=narrative_sector_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=narrative_sector_intelligence; backend=cap646.batch03_production.cap_131 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/131 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 93.7ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 132 — Mindshare Gainers / Losers

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Mindshare Gainers / Losers' served via surface 'mindshare_gainers_losers'; Cor:success=True surface matches expected_surface=mindshare_gainers_losers; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap132 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=132; surface=mindshare_gainers_losers; binding_source=explicit_option_a | ACT:success=True; surface=mindshare_gainers_losers; backend=cap646.batch03_production.cap_132 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/132 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.6ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 133 — Curated Crypto News Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Curated Crypto News Intelligence' served via surface 'curated_crypto_news_intelligence'; Cor:success=True surface matches expected_surface=curated_crypto_news_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap133 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=133; surface=curated_crypto_news_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=curated_crypto_news_intelligence; backend=cap646.batch03_production.cap_133 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/133 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 109.7ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 134 — AI News Summaries

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'AI News Summaries' served via surface 'ai_news_summaries'; Cor:success=True surface matches expected_surface=ai_news_summaries; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap134 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=134; surface=ai_news_summaries; binding_source=explicit_option_a | ACT:success=True; surface=ai_news_summaries; backend=cap646.batch03_production.cap_134 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/134 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 91.0ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 135 — Real-Time Industry Event Monitoring

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Real-Time Industry Event Monitoring' served via surface 'real_time_industry_event_monitoring'; Cor:success=True surface matches expected_surface=real_time_industry_event_monitoring; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap135 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=135; surface=real_time_industry_event_monitoring; binding_source=explicit_option_a | ACT:success=True; surface=real_time_industry_event_monitoring; backend=cap646.batch03_production.cap_135 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/135 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.6ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 136 — Agentic Monitoring Views

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Agentic Monitoring Views' served via surface 'agentic_monitoring_views'; Cor:success=True surface matches expected_surface=agentic_monitoring_views; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap136 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=136; surface=agentic_monitoring_views; binding_source=explicit_option_a | ACT:success=True; surface=agentic_monitoring_views; backend=cap646.batch03_production.cap_136 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/136 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 137 — Custom Watchlists

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Custom Watchlists' served via surface 'custom_watchlists'; Cor:success=True surface matches expected_surface=custom_watchlists; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap137 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=137; surface=custom_watchlists; binding_source=explicit_option_a | ACT:success=True; surface=custom_watchlists; backend=cap646.batch03_production.cap_137 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/137 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 138 — Token Unlock Calendar

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Token Unlock Calendar' served via surface 'token_unlock_calendar'; Cor:success=True surface matches expected_surface=token_unlock_calendar; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap138 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=138; surface=token_unlock_calendar; binding_source=explicit_option_a | ACT:success=True; surface=token_unlock_calendar; backend=cap646.batch03_production.cap_138 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/138 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 139 — Vesting Schedule Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Vesting Schedule Intelligence' served via surface 'vesting_schedule_intelligence'; Cor:success=True surface matches expected_surface=vesting_schedule_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap139 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=139; surface=vesting_schedule_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=vesting_schedule_intelligence; backend=cap646.batch03_production.cap_139 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/139 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 1.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 140 — Token Allocation Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Token Allocation Intelligence' served via surface 'token_allocation_intelligence'; Cor:success=True surface matches expected_surface=token_allocation_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap140 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=140; surface=token_allocation_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=token_allocation_intelligence; backend=cap646.batch03_production.cap_140 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/140 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.9ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 141 — Unlock Impact Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Unlock Impact Intelligence' served via surface 'unlock_impact_intelligence'; Cor:success=True surface matches expected_surface=unlock_impact_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap141 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=141; surface=unlock_impact_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=unlock_impact_intelligence; backend=cap646.batch03_production.cap_141 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/141 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 142 — Fundraising Rounds Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Fundraising Rounds Intelligence' served via surface 'fundraising_rounds_intelligence'; Cor:success=True surface matches expected_surface=fundraising_rounds_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap142 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=142; surface=fundraising_rounds_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=fundraising_rounds_intelligence; backend=cap646.batch03_production.cap_142 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/142 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 143 — Investor Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Investor Intelligence' served via surface 'investor_intelligence'; Cor:success=True surface matches expected_surface=investor_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap143 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=143; surface=investor_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=investor_intelligence; backend=cap646.batch03_production.cap_143 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/143 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 144 — Fund & Fund-Manager Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Fund & Fund-Manager Intelligence' served via surface 'fund_fund_manager_intelligence'; Cor:success=True surface matches expected_surface=fund_fund_manager_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap144 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=144; surface=fund_fund_manager_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=fund_fund_manager_intelligence; backend=cap646.batch03_production.cap_144 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/144 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.4ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 145 — M&A Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'M&A Intelligence' served via surface 'm_a_intelligence'; Cor:success=True surface matches expected_surface=m_a_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap145 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=145; surface=m_a_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=m_a_intelligence; backend=cap646.batch03_production.cap_145 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/145 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 598.8ms / limit 2000ms (analysis) | within:True | PROD: AWAITING_DEPLOY |

### ID 146 — Capital Flow & Funding Trend Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Capital Flow & Funding Trend Intelligence' served via surface 'capital_flow_funding_trend_intelligence'; Cor:success=True surface matches expected_surface=capital_flow_funding_trend_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap146 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=146; surface=capital_flow_funding_trend_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=capital_flow_funding_trend_intelligence; backend=cap646.batch03_production.cap_146 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/146 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 614.3ms / limit 2000ms (analysis) | within:True | PROD: AWAITING_DEPLOY |

### ID 147 — Comparable Funding & Valuation Analysis

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Comparable Funding & Valuation Analysis' served via surface 'comparable_funding_valuation_analysis'; Cor:success=True surface matches expected_surface=comparable_funding_valuation_analysis; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap147 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=147; surface=comparable_funding_valuation_analysis; binding_source=explicit_option_a | ACT:success=True; surface=comparable_funding_valuation_analysis; backend=cap646.batch03_production.cap_147 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/147 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 196.2ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 148 — Due Diligence Report Engine

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Due Diligence Report Engine' served via surface 'due_diligence_report_engine'; Cor:success=True surface matches expected_surface=due_diligence_report_engine; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap148 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=148; surface=due_diligence_report_engine; binding_source=explicit_option_a | ACT:success=True; surface=due_diligence_report_engine; backend=cap646.batch03_production.cap_148 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/148 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.6ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 149 — Automated Risk Scoring from Diligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Automated Risk Scoring from Diligence' served via surface 'automated_risk_scoring_from_diligence'; Cor:success=True surface matches expected_surface=automated_risk_scoring_from_diligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap149 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=149; surface=automated_risk_scoring_from_diligence; binding_source=explicit_option_a | ACT:success=True; surface=automated_risk_scoring_from_diligence; backend=cap646.batch03_production.cap_149 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/149 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 0.5ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

### ID 150 — Protocol KPI Intelligence

| العمود | المصدر | الدليل |
|--------|--------|--------|
| 6 الهدف الداخلي (25010) | Completeness/Correctness/Appropriateness | C:Catalog goal 'Protocol KPI Intelligence' served via surface 'protocol_kpi_intelligence'; Cor:success=True surface matches expected_surface=protocol_kpi_intelligence; App:Goal-specific payload via cap646/batch03_dedicated.py:_cap150 |
| 7 النتيجة الخارجية (29148) | Expected vs Actual | EXP:success=true; capability_id=150; surface=protocol_kpi_intelligence; binding_source=explicit_option_a | ACT:success=True; surface=protocol_kpi_intelligence; backend=cap646.batch03_production.cap_150 | MATCH:True |
| 8 الواجهة (29119) | /api/cap646/150 | LOCAL:tests/cap646/test_batch03_prep_dedicated.py::test_batch03_runtime_production_path | LIVE:AWAITING_DEPLOY — Railway 404 per docs/BATCH03_GATE_ZERO_PRODUCTION.json |
| 9 الأمان (ASVS) | entitlement | cap646.runtime.execute_capability → entitlement_engine.check(canonical_id) before spine dispatch | paid:False |
| 10 المراجعة (SRE PRR) | docs/BATCH03_LOCAL_GOVERNANCE_COMPLETE.md + PR #362 CI gateway contracts | LOCAL_GOVERNANCE_COMPLETE agent run 2026-09-03 |
| 13 Lookahead | Deterministic seed/sym params; no future timestamps in signal construction (batch03_dedicated) |
| 14 AI (25059) | rule_based_N/A_PSI |
| 17 PSI | N/A — rule-based |
| 25 Latency (local) | 1.3ms / limit 500ms (direct_data) | within:True | PROD: AWAITING_DEPLOY |

---

## ج) Expected Output — ملخص 44 صف (البنود 11–13)

| ID | Expected Output (29148) | Actual (probe session) | Match |
|----|-------------------------|------------------------|-------|
| 101 | success=true; capability_id=101; surface=ai_data_analyst_ask_ai; binding_source=... | surface=ai_data_analyst_ask_ai | True |
| 102 | success=true; capability_id=102; surface=ai_generated_reporting; binding_source=... | surface=ai_generated_reporting | True |
| 104 | success=true; capability_id=104; surface=high_resolution_block_level_data_delive... | surface=high_resolution_block_level_data_delivery | True |
| 105 | success=true; capability_id=105; surface=historical_full_data_layer; binding_sou... | surface=historical_full_data_layer | True |
| 108 | success=true; capability_id=108; surface=institutional_data_api_delivery; bindin... | surface=institutional_data_api_delivery | True |
| 109 | success=true; capability_id=109; surface=white_label_research_reporting; binding... | surface=white_label_research_reporting | True |
| 111 | success=true; capability_id=111; surface=exchange_flow_actionability_score; bind... | surface=exchange_flow_actionability_score | True |
| 112 | success=true; capability_id=112; surface=flow_to_price_explanation_engine; bindi... | surface=flow_to_price_explanation_engine | True |
| 113 | success=true; capability_id=113; surface=asset_intelligence_profiles; binding_so... | surface=asset_intelligence_profiles | True |
| 114 | success=true; capability_id=114; surface=asset_classification_taxonomy; binding_... | surface=asset_classification_taxonomy | True |
| 115 | success=true; capability_id=115; surface=asset_screener; binding_source=explicit... | surface=asset_screener | True |
| 116 | success=true; capability_id=116; surface=market_pair_intelligence; binding_sourc... | surface=market_pair_intelligence | True |
| 117 | success=true; capability_id=117; surface=real_volume_quality_adjusted_volume; bi... | surface=real_volume_quality_adjusted_volume | True |
| 118 | success=true; capability_id=118; surface=vwap_price_intelligence; binding_source... | surface=vwap_price_intelligence | True |
| 119 | success=true; capability_id=119; surface=market_cap_fdv_intelligence; binding_so... | surface=market_cap_fdv_intelligence | True |
| 120 | success=true; capability_id=120; surface=supply_intelligence; binding_source=exp... | surface=supply_intelligence | True |
| 121 | success=true; capability_id=121; surface=roi_ath_intelligence; binding_source=ex... | surface=roi_ath_intelligence | True |
| 122 | success=true; capability_id=122; surface=volatility_intelligence; binding_source... | surface=volatility_intelligence | True |
| 123 | success=true; capability_id=123; surface=sharpe_ratio_intelligence; binding_sour... | surface=sharpe_ratio_intelligence | True |
| 124 | success=true; capability_id=124; surface=futures_funding_rate_intelligence; bind... | surface=futures_funding_rate_intelligence | True |
| 126 | success=true; capability_id=126; surface=futures_volume_intelligence; binding_so... | surface=futures_volume_intelligence | True |
| 127 | success=true; capability_id=127; surface=multi_factor_market_overview; binding_s... | surface=multi_factor_market_overview | True |
| 128 | success=true; capability_id=128; surface=momentum_intelligence; binding_source=e... | surface=momentum_intelligence | True |
| 130 | success=true; capability_id=130; surface=mindshare_intelligence; binding_source=... | surface=mindshare_intelligence | True |
| 131 | success=true; capability_id=131; surface=narrative_sector_intelligence; binding_... | surface=narrative_sector_intelligence | True |
| 132 | success=true; capability_id=132; surface=mindshare_gainers_losers; binding_sourc... | surface=mindshare_gainers_losers | True |
| 133 | success=true; capability_id=133; surface=curated_crypto_news_intelligence; bindi... | surface=curated_crypto_news_intelligence | True |
| 134 | success=true; capability_id=134; surface=ai_news_summaries; binding_source=expli... | surface=ai_news_summaries | True |
| 135 | success=true; capability_id=135; surface=real_time_industry_event_monitoring; bi... | surface=real_time_industry_event_monitoring | True |
| 136 | success=true; capability_id=136; surface=agentic_monitoring_views; binding_sourc... | surface=agentic_monitoring_views | True |
| 137 | success=true; capability_id=137; surface=custom_watchlists; binding_source=expli... | surface=custom_watchlists | True |
| 138 | success=true; capability_id=138; surface=token_unlock_calendar; binding_source=e... | surface=token_unlock_calendar | True |
| 139 | success=true; capability_id=139; surface=vesting_schedule_intelligence; binding_... | surface=vesting_schedule_intelligence | True |
| 140 | success=true; capability_id=140; surface=token_allocation_intelligence; binding_... | surface=token_allocation_intelligence | True |
| 141 | success=true; capability_id=141; surface=unlock_impact_intelligence; binding_sou... | surface=unlock_impact_intelligence | True |
| 142 | success=true; capability_id=142; surface=fundraising_rounds_intelligence; bindin... | surface=fundraising_rounds_intelligence | True |
| 143 | success=true; capability_id=143; surface=investor_intelligence; binding_source=e... | surface=investor_intelligence | True |
| 144 | success=true; capability_id=144; surface=fund_fund_manager_intelligence; binding... | surface=fund_fund_manager_intelligence | True |
| 145 | success=true; capability_id=145; surface=m_a_intelligence; binding_source=explic... | surface=m_a_intelligence | True |
| 146 | success=true; capability_id=146; surface=capital_flow_funding_trend_intelligence... | surface=capital_flow_funding_trend_intelligence | True |
| 147 | success=true; capability_id=147; surface=comparable_funding_valuation_analysis; ... | surface=comparable_funding_valuation_analysis | True |
| 148 | success=true; capability_id=148; surface=due_diligence_report_engine; binding_so... | surface=due_diligence_report_engine | True |
| 149 | success=true; capability_id=149; surface=automated_risk_scoring_from_diligence; ... | surface=automated_risk_scoring_from_diligence | True |
| 150 | success=true; capability_id=150; surface=protocol_kpi_intelligence; binding_sour... | surface=protocol_kpi_intelligence | True |

---

## د) AI العلمية (البنود 14–17)

جميع الـ44 مستقلة: **rule-based** — PSI/KS **N/A** لكل ID. مرجع: `docs/BATCH03_AI_CAPABILITY_REVIEW.json`.

---

## هـ) طبقة الأبطال الستة (البنود 18–24)

**44 مستقلة:** لا ربط مباشر بأي بطل (نفي: `rg heroes cap646/batch03*` → 0).

**REUSED-LINK → canonical → أبطال:**

| Duplicate | Canonical | أبطال مغذّية |
|-----------|-----------|-------------|
| 106 | 63 | Public Accuracy Ledger |
| 107 | 64 | Public Accuracy Ledger |
| 110 | 69 | Single-Sentence Oracle, Arbitrage Scanner |
| 125 | 85 | Arbitrage Scanner, Whale Signal vs Noise, Stealth Advisor |

**بند 24 — أثر عيب gateway/canonical (ITIL):**
- {"issue": "gateway checked raw ID before canonical_id fix", "affected_pairs": ["110→69", "125→85"], "heroes_potentially_affected": ["Single-Sentence Oracle", "Arbitrage Scanner", "Whale Signal vs Noise", "Stealth Advisor"], "status": "CLOSED in code — tests/cap646/test_batch03_gateway_canonical_entitlement_contract.py", "user_visible_period": "pre-2026-09-03 until gateway fix commit f5bae3f"}

تفاصيل كاملة: `docs/BATCH03_HERO_SIX_BINDING_101_150.json`

---

## ز) الأمان (البنود 26–27)

| فحص | النتيجة | الدليل |
|------|---------|--------|
| gateway↔canonical entitlement | ✅ aligned | `tests/cap646/test_batch03_gateway_canonical_entitlement_contract.py` |
| REUSED-LINK Type-4 | ✅ | `tests/cap646/test_batch03_reused_link_contract.py` |
| SLSA same commit | ✅ local session | commit `{commit[:12]}` + probe timestamps in JSON |

---

## ح) ما يُكمَل الآن vs ما ينتظر Railway (البنود 28–29)

- **يُكمَل الآن:** البنود 1–27 هندسيًا (هذا الملف)
- **لا يُعلَن جاهزية حية 100%:** حتى Gate Zero + E2E + latency إنتاج

---

## مقياسان منفصلان

```
batch03_independent = 44
progress_826 = 148
```

---

هذا التسليم يغطي البنود الهندسية 1-27 بدرجة LOCAL_GOVERNANCE_COMPLETE. لا إعلان جاهزية حية 100% قبل استيفاء البند 29 (البوابة الحية + E2E + latency على الإنتاج الفعلي) بعد استعادة Railway.
