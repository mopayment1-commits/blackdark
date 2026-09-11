# Batch 06 Independent RBAS Due Diligence Report (IDs 251–300)
**Generated:** 2026-09-11T11:39:03.161973+00:00  
**Run:** Master Contract 013 — RBAS-001 risk-based diagnostic audit  
**Auditor role:** Third Line of Defense — Independent Assurance  
**Policies:** RTM-IND-001 | SCORE-IDX-001 | CROSS-SPINE-001 | WF-027 | RBAS-001  

## RBAS-001 Tier Classification (all 50 IDs)

| ID | Capability | Tier | Reason |
|---:|---|---|---|
| 251 | Cross-Domain Decision Intelligence | **TIER1** | Cross-Domain Decision Intelligence — explicit decision output |
| 252 | Liquidation Heatmap | **TIER2** | Liquidation Heatmap — liquidation metric delivery |
| 253 | Liquidation Map / Levels | **TIER2** | Liquidation Map / Levels — liquidation level delivery |
| 254 | Real-Time Liquidation Events | **TIER2** | Real-Time Liquidation Events — event feed delivery |
| 255 | Open Interest Intelligence | **TIER2** | Open Interest Intelligence — metric delivery (duplicate_of=205) |
| 256 | Funding Rate Intelligence | **TIER2** | Funding Rate Intelligence — metric delivery (duplicate_of=86) |
| 257 | Long/Short Ratio Intelligence | **TIER2** | Long/Short Ratio Intelligence — ratio metric delivery (duplicate_of=235) |
| 258 | Top Trader Positioning | **TIER2** | Top Trader Positioning — positioning metric delivery |
| 259 | Futures Basis Intelligence | **TIER2** | Futures Basis Intelligence — basis metric delivery |
| 260 | Futures Volume Intelligence | **TIER2** | Futures Volume Intelligence — volume metric delivery (duplicate_of=126) |
| 261 | Futures CVD / Taker Flow | **TIER2** | Futures CVD / Taker Flow — flow metric delivery |
| 262 | Options Open Interest | **TIER2** | Options Open Interest — options metric delivery |
| 263 | Options Volume | **TIER2** | Options Volume — options volume delivery |
| 264 | Options IV / Skew | **TIER2** | Options IV / Skew — options metric delivery |
| 265 | Max Pain / Gamma Context | **TIER2** | Max Pain / Gamma Context — options context metric delivery |
| 266 | Spot Market Intelligence | **TIER2** | Spot Market Intelligence — market data delivery |
| 267 | Order Book / Market Depth | **TIER2** | Order Book / Market Depth — order book delivery |
| 268 | Historical Derivatives Data | **TIER2** | Historical Derivatives Data — historical data delivery |
| 269 | Exchange Comparison | **TIER2** | Exchange Comparison — comparison delivery |
| 270 | Liquidation Cascade Proximity | **TIER1** | Liquidation Cascade Proximity — proximity score influences trading decisions (default-on-doubt) |
| 271 | Leverage Pressure Score | **TIER1** | Leverage Pressure Score — SCORE-IDX surface |
| 272 | API Data Platform | **TIER2** | API Data Platform — data platform delivery (duplicate_of=103) |
| 273 | Multi-Model Liquidation Comparison | **TIER2** | Multi-Model Liquidation Comparison — comparison tool |
| 274 | Derivatives Alerts | **TIER2** | Derivatives Alerts — alert feed delivery |
| 275 | Cross-Domain Decision Intelligence | **TIER1** | Cross-Domain Decision Intelligence — decision output (catalog duplicate link) |
| 276 | Entity Resolution Engine | **TIER2** | Entity Resolution Engine — entity reference/registry |
| 277 | Address Labeling System | **TIER1** | Address Labeling System — on-chain address labeling (FATF R.16) |
| 278 | Entity Profiles | **TIER2** | Entity Profiles — profile catalog delivery |
| 279 | Transaction Search | **TIER1** | Transaction Search — on-chain transaction intelligence (FATF R.16) |
| 280 | Portfolio Holdings | **TIER2** | Portfolio Holdings — holdings delivery |
| 281 | Balance History | **TIER1** | Balance History — wallet balance history tool (FATF R.16) |
| 282 | Entity PnL | **TIER1** | Entity PnL — financial PnL surface |
| 283 | Exchange Usage Intelligence | **TIER2** | Exchange Usage Intelligence — usage metric delivery |
| 284 | Top Counterparties | **TIER2** | Top Counterparties — counterparty list delivery |
| 285 | Visualizer / Network Graph | **TIER2** | Visualizer / Network Graph — visualization delivery |
| 286 | Automated Trace / Path Finding | **TIER1** | Automated Trace / Path Finding — on-chain trace (FATF R.16) |
| 287 | Cross-Chain Trace | **TIER1** | Cross-Chain Trace — on-chain trace (FATF R.16) |
| 288 | Token Top Holders | **TIER1** | Token Top Holders — holder addresses (FATF R.16) |
| 289 | Token Exchange Flows | **TIER1** | Token Exchange Flows — exchange flow transaction intelligence |
| 290 | Token Transaction Explorer | **TIER1** | Token Transaction Explorer — transaction explorer (FATF R.16) |
| 291 | Custom Dashboards | **TIER2** | Custom Dashboards — dashboard delivery |
| 292 | Custom Alerts | **TIER2** | Custom Alerts — alert delivery |
| 293 | Private Labels | **TIER2** | Private Labels — label management delivery |
| 294 | Archive / Historical Portfolio Snapshot | **TIER2** | Archive / Historical Portfolio Snapshot — archive delivery |
| 295 | AI Market Insights | **TIER1** | AI Market Insights — AI surface (NIST AI RMF full path) |
| 296 | Whale Movement Intelligence | **TIER1** | Whale Movement Intelligence — whale/on-chain movement (FATF R.16) |
| 297 | Fraud / Suspicious Activity Intelligence | **TIER1** | Fraud / Suspicious Activity Intelligence — fraud verdict influences user action |
| 298 | API On-Chain Intelligence | **TIER2** | API On-Chain Intelligence — API delivery surface |
| 299 | Cross-Entity Decision Intelligence | **TIER1** | Cross-Entity Decision Intelligence — explicit decision output |
| 300 | Advanced Multi-Asset Charting | **TIER2** | Advanced Multi-Asset Charting — charting delivery |

**Tier summary:** TIER1=17 | TIER2=33  

## RBAS Impact Metrics

- **Tier1 executed:** 17 IDs — 153 phase checks — 25856 ms
- **Tier2 abbreviated:** 29 IDs — 87 phase checks — 9891 ms
- **Tier2 escalated to Tier1:** 4 IDs — 48 phase checks — 12240 ms
- **CONCEPTUALLY-UNSOUND:** 0/50

## WF-027 / CROSS-SPINE Preflight

- **Routing overlaps (BATCH01∩BATCH02∩BATCH03∩BATCH06):** 0 IDs `[]`
- **WF-027 dormant legacy in batch06 range (251–300):** `[]` (zero overlap — unresolved legacy IDs 584+ are outside range)
- **Cross-spine Run 015:** no WF-027 IDs in scope; batch06_prep spine registered for all 50

## Results Table

| ID | الاسم | RBAS | Path | الحالة النهائية | المرحلة | المعيار المرجعي | SPLIT-BRAIN | الدليل | الخطورة |
|---:|---|---|---|---|---|---|---|---|---|
| 251 | Cross-Domain Decision Intelligence | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=cross_domain_decision_intelligence spine=batch06_prep; code: async def _cap251(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 178 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T11:37:33.9199 | متوسط — |
| 252 | Liquidation Heatmap | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=liquidation_heatmap spine=batch06_prep; code: async def _cap252(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 253 | Liquidation Map / Levels | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=liquidation_map_levels spine=batch06_prep; code: async def _cap253(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 254 | Real-Time Liquidation Events | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=real_time_liquidation_events spine=batch06_prep; code: async def _cap254(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 255 | Open Interest Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=open_interest_intelligence spine=batch06_prep; code: async def _cap255(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 256 | Funding Rate Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=funding_rate_intelligence spine=batch06_prep; code: async def _cap256(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 257 | Long/Short Ratio Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=long_short_ratio_intelligence spine=batch06_prep; code: async def _cap257(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 258 | Top Trader Positioning | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=top_trader_positioning spine=batch06_prep; code: async def _cap258(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 259 | Futures Basis Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=futures_basis_intelligence spine=batch06_prep; code: async def _cap259(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 260 | Futures Volume Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=futures_volume_intelligence spine=batch06_prep; code: async def _cap260(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 261 | Futures CVD / Taker Flow | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=futures_cvd_taker_flow spine=batch06_prep; code: async def _cap261(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 262 | Options Open Interest | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=options_open_interest spine=batch06_prep; code: async def _cap262(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 263 | Options Volume | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=options_volume spine=batch06_prep; code: async def _cap263(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 264 | Options IV / Skew | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=options_iv_skew spine=batch06_prep; code: async def _cap264(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 265 | Max Pain / Gamma Context | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=max_pain_gamma_context spine=batch06_prep; code: async def _cap265(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 266 | Spot Market Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=spot_market_intelligence spine=batch06_prep; code: async def _cap266(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 267 | Order Book / Market Depth | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=order_book_market_depth spine=batch06_prep; code: async def _cap267(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 268 | Historical Derivatives Data | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=historical_derivatives_data spine=batch06_prep; code: async def _cap268(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 269 | Exchange Comparison | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=exchange_comparison spine=batch06_prep; code: async def _cap269(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 270 | Liquidation Cascade Proximity | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=liquidation_cascade_proximity spine=batch06_prep; code: async def _cap270(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 178 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T11:37:33.9199 | متوسط — |
| 271 | Leverage Pressure Score | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=leverage_pressure_score spine=batch06_prep; code: async def _cap271(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 178 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T11:37:33.9199 | متوسط — |
| 272 | API Data Platform | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=api_data_platform spine=batch06_prep; code: async def _cap272(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 273 | Multi-Model Liquidation Comparison | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=multi_model_liquidation_comparison spine=batch06_prep; code: async def _cap273(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 274 | Derivatives Alerts | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=derivatives_alerts spine=batch06_prep; code: async def _cap274(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 275 | Cross-Domain Decision Intelligence | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=cross_domain_decision_intelligence spine=batch06_prep; code: async def _cap275(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 178 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T11:37:33.9199 | متوسط — |
| 276 | Entity Resolution Engine | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=entity_resolution_engine spine=batch06_prep; code: async def _cap276(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 277 | Address Labeling System | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=address_labeling_system spine=batch06_prep; code: async def _cap277(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 278 | Entity Profiles | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=entity_profiles spine=batch06_prep; code: async def _cap278(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 279 | Transaction Search | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=transaction_search spine=batch06_prep; code: async def _cap279(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 280 | Portfolio Holdings | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=portfolio_holdings spine=batch06_prep; code: async def _cap280(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 281 | Balance History | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=balance_history spine=batch06_prep; code: async def _cap281(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 282 | Entity PnL | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=entity_pnl spine=batch06_prep; code: async def _cap282(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 283 | Exchange Usage Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=exchange_usage_intelligence spine=batch06_prep; code: async def _cap283(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 284 | Top Counterparties | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=top_counterparties spine=batch06_prep; code: async def _cap284(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 285 | Visualizer / Network Graph | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=visualizer_network_graph spine=batch06_prep; code: async def _cap285(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 286 | Automated Trace / Path Finding | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=automated_trace_path_finding spine=batch06_prep; code: async def _cap286(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 287 | Cross-Chain Trace | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=cross_chain_trace spine=batch06_prep; code: async def _cap287(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 288 | Token Top Holders | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=token_top_holders spine=batch06_prep; code: async def _cap288(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 289 | Token Exchange Flows | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=token_exchange_flows spine=batch06_prep; code: async def _cap289(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 290 | Token Transaction Explorer | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=token_transaction_explorer spine=batch06_prep; code: async def _cap290(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 291 | Custom Dashboards | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=custom_dashboards spine=batch06_prep; code: async def _cap291(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 292 | Custom Alerts | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=custom_alerts spine=batch06_prep; code: async def _cap292(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 293 | Private Labels | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=private_labels spine=batch06_prep; code: async def _cap293(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 294 | Archive / Historical Portfolio Snapshot | TIER2 | TIER2_ESCALATED_TIER1_FULL | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=archive_historical_portfolio_snapshot spine=batch06_prep; code: async def _cap294(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط ↑T1 |
| 295 | AI Market Insights | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 3 | NIST AI RMF 1.0 + NIST AI 600-1 GenAI Profile | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=ai_market_insights spine=batch06_prep; code: async def _cap295(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; ai_compliance_footer present; ISO 42001 lifecycle not verified | متوسط — |
| 296 | Whale Movement Intelligence | TIER1 | TIER1_FULL_9_PHASE | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=whale_movement_intelligence spine=batch06_prep; code: async def _cap296(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 297 | Fraud / Suspicious Activity Intelligence | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=fraud_suspicious_activity_intelligence spine=batch06_prep; code: async def _cap297(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 178 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T11:37:33.9199 | متوسط — |
| 298 | API On-Chain Intelligence | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=api_on_chain_intelligence spine=batch06_prep; code: async def _cap298(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |
| 299 | Cross-Entity Decision Intelligence | TIER1 | TIER1_FULL_9_PHASE | **PERFORMANCE-UNVERIFIABLE** | 2 | GIPS (CFA Institute) — full-population performance disclosure | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=cross_entity_decision_intelligence spine=batch06_prep; code: async def _cap299(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; PERFORMANCE-UNVERIFIABLE: 178 decisions all SIMULATED/SHADOW (2026-09-11T00:30:49.493941+00:00..2026-09-11T11:37:33.9199 | متوسط — |
| 300 | Advanced Multi-Asset Charting | TIER2 | TIER2_ABBREVIATED_1_4_6 | **NOT_COMPLETE** | 6 | MITRE CWE Top 25 + OWASP API Top 10 + MITRE ATLAS | DEDICATED_ONLY | split_brain=DEDICATED_ONLY; runtime success=True surface=advanced_multi_asset_charting spine=batch06_prep; code: async def _cap300(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:; no user-facing API path — internal/surface-only | متوسط — |

## Summary

- **NOT_COMPLETE:** 44/50
- **PERFORMANCE-UNVERIFIABLE:** 6/50

**Independent result:** 0/50 PRODUCTION-ALIGNED  
**CONCEPTUALLY-UNSOUND:** 0/50  
**GIPS ledger:** 178 decisions, simulated_only=True

### SPLIT-BRAIN Summary (mandatory all 50)

- **DEDICATED_ONLY:** 50

### WF-027 Preflight — Zero Overlap (Run 015)

- **Unresolved WF-027 IDs:** `{584, 629, 630, 631, 642, 644, 646}` — all outside 251–300
- **Resolved prior:** 175 (Batch04), 214/245 (Batch05)


## Critical Code Evidence (SR 26-2)

- *(none flagged in Run 015 static pre-scan — live audit above is authoritative)*

## رأي اللجنة المستقلة

بصفتنا لجنة تدقيق مستقلة (Third Line of Defense — IIA IPPF)، وبعد تنفيذ RBAS-001 على Batch 06 (IDs 251–300) وفق SR 26-2 وCOSO وGIPS وRTM-IND-001 وCROSS-SPINE-001، صُنّفت 17 قدرة TIER1 (9 مراحل) و33 قدرة TIER2 (مختصر 1/4/6). تصعيد Tier2→Tier1: 4 IDs. نجد **0/50** عند `PRODUCTION-ALIGNED`. **CONCEPTUALLY-UNSOUND=0**. **Batch 06 غير مغلق** — بوابة الإغلاق: CONCEPTUALLY-UNSOUND=0 + RTM صادق. فحص SPLIT-BRAIN: 50 dedicated-only; 0 routing overlap; 0 divergent. WF-027 preflight: zero overlap in 251–300. spine=batch06_prep. **نوصي بعدم أي إصلاح قبل مراجعة هذا التقرير** — الإغلاق في Run منفصل كما Batch 01/02/03.
