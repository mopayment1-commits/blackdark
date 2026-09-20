# LAUNCH57 HEAD Inventory Audit (57/57)

- **Generated:** 2026-09-20T01:02:12.825257+00:00
- **HEAD:** `161b60acf467bfa3bf283557e7ab40bf43b3916e`
- **Scope:** CURRENT_APPROVED_BUILD_SCOPE = LAUNCH57 (no PASS, no build)

## Counts

| Status | Count |
|--------|------:|
| WORKS | 4 |
| PARTIAL | 25 |
| MISSING_PATH | 26 |
| BLOCKED_EXTERNAL | 2 |
| **TOTAL** | **57** |

## Top 10 gaps blocking first launch screen

1. 1 Command Home بطيء (~3s command-home) ومركّب وليس شاشة أولى مستقلة
2. 2 Single-Sentence Oracle غير معزول عن command-home composite
3. 1 Command Home latency (~3s) still blocks first-screen paint SLA
4. 49 Personal decision history API بلا fetch في dashboard
5. 43 Spot–perp arbitrage launch57 API بلا wire؛ dashboard يستخدم /api/arbitrage legacy
6. 14/18 Whale surfaces تستخدم /api/whale و/alerts/inbox وليس launch57 smart_money
7. 36 AI copilot launch57 API بلا wire؛ dashboard chat = /api/chat
8. 51 Research portal launch57 بلا route؛ digest = /api/reports/daily
9. 7–12 Decision batch (regime/mode/signals) handlers بلا consumer path
10. 33 Smart Alerts Telegram BLOCKED_EXTERNAL؛ inbox محلي فقط

## Full register (57 rows)

| # | Name | cap_id | consumer_path | works_now | goal_met | test | hero | notes |
|---:|---|---|---|---|---|---|---|---|
| 1 | Six Heroes Command Home — «ماذا أفعل الآن؟» | UNMAPPED | /dashboard#trust-pulse → GET /api/launch57/command-home (launch_item_id=1 only) | PARTIAL | جزئي | نعم `tests/launch57/test_trust_pulse_launch57_consumer_path.py::test_trust_pulse_only_loads_launch57_command_home` | Single-Sentence Oracle | Trust Pulse يستهلك command-home فقط؛ PENDING_VERIFICATION |
| 2 | Single-Sentence Oracle (ACT/WAIT/ABSTAIN) | UNMAPPED | /dashboard#trust-pulse → command-home.oracle (launch_item_id=2) | PARTIAL | جزئي | نعم `tests/launch57/test_trust_pulse_launch57_consumer_path.py::test_command_home_with_oracle_exposes_act_wait_sentence` | Single-Sentence Oracle | ACT/WAIT/ABSTAIN + Why من oracle #2؛ PENDING_VERIFICATION |
| 3 | Decision Certificate + hash | CAP-0641 | command-home composite → launch57/trust_batch1:decision_certificate | PARTIAL | جزئي | نعم `tests/launch57/test_trust_batch1.py::test_decision_certificate_includes_hash` | NONE | شهادة في handler؛ لا زر مشاركة OG مستقل |
| 4 | Public Accuracy Ledger (حي فقط) | CAP-0640 | GET /oracle-accuracy (legacy oracle_track_record backend) | PARTIAL | جزئي | نعم `tests/launch57/test_trust_batch1.py::test_public_accuracy_ledger_live_only_primary` | Public Accuracy Ledger | صفحة /oracle-accuracy حية؛ backend legacy وليس launch57/trust_batch1 مباشرة |
| 5 | Net-Edge / Cost Autopsy على كل فرصة أو إشارة | CAP-0639,CAP-0635 | GET /api/launch57/net-edge (elite tier, auth) | PARTIAL | جزئي | نعم `tests/launch57/test_trust_batch1.py::test_net_edge_scores_real_opportunity` | NONE | Net-edge API موجود؛ elite tier وليس على كل إشارة افتراضياً |
| 6 | Evidence class ظاهر (LIVE / DELAYED / SIM) | UNMAPPED | /dashboard#trust-pulse → evidence_class in command-home payload | WORKS | نعم | نعم `tests/launch57/test_trust_batch1.py::test_user_evidence_display_maps_live_delayed_sim` | NONE | LIVE/DELAYED/SIM على trust-pulse + اختبار display |
| 7 | Market Regime / Compass | CAP-0035 | UNMAPPED | MISSING_PATH | لا | نعم `tests/launch57/test_decision_batch1.py::test_market_regime_live_path` | Whale Signal vs Noise | Handler+اختبار batch فقط؛ لا API ولا dashboard wire |
| 8 | Beginner Decision Mode | CAP-0034 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_decision_batch1.py` | Single-Sentence Oracle | uxMode في dashboard legacy؛ launch57 beginner_mode غير مستدعى |
| 9 | Cross-Signal Confirmation | CAP-0031 | UNMAPPED | MISSING_PATH | لا | نعم `tests/launch57/test_decision_batch1.py::test_cross_signal_confirmation_uses_spine_price` | Single-Sentence Oracle | cross_signal_confirmation غير موصول بمسار مستهلك |
| 10 | Contradiction Detection | CAP-0032 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_decision_batch1.py` | Whale Signal vs Noise | contradiction_detection غير موصول بمسار مستهلك |
| 11 | Smart Money Actionability Score | CAP-0033 | UNMAPPED | MISSING_PATH | لا | نعم `tests/launch57/test_decision_batch1.py::test_actionability_blocks_cost_claim_without_net_edge` | Stealth Advisor | actionability score غير موصول بمسار مستهلك |
| 12 | Smart Money Conviction Engine | CAP-0028 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_decision_batch2.py` | Whale Signal vs Noise | conviction engine غير موصول بمسار مستهلك |
| 13 | Accumulation / Distribution Detection | CAP-0005 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_smart_money_batch1.py` | Whale Signal vs Noise | accumulation/distribution غير موصول بمسار مستهلك |
| 14 | Smart Money Token Screener | CAP-0006 | UNMAPPED | MISSING_PATH | لا | نعم `tests/launch57/test_smart_money_batch1.py::test_token_screener_live` | Whale Signal vs Noise | smart-money screener غير موصول؛ dashboard يستخدم /api/whale/* |
| 15 | Entity-Aware Wallet Intelligence | CAP-0014 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_smart_money_batch2.py` | Whale Signal vs Noise | entity wallet intel غير موصول بمسار مستهلك |
| 16 | Exchange Flow Intelligence (in/out/net) | CAP-0015 | UNMAPPED | MISSING_PATH | لا | نعم `tests/launch57/test_smart_money_batch1.py::test_exchange_flow_live_path` | Whale Signal vs Noise | exchange flow غير موصول؛ لا API launch57 |
| 17 | Exchange Whale Ratio + internal-flow filter | CAP-0072 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_smart_money_batch1.py` | Whale Signal vs Noise | whale ratio filter غير موصول بمسار مستهلك |
| 18 | Whale Accumulation / Movement Alerts | CAP-0081 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_smart_money_batch2.py` | Whale Signal vs Noise | whale alerts غير موصول؛ inbox يستخدم /api/alerts/inbox |
| 19 | Inter-Entity Flow (محدود الإطلاق) | CAP-0091 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_smart_money_batch2.py` | Arbitrage Scanner | inter-entity flow غير موصول بمسار مستهلك |
| 20 | Address Labels & Cohorts (نواة محدودة) | CAP-0092 | UNMAPPED | MISSING_PATH | لا | نعم `tests/launch57/test_smart_money_batch1.py::test_address_labels_blocks_stale` | Whale Signal vs Noise | address labels غير موصول بمسار مستهلك |
| 21 | Spot metrics suite (صادق التحديث) | CAP-0047 | launch57/data_batch1:spot_metrics_suite (cap646/spine only) | PARTIAL | جزئي | نعم `tests/launch57/test_data_batch1.py::test_spot_metrics_unknown_not_zero` | Single-Sentence Oracle | spot metrics handler موجود؛ لا سطح UI/API مخصص |
| 22 | Real-time / near-real-time prices | CAP-0561 | GET /api/launch57/real-time-prices (+ landing fetch) | WORKS | نعم | نعم `tests/launch57/test_data_batch1.py::test_real_time_prices_live_path` | NONE | Landing+dashboard يستدعيان /api/launch57/real-time-prices |
| 23 | OHLCV | CAP-0507 | launch57/data_batch1:ohlcv (no dedicated UI route) | PARTIAL | جزئي | نعم `tests/launch57/test_data_batch1.py::test_ohlcv_full_bars_and_invariants` | B2B Feed | OHLCV handler؛ chart يستخدم /api/market/klines legacy |
| 24 | Quote + symbol metadata | CAP-0506 | launch57/data_batch1:quote+metadata (spine only) | PARTIAL | جزئي | نعم `tests/launch57/test_data_batch1.py::test_quote_and_metadata_distinct_contracts` | Arbitrage Scanner | quote/metadata داخل spine فقط |
| 25 | Futures OI intelligence | CAP-0085 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_derivatives_batch1.py` | Arbitrage Scanner | futures OI handler؛ dashboard يستخدم /api/market/open-interest |
| 26 | Funding rate intelligence | CAP-0086 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_derivatives_batch1.py` | Arbitrage Scanner | funding handler غير موصول |
| 27 | Liquidation intelligence / heatmap خفيف | CAP-0088 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_derivatives_batch1.py` | Arbitrage Scanner | liquidation handler غير موصول |
| 28 | Taker buy/sell + leverage ratio | CAP-0089 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_derivatives_batch1.py` | Arbitrage Scanner | taker/leverage handler غير موصول |
| 29 | Derivatives sentiment composite | CAP-0090 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_derivatives_batch1.py` | B2B Feed | derivatives composite handler غير موصول |
| 30 | Order book intelligence (L1 على الأقل) | CAP-0050 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_derivatives_batch2.py` | B2B Feed | order book handler غير موصول |
| 31 | Token screener (سوق عام) | CAP-0056 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_derivatives_batch2.py` | Public Accuracy Ledger | market screener handler غير موصول |
| 32 | Watchlists (توكن + محفظة محدودة) | CAP-0019 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_derivatives_batch2.py` | Whale Signal vs Noise | watchlists handler غير موصول |
| 33 | Smart Alerts (سعر + تدفق + حوت + قرار) | CAP-0017 | UNMAPPED | BLOCKED_EXTERNAL | لا | جزئي `tests/launch57/test_derivatives_batch2.py` | Stealth Advisor | Telegram push محجوب خارجياً؛ inbox محلي legacy فقط |
| 34 | Signal → Explanation workflow | CAP-0025 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_explanation_ai_batch1.py` | NONE | signal→explanation handler غير موصول |
| 35 | Price-move explanation | CAP-0026 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_explanation_ai_batch1.py` | NONE | price-move explanation handler غير موصول |
| 36 | AI Research Agent + Copilot مربوط ببيانات المنصة فقط (شات على أسطح الإطلاق + footer امتثال) | CAP-0024 | GET /api/launch57/ai-copilot | PARTIAL | جزئي | جزئي `tests/launch57/test_explanation_ai_batch1.py` | Stealth Advisor | API ai-copilot موجود؛ dashboard chat يستخدم /api/chat legacy |
| 37 | Cross-market decision engine | CAP-0029 | GET /api/launch57/cross-market | PARTIAL | جزئي | جزئي `tests/launch57/test_decision_batch2.py` | Whale Signal vs Noise | API cross-market موجود؛ غير ظاهر في dashboard الافتراضي |
| 38 | MVRV / Z-Score (نواة BTC/ETH إن توفّر مصدر) | CAP-0040 | launch57/edge_ui_batch1:mvrv (no HTTP route; vendor blocker) | BLOCKED_EXTERNAL | لا | نعم `tests/launch57/test_edge_ui_batch1.py::test_mvrv_source_blocker_visible` | Arbitrage Scanner | MVRV محجوب بمصدر مرخص؛ لا route /api/launch57/mvrv-suite |
| 39 | Point-in-time immutable metrics | CAP-0061 | launch57/data_batch2:pit_immutable_metrics (internal) | PARTIAL | جزئي | نعم `tests/launch57/test_data_batch2.py::test_pit_immutable_metrics_hash_and_timestamp` | Public Accuracy Ledger | PIT metrics داخلية؛ لا سطح مستهلك |
| 40 | Data quality & provenance (ظاهر للمستخدم) | CAP-0063 | launch57/data_batch2:provenance (embedded in data responses) | PARTIAL | جزئي | نعم `tests/launch57/test_data_batch2.py::test_provenance_layer_user_disclosure` | Public Accuracy Ledger | provenance في payload؛ غير معروض صراحة للمستخدم |
| 41 | Freshness assurance + تسمية delayed صريحة | CAP-0630 | load_decision_spine → freshness_update_assurance + trust-pulse labels | WORKS | نعم | نعم `tests/launch57/test_data_batch2.py::test_freshness_rejects_stale_as_live` | B2B Feed | freshness gate في spine + trust-pulse stale labels |
| 42 | Unified exchange connector (مسار واحد) | CAP-0504 | launch57/data_batch1:unified_exchange_connector (no /status wire) | PARTIAL | جزئي | نعم `tests/launch57/test_data_batch1.py::test_unified_exchange_connector_routes_without_synthetic` | Arbitrage Scanner | connector handler؛ /status لا يعرض unified connector |
| 43 | Spot–perp / arbitrage (Net-Edge إلزامي) | CAP-0230 | GET /api/launch57/spot-perp-arbitrage | PARTIAL | جزئي | نعم `tests/launch57/test_edge_ui_batch1.py::test_spot_perp_scan_without_cost_claim` | Arbitrage Scanner | API spot-perp موجود؛ dashboard arb يستخدم /api/arbitrage/* |
| 44 | Shareable decision / oracle card (OG) | UNMAPPED | GET /api/launch57/share-proof → dashboard Share Proof (hidden unless success) | PARTIAL | جزئي | نعم `tests/launch57/test_trust_pulse_launch57_consumer_path.py::test_share_proof_route_launch_44` | Single-Sentence Oracle | Share Proof → #44 أو مخفي؛ PENDING_VERIFICATION |
| 45 | Shareable accuracy / outcome page | CAP-0640 | /oracle-accuracy share samples (trust_batch2 handler) | PARTIAL | جزئي | نعم `tests/launch57/test_trust_batch2.py::test_shareable_accuracy_page_live_only` | Public Accuracy Ledger | shareable accuracy handler؛ /oracle-accuracy legacy |
| 46 | Guest trust surface | UNMAPPED | GET /api/launch57/guest-trust (+ / landing, /status) | WORKS | نعم | نعم `tests/launch57/test_trust_batch2.py::test_guest_trust_surface` | Public Accuracy Ledger | guest-trust API على / و/status |
| 47 | One-click risk disclosure على كل قرار | UNMAPPED | command-home/trust-pulse → one_click_risk_disclosure fields | PARTIAL | جزئي | نعم `tests/launch57/test_trust_batch2.py::test_one_click_risk_disclosure` | NONE | حقول risk disclosure داخل command-home payload |
| 48 | Abstain / reject reasons ظاهرة | UNMAPPED | command-home abstain → reject reasons in payload | PARTIAL | جزئي | نعم `tests/launch57/test_trust_batch2.py::test_abstain_reject_reasons_first_class` | NONE | abstain reasons داخل command-home عند ABSTAIN |
| 49 | Personal decision history (محدود Free) | UNMAPPED | GET /api/launch57/decision-history (no dashboard fetch) | PARTIAL | جزئي | نعم `tests/launch57/test_edge_ui_batch1.py::test_personal_decision_history_free_limit` | NONE | API decision-history؛ لا fetch في dashboard.html |
| 50 | Discipline / missed-opportunity mirror (خفيف) | UNMAPPED | GET /api/launch57/discipline-mirror (+ /discipline-mirror link) | PARTIAL | جزئي | نعم `tests/launch57/test_edge_ui_batch1.py::test_discipline_mirror_light` | NONE | API discipline-mirror؛ رابط فقط بدون استدعاء API |
| 51 | Research portal / short briefs | CAP-0065 | UNMAPPED | MISSING_PATH | لا | نعم `tests/launch57/test_explanation_ai_batch1.py::test_research_portal_short_brief` | Public Accuracy Ledger | research_intelligence_portal handler؛ dashboard يستخدم /api/reports/daily |
| 52 | Capability library (بحث) — طبقة ثانية لا الرئيسية | UNMAPPED | GET /api/launch57/capability-library | PARTIAL | جزئي | نعم `tests/launch57/test_capability_library.py` | NONE | API capability-library ثانوي |
| 53 | Instant Wallet Due Diligence | CAP-0022 | GET /api/launch57/wallet-due-diligence | PARTIAL | جزئي | جزئي `tests/launch57/test_smart_money_batch2.py` | Public Accuracy Ledger | API wallet DD موجود؛ غير في dashboard الافتراضي |
| 54 | Instant Token Due Diligence | CAP-0023 | GET /api/launch57/token-due-diligence | PARTIAL | جزئي | جزئي `tests/launch57/test_smart_money_batch2.py` | Public Accuracy Ledger | API token DD موجود؛ غير في dashboard الافتراضي |
| 55 | Pump & Dump / manipulation pattern alerts | CAP-0238 | UNMAPPED | MISSING_PATH | لا | جزئي `tests/launch57/test_smart_money_batch3.py` | Whale Signal vs Noise | pump/dump handler غير موصول بمسار مستهلك |
| 56 | Suspicious activity flags (على مسارات توكن/سمارت موني — ليس AML كامل) | CAP-0297 | GET /api/launch57/suspicious-flags | PARTIAL | جزئي | جزئي `tests/launch57/test_smart_money_batch3.py` | Whale Signal vs Noise | API suspicious-flags موجود؛ غير في dashboard |
| 57 | Exchange transparency / risk indicators (احتياطي معلن إن وُجد، شذوذ تدفق، حوادث — بدون شهادة ملاءة أو ضمان) | CAP-0916 | GET /api/launch57/exchange-transparency | PARTIAL | جزئي | جزئي `tests/launch57/test_smart_money_batch3.py` | NONE | API exchange-transparency موجود؛ غير في dashboard |
