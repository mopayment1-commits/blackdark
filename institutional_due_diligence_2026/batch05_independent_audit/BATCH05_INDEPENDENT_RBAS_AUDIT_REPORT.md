# Batch 05 Independent RBAS Due Diligence Report (IDs 201–250)
**Generated:** 2026-09-11T09:04:52.735320+00:00  
**Run:** Master Contract 013 — RBAS-001 risk-based diagnostic audit  
**Auditor role:** Third Line of Defense — Independent Assurance  
**Policies:** RTM-IND-001 | SCORE-IDX-001 | CROSS-SPINE-001 | WF-027 | RBAS-001  

## RBAS-001 Tier Classification (all 50 IDs)

| ID | Capability | Tier | Reason |
|---:|---|---|---|
| 201 | Network Growth Intelligence | **TIER2** | Network growth intelligence — on-chain metric delivery (no user verdict score) |
| 202 | Supply Distribution Intelligence | **TIER2** | Supply distribution intelligence — distribution metric delivery |
| 203 | DEX Trading Intelligence | **TIER2** | DEX trading intelligence — market data delivery |
| 204 | DeFi Protocol Activity Intelligence | **TIER2** | DeFi protocol activity intelligence — activity metric delivery |
| 205 | Open Interest Intelligence | **TIER2** | Open Interest Intelligence — derivatives metric delivery |
| 206 | Funding Rate Intelligence | **TIER2** | Funding Rate Intelligence — metric delivery (duplicate_of=86) |
| 207 | Price / Volume / Market Metrics | **TIER2** | Price / Volume / Market Metrics — market metric delivery |
| 208 | Metric Correlation Workbench | **TIER2** | Metric Correlation Workbench — analysis workbench (no score output) |
| 209 | Custom Chart Builder | **TIER2** | Custom Chart Builder — chart builder delivery |
| 210 | Custom Dashboards / Layouts | **TIER2** | Custom Dashboards / Layouts — dashboard delivery |
| 211 | Screener | **TIER2** | Screener — screening tool without scored verdict |
| 212 | Smart Alerts | **TIER2** | Smart Alerts — alert delivery (duplicate_of=17) |
| 213 | Anomaly Detection Alerts | **TIER2** | Anomaly Detection Alerts — alert feed delivery |
| 214 | Watchlists | **TIER1** | WF-027 dormant legacy ID — Watchlists (T11); mandatory full audit |
| 215 | Community Explorer | **TIER2** | Community Explorer — catalog/explorer delivery |
| 216 | Research & Market Insights | **TIER2** | Research & Market Insights — research delivery |
| 217 | SanAPI-Style Data Access | **TIER2** | SanAPI-Style Data Access — data access delivery |
| 218 | Google Sheets Integration | **TIER2** | Google Sheets Integration — integration delivery |
| 219 | Metric Availability Registry | **TIER2** | Metric Availability Registry — registry/catalog |
| 220 | Data Stabilization & Mutability Metadata | **TIER2** | Data Stabilization & Mutability Metadata — metadata delivery |
| 221 | Data Quality & Provenance Layer | **TIER2** | Data Quality & Provenance Layer — provenance delivery (duplicate_of=63) |
| 222 | Metric Methodology Registry | **TIER2** | Metric Methodology Registry — methodology registry |
| 223 | Social-to-On-Chain Confirmation Engine | **TIER1** | Social-to-On-Chain Confirmation Engine — confirmation/decision output |
| 224 | Narrative Actionability Score | **TIER1** | Narrative Actionability Score — SCORE-IDX surface |
| 225 | Development-to-Market Divergence Detector | **TIER1** | Development-to-Market Divergence Detector — divergence signal influences decisions |
| 226 | Cross-Domain Decision Intelligence Layer | **TIER1** | Cross-Domain Decision Intelligence Layer — explicit decision output |
| 227 | Unified Trading Intelligence Workspace | **TIER1** | Unified Trading Intelligence Workspace — trading decision workspace |
| 228 | Funding Rate Intelligence | **TIER2** | Funding Rate Intelligence — metric delivery (duplicate_of=86) |
| 229 | Cross-Exchange Funding Arbitrage Scanner | **TIER1** | Cross-Exchange Funding Arbitrage Scanner — arbitrage/trading decision surface |
| 230 | Spot-Perp Arbitrage Scanner | **TIER1** | Spot-Perp Arbitrage Scanner — arbitrage/trading decision surface |
| 231 | Futures Basis & Term Structure | **TIER2** | Futures Basis & Term Structure — term structure metric delivery |
| 232 | Open Interest Intelligence | **TIER2** | Open Interest Intelligence — metric delivery (duplicate_of=205) |
| 233 | Liquidation Intelligence | **TIER2** | Liquidation Intelligence — metric delivery (duplicate_of=88) |
| 234 | CVD Intelligence | **TIER2** | CVD Intelligence — volume delta metric delivery |
| 235 | Long/Short Ratio Intelligence | **TIER2** | Long/Short Ratio Intelligence — ratio metric delivery |
| 236 | DEX Screener | **TIER2** | DEX Screener — screener delivery |
| 237 | Token Risk Scoring | **TIER1** | Token Risk Scoring — SCORE-IDX surface |
| 238 | Pump & Dump Detection | **TIER1** | Pump & Dump Detection — detection verdict influences user action |
| 239 | Narrative Tracking | **TIER2** | Narrative Tracking — narrative catalog tracking |
| 240 | Sector Rotation Intelligence | **TIER1** | Sector Rotation Intelligence — portfolio allocation decision-adjacent |
| 241 | Sentiment Intelligence | **TIER1** | Sentiment Intelligence — sentiment index (duplicate_of=129; SCORE-IDX pattern) |
| 242 | Price Prediction / Multi-Signal Forecast | **TIER1** | Price Prediction / Multi-Signal Forecast — AI prediction (NIST AI RMF full path) |
| 243 | Correlation Matrix | **TIER2** | Correlation Matrix — correlation data tool |
| 244 | New Listings Intelligence | **TIER2** | New Listings Intelligence — listings feed delivery |
| 245 | Market Health & Freshness | **TIER1** | WF-027 dormant legacy ID — Market Health & Freshness (T13); mandatory full audit |
| 246 | Coverage Metadata Registry | **TIER2** | Coverage Metadata Registry — coverage registry |
| 247 | Public REST API | **TIER2** | Public REST API — API delivery surface |
| 248 | MCP Server for AI Agents | **TIER2** | MCP Server for AI Agents — platform delivery |
| 249 | CLI Access | **TIER2** | CLI Access — CLI delivery |
| 250 | OpenAPI / SDK Generation | **TIER2** | OpenAPI / SDK Generation — SDK generation delivery |

**Tier summary:** TIER1=14 | TIER2=36  

## RBAS Impact Metrics

- **Tier1 executed:** 14 IDs — 126 phase checks — 13071 ms
- **Tier2 abbreviated:** 28 IDs — 84 phase checks — 9610 ms
- **Tier2 escalated to Tier1:** 8 IDs — 96 phase checks — 27267 ms
- **CONCEPTUALLY-UNSOUND:** 0/50

## WF-027 / CROSS-SPINE Preflight

- **Routing overlaps (BATCH01∩BATCH02∩BATCH03∩BATCH05):** 0 IDs `[]`
- **WF-027 dormant legacy in batch05 range (201–250):** `[214, 245]`
- **Cross-spine resolved IDs 214/245:** dedicated batch05 handler Run 013; classification from scratch (no batch01 carry-over)

## Results Table

| ID | الاسم | RBAS | Path | الحالة النهائية | المرحلة | المعيار المرجعي | SPLIT-BRAIN | الدليل | الخطورة |
|---:|---|---|---|---|---|---|---|---|---|
| 201 | Network Growth Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=network_growth_intelligence spine=batch05_prep; code: async def _cap201(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 202 | Supply Distribution Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=supply_distribution_intelligence spine=batch05_prep; code: async def _cap202(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 203 | DEX Trading Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=dex_trading_intelligence spine=batch05_prep; code: async def _cap203(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 204 | DeFi Protocol Activity Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=defi_protocol_activity_intelligence spine=batch05_prep; code: async def _cap204(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 205 | Open Interest Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=open_interest_intelligence spine=batch05_prep; code: async def _cap205(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 206 | Funding Rate Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=funding_rate_intelligence spine=batch05_prep; code: async def _cap206(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 207 | Price / Volume / Market Metrics | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=price_volume_market_metrics spine=batch05_prep; code: async def _cap207(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 208 | Metric Correlation Workbench | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=metric_correlation_workbench spine=batch05_prep; code: async def _cap208(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 209 | Custom Chart Builder | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=custom_chart_builder spine=batch05_prep; code: async def _cap209(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 210 | Custom Dashboards / Layouts | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=custom_dashboards_layouts spine=batch05_prep; code: async def _cap210(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 211 | Screener | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=screener spine=batch05_prep; code: async def _cap211(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 212 | Smart Alerts | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=smart_alerts spine=batch05_prep; code: async def _cap212(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 213 | Anomaly Detection Alerts | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=anomaly_detection_alerts spine=batch05_prep; code: async def _cap213(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 214 | Watchlists | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | CROSS-SPINE-001 resolved Run013: spine=batch05_prep module=cap646.batch05_production; split_brain=DEDICATED_ONLY; runtime success=True surface=watchlists spine=batch05_prep; code: async def _cap214(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; OWASP API: route prefix /api/cap646/214 not found in static scan | متوسط — |
| 215 | Community Explorer | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=community_explorer spine=batch05_prep; code: async def _cap215(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 216 | Research & Market Insights | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=research_market_insights spine=batch05_prep; code: async def _cap216(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 217 | SanAPI-Style Data Access | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=sanapi_style_data_access spine=batch05_prep; code: async def _cap217(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 218 | Google Sheets Integration | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=google_sheets_integration spine=batch05_prep; code: async def _cap218(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 219 | Metric Availability Registry | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=metric_availability_registry spine=batch05_prep; code: async def _cap219(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 220 | Data Stabilization & Mutability Metadata | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=data_stabilization_mutability_metadata spine=batch05_prep; code: async def _cap220(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 221 | Data Quality & Provenance Layer | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=data_quality_provenance_layer spine=batch05_prep; code: async def _cap221(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 222 | Metric Methodology Registry | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=metric_methodology_registry spine=batch05_prep; code: async def _cap222(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 223 | Social-to-On-Chain Confirmation Engine | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=social_to_on_chain_confirmation_engine spine=batch05_prep; code: async def _cap223(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 224 | Narrative Actionability Score | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=narrative_actionability_score spine=batch05_prep; code: async def _cap224(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 225 | Development-to-Market Divergence Detector | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=development_to_market_divergence_detector spine=batch05_prep; code: async def _cap225(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 226 | Cross-Domain Decision Intelligence Layer | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=cross_domain_decision_intelligence_layer spine=batch05_prep; code: async def _cap226(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 227 | Unified Trading Intelligence Workspace | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=unified_trading_intelligence_workspace spine=batch05_prep; code: async def _cap227(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 228 | Funding Rate Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=funding_rate_intelligence spine=batch05_prep; code: async def _cap228(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 229 | Cross-Exchange Funding Arbitrage Scanner | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=cross_exchange_funding_arbitrage_scanner spine=batch05_prep; code: async def _cap229(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 230 | Spot-Perp Arbitrage Scanner | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=spot_perp_arbitrage_scanner spine=batch05_prep; code: async def _cap230(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 231 | Futures Basis & Term Structure | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=futures_basis_term_structure spine=batch05_prep; code: async def _cap231(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 232 | Open Interest Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=open_interest_intelligence spine=batch05_prep; code: async def _cap232(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 233 | Liquidation Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=liquidation_intelligence spine=batch05_prep; code: async def _cap233(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 234 | CVD Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=cvd_intelligence spine=batch05_prep; code: async def _cap234(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 235 | Long/Short Ratio Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=long_short_ratio_intelligence spine=batch05_prep; code: async def _cap235(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 236 | DEX Screener | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=dex_screener spine=batch05_prep; code: async def _cap236(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 237 | Token Risk Scoring | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=token_risk_scoring spine=batch05_prep; code: async def _cap237(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 238 | Pump & Dump Detection | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=pump_dump_detection spine=batch05_prep; code: async def _cap238(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 239 | Narrative Tracking | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=narrative_tracking spine=batch05_prep; code: async def _cap239(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 240 | Sector Rotation Intelligence | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=sector_rotation_intelligence spine=batch05_prep; code: async def _cap240(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 241 | Sentiment Intelligence | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 3 | NIST AI RMF 1.0 + NIST AI 600-1 GenAI Profile | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=sentiment_intelligence spine=batch05_prep; code: async def _cap241(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; ai_compliance_footer present; ISO 42001 lifecycle not verified | متوسط — |
| 242 | Price Prediction / Multi-Signal Forecast | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=price_prediction_multi_signal_forecast spine=batch05_prep; code: async def _cap242(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 74 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T09:04:14.92465 | متوسط — |
| 243 | Correlation Matrix | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=correlation_matrix spine=batch05_prep; code: async def _cap243(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 244 | New Listings Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=new_listings_intelligence spine=batch05_prep; code: async def _cap244(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 245 | Market Health & Freshness | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | CROSS-SPINE-001 resolved Run013: spine=batch05_prep module=cap646.batch05_production; split_brain=DEDICATED_ONLY; runtime success=True surface=market_health_freshness spine=batch05_prep; code: async def _cap245(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; OWASP API: route prefix /api/cap646/245 not found in static scan | متوسط — |
| 246 | Coverage Metadata Registry | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=coverage_metadata_registry spine=batch05_prep; code: async def _cap246(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 247 | Public REST API | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=public_rest_api spine=batch05_prep; code: async def _cap247(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 248 | MCP Server for AI Agents | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=mcp_server_for_ai_agents spine=batch05_prep; code: async def _cap248(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 249 | CLI Access | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=cli_access spine=batch05_prep; code: async def _cap249(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 250 | OpenAPI / SDK Generation | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=openapi_sdk_generation spine=batch05_prep; code: async def _cap250(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |

## Summary

- **NOT_COMPLETE:** 39/50
- **PERFORMANCE-UNVERIFIABLE:** 11/50

**Independent result:** 0/50 PRODUCTION-ALIGNED  
**CONCEPTUALLY-UNSOUND:** 0/50  
**GIPS ledger:** 74 decisions, simulated_only=True

### SPLIT-BRAIN Summary (mandatory all 50)

- **DEDICATED_ONLY:** 50

### IDs 214/245 — CROSS-SPINE-001 / WF-027 Resolution

- **ID 214:** status=NOT_COMPLETE tier=TIER1 path=TIER1_FULL_9_PHASE; backend=cap646.batch05_dedicated; split=DEDICATED_ONLY
- **ID 245:** status=NOT_COMPLETE tier=TIER1 path=TIER1_FULL_9_PHASE; backend=cap646.batch05_dedicated; split=DEDICATED_ONLY

## Critical Code Evidence (SR 26-2)

- *(none flagged in Run 013 static pre-scan — live audit above is authoritative)*

## رأي اللجنة المستقلة

بصفتنا لجنة تدقيق مستقلة (Third Line of Defense — IIA IPPF)، وبعد تنفيذ RBAS-001 على Batch 05 (IDs 201–250) وفق SR 26-2 وCOSO وGIPS وRTM-IND-001 وCROSS-SPINE-001، صُنّفت 14 قدرة TIER1 (9 مراحل) و36 قدرة TIER2 (مختصر 1/4/6). تصعيد Tier2→Tier1: 8 IDs. نجد **0/50** عند `PRODUCTION-ALIGNED`. **CONCEPTUALLY-UNSOUND=0**. **Batch 05 غير مغلق** — بوابة الإغلاق: CONCEPTUALLY-UNSOUND=0 + RTM صادق. فحص SPLIT-BRAIN: 50 dedicated-only; 0 routing overlap; 0 divergent. IDs 214/245: WF-027/CROSS-SPINE-001 resolved Run 013 — handler batch05_dedicated، spine=batch05_prep. **نوصي بعدم أي إصلاح قبل مراجعة هذا التقرير** — الإغلاق في Run منفصل كما Batch 01/02/03.
