# SPLIT_BRAIN categories B/C/D — live audit (58 capabilities)

**Generated:** 2026-08-31T07:56:26.982473+00:00

| Category | Population | Sample | Audit fn in prod % | Dedicated exec % | Outcomes |
|----------|----------:|-------:|-------------------:|-----------------:|----------|
| `SPLIT_BRAIN_REUSED` | 45 | 10 | 0.0% | 80.0% | PARTIAL:6, WRONG:4 |
| `SPLIT_BRAIN_OTHER` | 10 | 10 | 0.0% | 70.0% | PARTIAL:6, WRONG:4 |
| `SPLIT_BRAIN_GENERIC_HANDLER` | 3 | 3 | 0.0% | 33.3% | PARTIAL:1, WRONG:2 |

## Sample panels

### SPLIT_BRAIN_REUSED (n=10)

| ID | Catalog | Audit path | Production path | Audit in prod? | Verdict |
|----|---------|------------|-----------------|----------------|---------|
| 28 | Smart Money Conviction Engine | `bd_platform.retail_intelligence_layer.evaluate_contextual_alert_65` | `whale_tracker.get_latest_whale_alerts` | NO | WRONG |
| 45 | ETF Flow Intelligence | `bd_platform.free_tier_capabilities.smart_money_leaderboard` | `market_context.probe_price_sources` | NO | PARTIAL |
| 56 | Token Screener | `bd_platform.market_analysis_layer.attach_market_health_bundle_106_112_114` | `oracle_track_record.public_track_record` | NO | PARTIAL |
| 62 | Institutional Backtesting Data Layer | `bd_platform.institutional_b2b_layer.build_ic_report_87` | `ml.market_replay_bootstrap.bootstrap_market_replay_dataset` | NO | PARTIAL |
| 279 | Transaction Search | `bd_platform.pro_trader_layer.build_share_card_68` | `onchain_tracker.build_onchain_context_safe` | NO | PARTIAL |
| 441 | Oracle Risk | `bd_platform.intelligence_analysis_layer.stat_arb_insight_155` | `trust_pulse.build_trust_pulse` | NO | WRONG |
| 458 | Risk-to-Decision Intelligence | `bd_platform.whales_institutional_layer.build_methodology_docs_86` | `trust_pulse.build_trust_pulse` | NO | PARTIAL |
| 578 | Unified_Portfolio_Dashboard | `bd_platform.execution_rejected_layer.whale_behavior_analysis_216` | `bd_platform.portfolio_rebalancer.portfolio_snapshot` | NO | WRONG |
| 584 | Risk_Management_Shield | `bd_platform.news_classifier.coindesk_feed` | `risk_manager.risk_status` | NO | WRONG |
| 638 | Claims/Prediction Verification Engine | `bd_platform.security_trust_data_layer.build_contradiction_replay_254` | `oracle_track_record.public_track_record` | NO | PARTIAL |

### SPLIT_BRAIN_OTHER (n=10)

| ID | Catalog | Audit path | Production path | Audit in prod? | Verdict |
|----|---------|------------|-----------------|----------------|---------|
| 1 | Smart Money Leaderboard | `bd_platform.footprint_analytics.footprint_snapshot` | `whale_tracker.get_latest_whale_alerts` | NO | PARTIAL |
| 10 | Wallet PnL Analysis | `instant_alert_engine.engine_stats` | `bd_platform.onchain_hub.debank_wallet` | NO | PARTIAL |
| 11 | Wallet Historical Performance & Win Rate | `arbitrage_service.scan_arbitrage_opportunities` | `bd_platform.onchain_hub.debank_wallet` | NO | WRONG |
| 14 | Entity-Aware Wallet Intelligence | `market_context.whale_alert_message` | `bd_platform.onchain_hub.debank_wallet` | NO | PARTIAL |
| 17 | Smart Alerts | `alert_service.subscribe_alerts` | `instant_alert_engine.engine_stats` | NO | PARTIAL |
| 36 | On-Chain Metrics Library | `risk_manager.is_trading_frozen` | `onchain_tracker.build_onchain_context_safe` | NO | WRONG |
| 55 | NVT Fair-Value Model | `due_diligence_bundle.build_full_due_diligence_bundle` | `onchain_tracker.build_onchain_context_safe` | NO | WRONG |
| 330 | Reference Rates | `trade_simulator.simulate_spot_trade` | `market_context.probe_price_sources` | NO | PARTIAL |
| 382 | dbt Connector | `heroes_quality.heroes_quality_manifest` | `blackdark.canonical.layer.get_canonical_layer` | NO | WRONG |
| 629 | Real-Time Wallet Alerts | `regulatory_compliance_guard.compliant_oracle_sentence` | `instant_alert_engine.engine_stats` | NO | PARTIAL |

### SPLIT_BRAIN_GENERIC_HANDLER (n=3)

| ID | Catalog | Audit path | Production path | Audit in prod? | Verdict |
|----|---------|------------|-----------------|----------------|---------|
| 25 | Signal → Explanation Workflow | `bd_platform.footprint_analytics.footprint_snapshot` | `trust_pulse.build_trust_pulse` | NO | WRONG |
| 46 | Digital Asset Treasury Company Intellige | `bd_platform.slippage_tolerance_optimizer.optimize_slippage_tolerance` | `market_context.probe_price_sources` | NO | WRONG |
| 299 | Cross-Entity Decision Intelligence | `bd_platform.news_classifier.classify_headlines` | `trust_pulse.build_trust_pulse` | NO | PARTIAL |

