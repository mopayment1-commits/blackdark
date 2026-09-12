# BLACKDARK — Operations Runbook (RC2)

> Constitution: `docs/PRODUCT_CONSTITUTION_AR.md`  
> Handover: `docs/ops/BUYER_HANDOVER_PACK.md`  
> Findings closed here: `F-OPS-01`, portions of `F-XFER-01`

## Finalize (code → Railway)
```bash
python scripts/finalize_launch.py
python scripts/verify_constitution_live.py
# → writes .env.launch.local (gitignored) + data/finalize_launch.json
# Paste secrets into Railway Variables, then set DATABASE_URL
# After announce: python scripts/mark_golive.py --url https://YOUR-DOMAIN
# Full pack: docs/GO_LIVE_AR.md
```

## Pre-flight
1. `GET /api/production/guard` → `required_pass: true`
2. `GET /api/launch/readiness` → `code_launch_ready` + constitution modules
3. `GET /api/admin/launch-checklist` (admin) → review blocked items
4. `GET /api/oracle/accuracy/public` → proof_chain.verify ok
5. `GET /oracle/BTC?ux_mode=beginner&lang=en` → must include `decision_sentence`, `persona_clarity`
6. `GET /oracle/BTC?ux_mode=pro&lang=en` → must include `net_edge_truth`, `opportunity_half_life`, `signal_registry`
7. Confirm `CSP_NONCE_MODE` is ON (`docs/ops/CSP_PRODUCTION_ATTESTATION.md`)
8. Confirm `CORS_ALLOWED_ORIGINS` reviewed (`docs/ops/CORS_ALLOWLIST_REVIEW.md`)

## Required production env
See `docs/ops/ENV_VAR_REGISTRY.md` and `docs/ENV_CONFIG_MATRIX.md`.

Minimum:
- `SECRETS_MASTER_KEY` or `SECRETS_VAULT_KEY`
- `SESSION_TOKEN_PEPPER`
- `ADMIN_API_KEY` / `ADMIN_API_KEY_FILE` + `ADMIN_EMAILS`
- `APP_BASE_URL=https://...`
- Billing: Lemon **or** Stripe (+ webhook)
- Optional Telegram via `TELEGRAM_SECRETS_FILE` (0600), not cleartext `.env` token

## Deploy
| Mode | Command / path |
|------|----------------|
| Local Soft Launch | `bootstrap_free_human_ops.py` + uvicorn |
| Docker web | `docker compose up --build` |
| Optional Vault -dev | `docker compose --profile vault-dev up` (**not** prod secrets) |
| HA rehearsal | Postgres+Redis; `WEB_CONCURRENCY`/`WEB_REPLICAS` ≥2; Soft Launch unset |
| k8s | `deploy/k8s/` |

## Critical routes
| Route | Access | Purpose |
|-------|--------|---------|
| `/oracle/{symbol}` | quota | Primary Oracle (`oracle_unified`) + enrichment |
| `/oracle-accuracy` | public | Proof-native accuracy page |
| `/api/oracle/accuracy/public` | public | Hit-rate JSON + proof_chain |
| `/api/due-diligence/evidence-pack` | whale/admin | Full M&A pack |
| `/api/due-diligence/evidence-pack/public-summary` | public | Redacted teaser |
| `/api/production/guard` | ops | Fail-closed readiness |
| `/health/live` · `/health/ready` | public | Probes |
| `/metrics` | ops | Process metrics |

## Fail-closed behavior
- Contradiction veto / Net-Edge reject / Half-life expired → no execution
- Unknown trading/withdrawal fee → no executable opportunity (`fee_matrix` → `None`)
- Unknown/stale gas or native/USD mid → no executable DeFi P&L (`gas_oracle` → `None`)
- Unknown bridge protocol fee → `executable=false` (no invented flat bridge fee)
- Directional oracle soft-pass → labeled `ADVISORY_NOT_EXECUTABLE`
- Drift / OOD → rules fallback or withhold ML
- Missing production secrets → guard fails
- `CSP_NONCE_MODE=false` is break-glass only

## Incident response
Follow `docs/ops/INCIDENT_RESPONSE.md`.

## Backup / restore
Follow `docs/ops/BACKUP_RESTORE.md`. Live buyer drill evidence remains EXTERNAL (`F-EXT-03`).

## Secret rotation
Follow `docs/ops/SECRET_ROTATION.md`.

## Rollback
1. Redeploy previous Railway/Docker/k8s image (known-good SHA)
2. Keep DB intact (labeled corpus is the moat)
3. Freeze trading via panic if needed (`execution_engine.trigger_panic`)
4. Verify `/api/production/guard` and sample `/oracle/BTC`

## Post-launch 24h
- Watch `/health/ready`, billing webhooks, Telegram alerts
- Confirm live samples accumulating (flywheel)
- Do **not** claim HFT, guaranteed profit, or unproven 1k/10k user capacity
- Capacity claims must cite MEASURED rows in `docs/LOAD_TEST_RUN_LOG.md`

## Batch 01 capability ops (IDs 1–25) — Build 826 Run 021

Each capability has rollback via cap646 spine revert + batch01 pytest regression.

| ID | Runbook tag | Rollback |
|---:|---|---|
| 1 | cap-001 smart_money_leaderboard | revert `cap646/batch01_dedicated.py` + `pytest tests/cap646/test_capability_build_batch01.py` |
| 2 | cap-002 wallet_profiler | same |
| 3 | cap-003 wallet_profiler_for_token | same |
| 4 | cap-004 smart_money_tracking | same |
| 5 | cap-005 smart_money_accumulation_detection | same |
| 6 | cap-006 smart_money_token_screener | same |
| 7 | cap-007 holder_distribution_intelligence | same |
| 8 | cap-008 top_holders_concentration_analysis | same |
| 9 | cap-009 distribution_score | same |
| 10 | cap-010 wallet_pnl_analysis | same |
| 11 | cap-011 wallet_historical_performance_win_rate | same |
| 12 | cap-012 wallet_entry_exit_analysis | same |
| 13 | cap-013 wallet_counterparty_relationship_analysis | same |
| 14 | cap-014 entity_aware_wallet_intelligence | same |
| 15 | cap-015 exchange_flow_intelligence | same |
| 16 | cap-016 candle_price_move_investigator | same |
| 17 | cap-017 smart_alerts | same + verify `/api/cap646/17/execute` |
| 18 | cap-018 custom_wallet_labels | same |
| 19 | cap-019 wallet_token_watchlists | same |
| 20 | cap-020 multi_chain_portfolio_intelligence | same |
| 21 | cap-021 transaction_decoder | same |
| 22 | cap-022 instant_wallet_due_diligence | same |
| 23 | cap-023 instant_token_due_diligence | same |
| 24 | cap-024 ai_research_agent_grounded | same |
| 25 | cap-025 signal_explanation_workflow | same |

Consumer path: `POST /api/cap646/{id}/execute` via Six Heroes → cap646 institutional gateway.

### Build batch 02 (IDs 26–50)

| ID | Runbook tag | Rollback |
|---:|---|---|
| 26 | cap-026 price_move_explanation | batch01 pytest + batch02 pytest |
| 27 | cap-027 smart_money_historical_trend | same |
| 28 | cap-028 smart_money_conviction | same |
| 29 | cap-029 cross_market_decision | same |
| 30 | cap-030 evidence_confidence | same |
| 31 | cap-031 cross_signal_confirmation | same |
| 32 | cap-032 contradiction_detection | same |
| 33 | cap-033 actionability_score | same |
| 34 | cap-034 beginner_decision_mode | same |
| 35 | cap-035 market_compass_regime | same |
| 36 | cap-036 on_chain_metrics_library | same |
| 37 | cap-037 entity_adjusted_metrics | same |
| 38 | cap-038 cost_basis_distribution | same |
| 39 | cap-039 realized_cap_realized_price | same |
| 40 | cap-040 mvrv_suite | same |
| 41 | cap-041 sopr_profitability | same |
| 42 | cap-042 holder_cohort_intelligence | same |
| 43 | cap-043 supply_dynamics_intelligence | same |
| 44 | cap-044 exchange_balance_netflow | same |
| 45 | cap-045 etf_flow_intelligence | same |
| 46 | cap-046 treasury_company | same |
| 47 | cap-047 spot_market_metrics | same |
| 48 | cap-048 futures_intelligence | same |
| 49 | cap-049 options_intelligence | same |
| 50 | cap-050 order_book_intelligence | same |

### Build batch 03 (IDs 51–75)

| ID | Runbook tag | Rollback |
|---:|---|---|
| 51 | cap-051 macro_traditional_finance_integration | batch01–03 pytest |
| 52 | cap-052 cross_asset_return_breadth | batch01–03 pytest |
| 53 | cap-053 btc_to_macro_coupling | batch01–03 pytest |
| 54 | cap-054 global_liquidity_intelligence | batch01–03 pytest |
| 55 | cap-055 nvt_fair_value_model | batch01–03 pytest |
| 56 | cap-056 token_screener | batch01–03 pytest |
| 57 | cap-057 profitability_map | batch01–03 pytest |
| 58 | cap-058 custom_no_code_charting_workbench | batch01–03 pytest |
| 59 | cap-059 personalized_research_dashboards | batch01–03 pytest |
| 60 | cap-060 metric_based_smart_alerts | batch01–03 pytest |
| 61 | cap-061 point_in_time_immutable_metrics | batch01–03 pytest |
| 62 | cap-062 institutional_backtesting_data_layer | batch01–03 pytest |
| 63 | cap-063 data_quality_provenance_layer | batch01–03 pytest |
| 64 | cap-064 metric_methodology_registry | batch01–03 pytest |
| 65 | cap-065 research_intelligence_portal | batch01–03 pytest |
| 66 | cap-066 market_regime_written_read | batch01–03 pytest |
| 67 | cap-067 api_cli_excel_mcp_data_access | batch01–03 pytest |
| 68 | cap-068 bulk_data_institutional_delivery | batch01–03 pytest |
| 69 | cap-069 cross_domain_decision_intelligence_layer | batch01–03 pytest |
| 70 | cap-070 exchange_reserve_intelligence | batch01–03 pytest |
| 71 | cap-071 exchange_inflow_outflow_netflow | batch01–03 pytest |
| 72 | cap-072 exchange_whale_ratio | batch01–03 pytest |
| 73 | cap-073 exchange_address_transaction_activity | batch01–03 pytest |
| 74 | cap-074 exchange_to_exchange_flow_intelligence | batch01–03 pytest |
| 75 | cap-075 exchange_internal_flow_filter | batch01–03 pytest |

### Build batch 04 (IDs 76–100)

| ID | Runbook tag | Rollback |
|---:|---|---|
| 76 | cap-076 stablecoin_exchange_reserve | batch01–04 pytest |
| 77 | cap-077 stablecoin_exchange_flow_intelligence | batch01–04 pytest |
| 78 | cap-078 stablecoin_supply_ratio_intelligence | batch01–04 pytest |
| 79 | cap-079 miner_flow_intelligence | batch01–04 pytest |
| 80 | cap-080 miners_position_index_mpi | batch01–04 pytest |
| 81 | cap-081 whale_accumulation_distribution_intelligence | batch01–04 pytest |
| 82 | cap-082 coinbase_premium_intelligence | batch01–04 pytest |
| 83 | cap-083 korea_premium_intelligence | batch01–04 pytest |
| 84 | cap-084 fund_etf_data_intelligence | batch01–04 pytest |
| 85 | cap-085 futures_open_interest_intelligence | batch01–04 pytest |
| 86 | cap-086 funding_rate_intelligence | batch01–04 pytest |
| 87 | cap-087 estimated_leverage_ratio | batch01–04 pytest |
| 88 | cap-088 liquidation_intelligence | batch01–04 pytest |
| 89 | cap-089 taker_buy_sell_pressure | batch01–04 pytest |
| 90 | cap-090 derivatives_market_sentiment_composite | batch01–04 pytest |
| 91 | cap-091 inter_entity_flow_intelligence | batch01–04 pytest |
| 92 | cap-092 address_labels_cohorts | batch01–04 pytest |
| 93 | cap-093 custom_no_code_analytics_web3 | batch01–04 pytest |
| 94 | cap-094 native_sql_advanced_query_workspace | batch01–04 pytest |
| 95 | cap-095 pro_chart_multi_metric_workbench | batch01–04 pytest |
| 96 | cap-096 personal_dashboards | batch01–04 pytest |
| 97 | cap-097 custom_metric_alerts | batch01–04 pytest |
| 98 | cap-098 whale_movement_alerts | batch01–04 pytest |
| 99 | cap-099 quicktake_analyst_insight_feed | batch01–04 pytest |
| 100 | cap-100 research_reports | batch01–04 pytest |

### Build batches 05–06 (IDs 101–150)

| ID | Runbook tag | Rollback |
|---:|---|---|
| 101 | cap-101 ai_data_analyst_ask_ai | batch01–06 pytest |
| 102 | cap-102 ai_generated_reporting | batch01–06 pytest |
| 103 | cap-103 api_data_platform | batch01–06 pytest |
| 104 | cap-104 high_resolution_block_level_data_delivery | batch01–06 pytest |
| 105 | cap-105 historical_full_data_layer | batch01–06 pytest |
| 106 | cap-106 data_quality_provenance_layer | batch01–06 pytest |
| 107 | cap-107 metric_methodology_registry | batch01–06 pytest |
| 108 | cap-108 institutional_data_api_delivery | batch01–06 pytest |
| 109 | cap-109 white_label_research_reporting | batch01–06 pytest |
| 110 | cap-110 cross_domain_decision_intelligence_layer | batch01–06 pytest |
| 111 | cap-111 exchange_flow_actionability_score | batch01–06 pytest |
| 112 | cap-112 flow_to_price_explanation_engine | batch01–06 pytest |
| 113 | cap-113 asset_intelligence_profiles | batch01–06 pytest |
| 114 | cap-114 asset_classification_taxonomy | batch01–06 pytest |
| 115 | cap-115 asset_screener | batch01–06 pytest |
| 116 | cap-116 market_pair_intelligence | batch01–06 pytest |
| 117 | cap-117 real_volume_quality_adjusted_volume | batch01–06 pytest |
| 118 | cap-118 vwap_price_intelligence | batch01–06 pytest |
| 119 | cap-119 market_cap_fdv_intelligence | batch01–06 pytest |
| 120 | cap-120 supply_intelligence | batch01–06 pytest |
| 121 | cap-121 roi_ath_intelligence | batch01–06 pytest |
| 122 | cap-122 volatility_intelligence | batch01–06 pytest |
| 123 | cap-123 sharpe_ratio_intelligence | batch01–06 pytest |
| 124 | cap-124 futures_funding_rate_intelligence | batch01–06 pytest |
| 125 | cap-125 futures_open_interest_intelligence | batch01–06 pytest |
| 126 | cap-126 futures_volume_intelligence | batch01–06 pytest |
| 127 | cap-127 multi_factor_market_overview | batch01–06 pytest |
| 128 | cap-128 momentum_intelligence | batch01–06 pytest |
| 129 | cap-129 sentiment_intelligence | batch01–06 pytest |
| 130 | cap-130 mindshare_intelligence | batch01–06 pytest |
| 131 | cap-131 narrative_sector_intelligence | batch01–06 pytest |
| 132 | cap-132 mindshare_gainers_losers | batch01–06 pytest |
| 133 | cap-133 curated_crypto_news_intelligence | batch01–06 pytest |
| 134 | cap-134 ai_news_summaries | batch01–06 pytest |
| 135 | cap-135 real_time_industry_event_monitoring | batch01–06 pytest |
| 136 | cap-136 agentic_monitoring_views | batch01–06 pytest |
| 137 | cap-137 custom_watchlists | batch01–06 pytest |
| 138 | cap-138 token_unlock_calendar | batch01–06 pytest |
| 139 | cap-139 vesting_schedule_intelligence | batch01–06 pytest |
| 140 | cap-140 token_allocation_intelligence | batch01–06 pytest |
| 141 | cap-141 unlock_impact_intelligence | batch01–06 pytest |
| 142 | cap-142 fundraising_rounds_intelligence | batch01–06 pytest |
| 143 | cap-143 investor_intelligence | batch01–06 pytest |
| 144 | cap-144 fund_fund_manager_intelligence | batch01–06 pytest |
| 145 | cap-145 m_a_intelligence | batch01–06 pytest |
| 146 | cap-146 capital_flow_funding_trend_intelligence | batch01–06 pytest |
| 147 | cap-147 comparable_funding_valuation_analysis | batch01–06 pytest |
| 148 | cap-148 due_diligence_report_engine | batch01–06 pytest |
| 149 | cap-149 automated_risk_scoring_from_diligence | batch01–06 pytest |
| 150 | cap-150 protocol_kpi_intelligence | batch01–06 pytest |

### Build batches 07–10 (IDs 151–250)


| ID | Runbook tag | Rollback |
|---:|---|---|
| 151 | cap-151 quarterly_protocol_performance_reports | batch01–10 pytest |
| 152 | cap-152 governance_proposal_intelligence | batch01–10 pytest |
| 153 | cap-153 project_monitoring_coverage_registry | batch01–10 pytest |
| 154 | cap-154 ai_crypto_copilot | batch01–10 pytest |
| 155 | cap-155 ai_deep_research | batch01–10 pytest |
| 156 | cap-156 crypto_knowledge_graph | batch01–10 pytest |
| 157 | cap-157 research_library | batch01–10 pytest |
| 158 | cap-158 institutional_research_feed | batch01–10 pytest |
| 159 | cap-159 api_data_platform | batch01–10 pytest |
| 160 | cap-160 pay_per_request_data_access | batch01–10 pytest |
| 161 | cap-161 institutional_data_delivery_entitlements | batch01–10 pytest |
| 162 | cap-162 evidence_provenance_layer | batch01–10 pytest |
| 163 | cap-163 cross_domain_research_to_decision_intelligence | batch01–10 pytest |
| 164 | cap-164 token_unlock_actionability_score | batch01–10 pytest |
| 165 | cap-165 fundraising_momentum_score | batch01–10 pytest |
| 166 | cap-166 research_confidence_score | batch01–10 pytest |
| 167 | cap-167 social_volume_intelligence | batch01–10 pytest |
| 168 | cap-168 social_dominance_intelligence | batch01–10 pytest |
| 169 | cap-169 unique_social_volume | batch01–10 pytest |
| 170 | cap-170 trending_words | batch01–10 pytest |
| 171 | cap-171 trending_coins | batch01–10 pytest |
| 172 | cap-172 historical_crypto_trends | batch01–10 pytest |
| 173 | cap-173 key_narratives_intelligence | batch01–10 pytest |
| 174 | cap-174 alpha_narratives_intelligence | batch01–10 pytest |
| 175 | cap-175 social_sentiment_intelligence | batch01–10 pytest |
| 176 | cap-176 weighted_social_sentiment | batch01–10 pytest |
| 177 | cap-177 social_sentiment_balance | batch01–10 pytest |
| 178 | cap-178 social_source_breakdown | batch01–10 pytest |
| 179 | cap-179 development_activity_intelligence | batch01–10 pytest |
| 180 | cap-180 development_activity_contributors | batch01–10 pytest |
| 181 | cap-181 ecosystem_development_dashboard | batch01–10 pytest |
| 182 | cap-182 developer_activity_change_detection | batch01–10 pytest |
| 183 | cap-183 whale_transaction_intelligence | batch01–10 pytest |
| 184 | cap-184 whale_shark_holder_cohorts | batch01–10 pytest |
| 185 | cap-185 top_holders_intelligence | batch01–10 pytest |
| 186 | cap-186 historical_wallet_balance_tool | batch01–10 pytest |
| 187 | cap-187 exchange_inflow_intelligence | batch01–10 pytest |
| 188 | cap-188 exchange_outflow_intelligence | batch01–10 pytest |
| 189 | cap-189 exchange_netflow_intelligence | batch01–10 pytest |
| 190 | cap-190 exchange_supply_balance_intelligence | batch01–10 pytest |
| 191 | cap-191 exchange_user_activity | batch01–10 pytest |
| 192 | cap-192 network_activity_intelligence | batch01–10 pytest |
| 193 | cap-193 transaction_volume_intelligence | batch01–10 pytest |
| 194 | cap-194 nvt_intelligence | batch01–10 pytest |
| 195 | cap-195 mvrv_intelligence | batch01–10 pytest |
| 196 | cap-196 realized_cap_realized_value_intelligence | batch01–10 pytest |
| 197 | cap-197 daily_active_addresses | batch01–10 pytest |
| 198 | cap-198 age_consumed_dormancy_intelligence | batch01–10 pytest |
| 199 | cap-199 mean_dollar_invested_age | batch01–10 pytest |
| 200 | cap-200 token_circulation_intelligence | batch01–10 pytest |
| 201 | cap-201 network_growth_intelligence | batch01–10 pytest |
| 202 | cap-202 supply_distribution_intelligence | batch01–10 pytest |
| 203 | cap-203 dex_trading_intelligence | batch01–10 pytest |
| 204 | cap-204 defi_protocol_activity_intelligence | batch01–10 pytest |
| 205 | cap-205 open_interest_intelligence | batch01–10 pytest |
| 206 | cap-206 funding_rate_intelligence | batch01–10 pytest |
| 207 | cap-207 price_volume_market_metrics | batch01–10 pytest |
| 208 | cap-208 metric_correlation_workbench | batch01–10 pytest |
| 209 | cap-209 custom_chart_builder | batch01–10 pytest |
| 210 | cap-210 custom_dashboards_layouts | batch01–10 pytest |
| 211 | cap-211 screener | batch01–10 pytest |
| 212 | cap-212 smart_alerts | batch01–10 pytest |
| 213 | cap-213 anomaly_detection_alerts | batch01–10 pytest |
| 214 | cap-214 watchlists | batch01–10 pytest |
| 215 | cap-215 community_explorer | batch01–10 pytest |
| 216 | cap-216 research_market_insights | batch01–10 pytest |
| 217 | cap-217 sanapi_style_data_access | batch01–10 pytest |
| 218 | cap-218 google_sheets_integration | batch01–10 pytest |
| 219 | cap-219 metric_availability_registry | batch01–10 pytest |
| 220 | cap-220 data_stabilization_mutability_metadata | batch01–10 pytest |
| 221 | cap-221 data_quality_provenance_layer | batch01–10 pytest |
| 222 | cap-222 metric_methodology_registry | batch01–10 pytest |
| 223 | cap-223 social_to_on_chain_confirmation_engine | batch01–10 pytest |
| 224 | cap-224 narrative_actionability_score | batch01–10 pytest |
| 225 | cap-225 development_to_market_divergence_detector | batch01–10 pytest |
| 226 | cap-226 cross_domain_decision_intelligence_layer | batch01–10 pytest |
| 227 | cap-227 unified_trading_intelligence_workspace | batch01–10 pytest |
| 228 | cap-228 funding_rate_intelligence | batch01–10 pytest |
| 229 | cap-229 cross_exchange_funding_arbitrage_scanner | batch01–10 pytest |
| 230 | cap-230 spot_perp_arbitrage_scanner | batch01–10 pytest |
| 231 | cap-231 futures_basis_term_structure | batch01–10 pytest |
| 232 | cap-232 open_interest_intelligence | batch01–10 pytest |
| 233 | cap-233 liquidation_intelligence | batch01–10 pytest |
| 234 | cap-234 cvd_intelligence | batch01–10 pytest |
| 235 | cap-235 long_short_ratio_intelligence | batch01–10 pytest |
| 236 | cap-236 dex_screener | batch01–10 pytest |
| 237 | cap-237 token_risk_scoring | batch01–10 pytest |
| 238 | cap-238 pump_dump_detection | batch01–10 pytest |
| 239 | cap-239 narrative_tracking | batch01–10 pytest |
| 240 | cap-240 sector_rotation_intelligence | batch01–10 pytest |
| 241 | cap-241 sentiment_intelligence | batch01–10 pytest |
| 242 | cap-242 price_prediction_multi_signal_forecast | batch01–10 pytest |
| 243 | cap-243 correlation_matrix | batch01–10 pytest |
| 244 | cap-244 new_listings_intelligence | batch01–10 pytest |
| 245 | cap-245 market_health_freshness | batch01–10 pytest |
| 246 | cap-246 coverage_metadata_registry | batch01–10 pytest |
| 247 | cap-247 public_rest_api | batch01–10 pytest |
| 248 | cap-248 mcp_server_for_ai_agents | batch01–10 pytest |
| 249 | cap-249 cli_access | batch01–10 pytest |
| 250 | cap-250 openapi_sdk_generation | batch01–10 pytest |
### Build batches 11–16 (IDs 251–400)


| ID | Runbook tag | Rollback |
|---:|---|---|
| 251 | cap-251 cross_domain_decision_intelligence | batch01–16 pytest |
| 252 | cap-252 liquidation_heatmap | batch01–16 pytest |
| 253 | cap-253 liquidation_map_levels | batch01–16 pytest |
| 254 | cap-254 real_time_liquidation_events | batch01–16 pytest |
| 255 | cap-255 open_interest_intelligence | batch01–16 pytest |
| 256 | cap-256 funding_rate_intelligence | batch01–16 pytest |
| 257 | cap-257 long_short_ratio_intelligence | batch01–16 pytest |
| 258 | cap-258 top_trader_positioning | batch01–16 pytest |
| 259 | cap-259 futures_basis_intelligence | batch01–16 pytest |
| 260 | cap-260 futures_volume_intelligence | batch01–16 pytest |
| 261 | cap-261 futures_cvd_taker_flow | batch01–16 pytest |
| 262 | cap-262 options_open_interest | batch01–16 pytest |
| 263 | cap-263 options_volume | batch01–16 pytest |
| 264 | cap-264 options_iv_skew | batch01–16 pytest |
| 265 | cap-265 max_pain_gamma_context | batch01–16 pytest |
| 266 | cap-266 spot_market_intelligence | batch01–16 pytest |
| 267 | cap-267 order_book_market_depth | batch01–16 pytest |
| 268 | cap-268 historical_derivatives_data | batch01–16 pytest |
| 269 | cap-269 exchange_comparison | batch01–16 pytest |
| 270 | cap-270 liquidation_cascade_proximity | batch01–16 pytest |
| 271 | cap-271 leverage_pressure_score | batch01–16 pytest |
| 272 | cap-272 api_data_platform | batch01–16 pytest |
| 273 | cap-273 multi_model_liquidation_comparison | batch01–16 pytest |
| 274 | cap-274 derivatives_alerts | batch01–16 pytest |
| 275 | cap-275 cross_domain_decision_intelligence | batch01–16 pytest |
| 276 | cap-276 entity_resolution_engine | batch01–16 pytest |
| 277 | cap-277 address_labeling_system | batch01–16 pytest |
| 278 | cap-278 entity_profiles | batch01–16 pytest |
| 279 | cap-279 transaction_search | batch01–16 pytest |
| 280 | cap-280 portfolio_holdings | batch01–16 pytest |
| 281 | cap-281 balance_history | batch01–16 pytest |
| 282 | cap-282 entity_pnl | batch01–16 pytest |
| 283 | cap-283 exchange_usage_intelligence | batch01–16 pytest |
| 284 | cap-284 top_counterparties | batch01–16 pytest |
| 285 | cap-285 visualizer_network_graph | batch01–16 pytest |
| 286 | cap-286 automated_trace_path_finding | batch01–16 pytest |
| 287 | cap-287 cross_chain_trace | batch01–16 pytest |
| 288 | cap-288 token_top_holders | batch01–16 pytest |
| 289 | cap-289 token_exchange_flows | batch01–16 pytest |
| 290 | cap-290 token_transaction_explorer | batch01–16 pytest |
| 291 | cap-291 custom_dashboards | batch01–16 pytest |
| 292 | cap-292 custom_alerts | batch01–16 pytest |
| 293 | cap-293 private_labels | batch01–16 pytest |
| 294 | cap-294 archive_historical_portfolio_snapshot | batch01–16 pytest |
| 295 | cap-295 ai_market_insights | batch01–16 pytest |
| 296 | cap-296 whale_movement_intelligence | batch01–16 pytest |
| 297 | cap-297 fraud_suspicious_activity_intelligence | batch01–16 pytest |
| 298 | cap-298 api_on_chain_intelligence | batch01–16 pytest |
| 299 | cap-299 cross_entity_decision_intelligence | batch01–16 pytest |
| 300 | cap-300 advanced_multi_asset_charting | batch01–16 pytest |
| 301 | cap-301 multi_chart_layouts | batch01–16 pytest |
| 302 | cap-302 technical_indicator_library | batch01–16 pytest |
| 303 | cap-303 custom_indicator_scripting | batch01–16 pytest |
| 304 | cap-304 strategy_backtesting | batch01–16 pytest |
| 305 | cap-305 market_screener | batch01–16 pytest |
| 306 | cap-306 pine_style_screener | batch01–16 pytest |
| 307 | cap-307 smart_alerts | batch01–16 pytest |
| 308 | cap-308 watchlists | batch01–16 pytest |
| 309 | cap-309 economic_calendar | batch01–16 pytest |
| 310 | cap-310 crypto_calendar_events | batch01–16 pytest |
| 311 | cap-311 news_integration | batch01–16 pytest |
| 312 | cap-312 heatmaps | batch01–16 pytest |
| 313 | cap-313 technical_ratings | batch01–16 pytest |
| 314 | cap-314 drawing_tools | batch01–16 pytest |
| 315 | cap-315 replay_mode | batch01–16 pytest |
| 316 | cap-316 idea_chart_sharing | batch01–16 pytest |
| 317 | cap-317 community_scripts | batch01–16 pytest |
| 318 | cap-318 broker_comparison | batch01–16 pytest |
| 319 | cap-319 paper_trading_simulation | batch01–16 pytest |
| 320 | cap-320 cross_market_workspace | batch01–16 pytest |
| 321 | cap-321 custom_intelligence_screener | batch01–16 pytest |
| 322 | cap-322 decision_first_mode | batch01–16 pytest |
| 323 | cap-323 institutional_l1_l2_market_data | batch01–16 pytest |
| 324 | cap-324 reference_data_registry | batch01–16 pytest |
| 325 | cap-325 spot_derivatives_coverage | batch01–16 pytest |
| 326 | cap-326 defi_market_data | batch01–16 pytest |
| 327 | cap-327 market_depth_liquidity_intelligence | batch01–16 pytest |
| 328 | cap-328 fair_market_value_pricing | batch01–16 pytest |
| 329 | cap-329 best_execution_pricing | batch01–16 pytest |
| 330 | cap-330 reference_rates | batch01–16 pytest |
| 331 | cap-331 etf_reference_rates_inav | batch01–16 pytest |
| 332 | cap-332 commodity_tradfi_reference_rates | batch01–16 pytest |
| 333 | cap-333 indices | batch01–16 pytest |
| 334 | cap-334 risk_analytics | batch01–16 pytest |
| 335 | cap-335 derivatives_listing_analytics | batch01–16 pytest |
| 336 | cap-336 market_surveillance | batch01–16 pytest |
| 337 | cap-337 aml_cft_on_chain_monitoring | batch01–16 pytest |
| 338 | cap-338 data_quality_pipeline | batch01–16 pytest |
| 339 | cap-339 data_provenance_audit | batch01–16 pytest |
| 340 | cap-340 real_time_rest_grpc_streaming | batch01–16 pytest |
| 341 | cap-341 historical_data_archive | batch01–16 pytest |
| 342 | cap-342 venue_quality_ranking | batch01–16 pytest |
| 343 | cap-343 execution_quality_analytics | batch01–16 pytest |
| 344 | cap-344 institutional_sla_monitoring | batch01–16 pytest |
| 345 | cap-345 cross_market_institutional_decision_layer | batch01–16 pytest |
| 346 | cap-346 standardized_financial_metrics | batch01–16 pytest |
| 347 | cap-347 fees_intelligence | batch01–16 pytest |
| 348 | cap-348 revenue_intelligence | batch01–16 pytest |
| 349 | cap-349 token_incentives | batch01–16 pytest |
| 350 | cap-350 earnings_economic_profit_proxy | batch01–16 pytest |
| 351 | cap-351 active_users | batch01–16 pytest |
| 352 | cap-352 core_developers | batch01–16 pytest |
| 353 | cap-353 code_commits | batch01–16 pytest |
| 354 | cap-354 tvl_intelligence | batch01–16 pytest |
| 355 | cap-355 borrowed_loans_outstanding | batch01–16 pytest |
| 356 | cap-356 dex_volume | batch01–16 pytest |
| 357 | cap-357 stablecoin_supply | batch01–16 pytest |
| 358 | cap-358 valuation_multiples | batch01–16 pytest |
| 359 | cap-359 growth_metrics | batch01–16 pytest |
| 360 | cap-360 margins_take_rate | batch01–16 pytest |
| 361 | cap-361 project_comparables | batch01–16 pytest |
| 362 | cap-362 sector_comparables | batch01–16 pytest |
| 363 | cap-363 tokenized_asset_coverage | batch01–16 pytest |
| 364 | cap-364 fundamental_screener | batch01–16 pytest |
| 365 | cap-365 financial_statement_view | batch01–16 pytest |
| 366 | cap-366 data_methodology_registry | batch01–16 pytest |
| 367 | cap-367 source_data_provenance | batch01–16 pytest |
| 368 | cap-368 api_data_export | batch01–16 pytest |
| 369 | cap-369 cross_fundamental_decision_intelligence | batch01–16 pytest |
| 370 | cap-370 sql_on_chain_query_workspace | batch01–16 pytest |
| 371 | cap-371 curated_data_models | batch01–16 pytest |
| 372 | cap-372 decoded_smart_contract_tables | batch01–16 pytest |
| 373 | cap-373 cross_chain_data_warehouse | batch01–16 pytest |
| 374 | cap-374 visualization_builder | batch01–16 pytest |
| 375 | cap-375 dashboard_builder | batch01–16 pytest |
| 376 | cap-376 public_dashboard_sharing | batch01–16 pytest |
| 377 | cap-377 community_discovery | batch01–16 pytest |
| 378 | cap-378 query_forking | batch01–16 pytest |
| 379 | cap-379 data_api | batch01–16 pytest |
| 380 | cap-380 real_time_feed | batch01–16 pytest |
| 381 | cap-381 datashare | batch01–16 pytest |
| 382 | cap-382 dbt_connector | batch01–16 pytest |
| 383 | cap-383 bi_connectors | batch01–16 pytest |
| 384 | cap-384 mcp_for_ai_agents | batch01–16 pytest |
| 385 | cap-385 prompt_to_sql_agent | batch01–16 pytest |
| 386 | cap-386 dashboard_from_prompt | batch01–16 pytest |
| 387 | cap-387 scheduled_queries | batch01–16 pytest |
| 388 | cap-388 alerts_from_query_results | batch01–16 pytest |
| 389 | cap-389 data_lineage | batch01–16 pytest |
| 390 | cap-390 query_performance_governance | batch01–16 pytest |
| 391 | cap-391 white_label_embedded_analytics | batch01–16 pytest |
| 392 | cap-392 cross_domain_decision_layer | batch01–16 pytest |
| 393 | cap-393 tvl_intelligence | batch01–16 pytest |
| 394 | cap-394 chain_tvl_comparison | batch01–16 pytest |
| 395 | cap-395 protocol_directory | batch01–16 pytest |
| 396 | cap-396 fees_revenue | batch01–16 pytest |
| 397 | cap-397 dex_volume | batch01–16 pytest |
| 398 | cap-398 perps_volume | batch01–16 pytest |
| 399 | cap-399 options_volume | batch01–16 pytest |
| 400 | cap-400 stablecoins_intelligence | batch01–16 pytest |

### Build batches 17–20 (IDs 401–500)


| ID | Runbook tag | Rollback |
|---:|---|---|
| 401 | cap-401 bridges_intelligence | batch01–20 pytest |
| 402 | cap-402 yields_screener | batch01–20 pytest |
| 403 | cap-403 yield_history | batch01–20 pytest |
| 404 | cap-404 borrowing_rates | batch01–20 pytest |
| 405 | cap-405 liquid_staking_intelligence | batch01–20 pytest |
| 406 | cap-406 rwa_intelligence | batch01–20 pytest |
| 407 | cap-407 raises_funding_rounds | batch01–20 pytest |
| 408 | cap-408 investor_profiles | batch01–20 pytest |
| 409 | cap-409 unlocks | batch01–20 pytest |
| 410 | cap-410 treasury_intelligence | batch01–20 pytest |
| 411 | cap-411 airdrop_incentive_intelligence | batch01–20 pytest |
| 412 | cap-412 capital_formation_radar | batch01–20 pytest |
| 413 | cap-413 defi_opportunity_screener | batch01–20 pytest |
| 414 | cap-414 defi_risk_passport | batch01–20 pytest |
| 415 | cap-415 api_aggregation_layer | batch01–20 pytest |
| 416 | cap-416 cross_defi_decision_intelligence | batch01–20 pytest |
| 417 | cap-417 cross_chain_fundamentals | batch01–20 pytest |
| 418 | cap-418 protocol_fundamentals | batch01–20 pytest |
| 419 | cap-419 stablecoin_intelligence | batch01–20 pytest |
| 420 | cap-420 stablecoin_activity_breakdown | batch01–20 pytest |
| 421 | cap-421 developer_activity | batch01–20 pytest |
| 422 | cap-422 sector_ecosystem_comparables | batch01–20 pytest |
| 423 | cap-423 equities_crypto_research | batch01–20 pytest |
| 424 | cap-424 consensus_estimates | batch01–20 pytest |
| 425 | cap-425 ai_analyst | batch01–20 pytest |
| 426 | cap-426 thesis_research_workspace | batch01–20 pytest |
| 427 | cap-427 comparable_company_protocol_analysis | batch01–20 pytest |
| 428 | cap-428 excel_sheets_integration | batch01–20 pytest |
| 429 | cap-429 api_data_platform | batch01–20 pytest |
| 430 | cap-430 research_templates | batch01–20 pytest |
| 431 | cap-431 dashboards | batch01–20 pytest |
| 432 | cap-432 stablecoin_payment_intelligence | batch01–20 pytest |
| 433 | cap-433 on_chain_usage_intelligence | batch01–20 pytest |
| 434 | cap-434 revenue_fees_economic_activity | batch01–20 pytest |
| 435 | cap-435 cross_market_research_copilot | batch01–20 pytest |
| 436 | cap-436 investment_thesis_scoring | batch01–20 pytest |
| 437 | cap-437 defi_risk_radar | batch01–20 pytest |
| 438 | cap-438 lending_market_risk | batch01–20 pytest |
| 439 | cap-439 collateral_risk | batch01–20 pytest |
| 440 | cap-440 liquidation_risk | batch01–20 pytest |
| 441 | cap-441 oracle_risk | batch01–20 pytest |
| 442 | cap-442 liquidity_risk | batch01–20 pytest |
| 443 | cap-443 protocol_exploit_intelligence | batch01–20 pytest |
| 444 | cap-444 stablecoin_risk_intelligence | batch01–20 pytest |
| 445 | cap-445 defi_strategy_risk | batch01–20 pytest |
| 446 | cap-446 real_time_risk_alerts | batch01–20 pytest |
| 447 | cap-447 dao_treasury_risk | batch01–20 pytest |
| 448 | cap-448 institutional_risk_api | batch01–20 pytest |
| 449 | cap-449 curated_on_chain_dashboards | batch01–20 pytest |
| 450 | cap-450 narrative_driven_research | batch01–20 pytest |
| 451 | cap-451 protocol_dominance | batch01–20 pytest |
| 452 | cap-452 aave_multi_chain_analytics | batch01–20 pytest |
| 453 | cap-453 risk_curation | batch01–20 pytest |
| 454 | cap-454 capital_protection_controls | batch01–20 pytest |
| 455 | cap-455 stress_testing | batch01–20 pytest |
| 456 | cap-456 cross_protocol_contagion | batch01–20 pytest |
| 457 | cap-457 protocol_risk_passport | batch01–20 pytest |
| 458 | cap-458 risk_to_decision_intelligence | batch01–20 pytest |
| 459 | cap-459 network_data_pro_metrics | batch01–20 pytest |
| 460 | cap-460 atlas_blockchain_search | batch01–20 pytest |
| 461 | cap-461 address_balance_search | batch01–20 pytest |
| 462 | cap-462 transaction_search | batch01–20 pytest |
| 463 | cap-463 block_search | batch01–20 pytest |
| 464 | cap-464 balance_updates | batch01–20 pytest |
| 465 | cap-465 stablecoin_network_metrics | batch01–20 pytest |
| 466 | cap-466 market_data_feed | batch01–20 pytest |
| 467 | cap-467 market_data_pro | batch01–20 pytest |
| 468 | cap-468 reference_rates | batch01–20 pytest |
| 469 | cap-469 indexes | batch01–20 pytest |
| 470 | cap-470 realized_metrics | batch01–20 pytest |
| 471 | cap-471 supply_metrics | batch01–20 pytest |
| 472 | cap-472 mining_validator_metrics | batch01–20 pytest |
| 473 | cap-473 fee_metrics | batch01–20 pytest |
| 474 | cap-474 activity_metrics | batch01–20 pytest |
| 475 | cap-475 custom_metric_workbench | batch01–20 pytest |
| 476 | cap-476 community_charts_api | batch01–20 pytest |
| 477 | cap-477 market_network_join | batch01–20 pytest |
| 478 | cap-478 data_quality_methodologies | batch01–20 pytest |
| 479 | cap-479 historical_research_dataset | batch01–20 pytest |
| 480 | cap-480 institutional_apis | batch01–20 pytest |
| 481 | cap-481 cross_network_decision_intelligence | batch01–20 pytest |
| 482 | cap-482 institutional_trade_data | batch01–20 pytest |
| 483 | cap-483 order_book_data | batch01–20 pytest |
| 484 | cap-484 ohlcv_data | batch01–20 pytest |
| 485 | cap-485 derivatives_data | batch01–20 pytest |
| 486 | cap-486 open_interest_data | batch01–20 pytest |
| 487 | cap-487 funding_rate_data | batch01–20 pytest |
| 488 | cap-488 index_data | batch01–20 pytest |
| 489 | cap-489 reference_pricing | batch01–20 pytest |
| 490 | cap-490 exchange_metadata | batch01–20 pytest |
| 491 | cap-491 asset_metadata | batch01–20 pytest |
| 492 | cap-492 historical_market_archive | batch01–20 pytest |
| 493 | cap-493 real_time_streams | batch01–20 pytest |
| 494 | cap-494 market_aggregates | batch01–20 pytest |
| 495 | cap-495 liquidity_analytics | batch01–20 pytest |
| 496 | cap-496 volatility_analytics | batch01–20 pytest |
| 497 | cap-497 market_cap_supply | batch01–20 pytest |
| 498 | cap-498 etf_etp_data | batch01–20 pytest |
| 499 | cap-499 api_coverage_registry | batch01–20 pytest |
| 500 | cap-500 data_quality_normalization | batch01–20 pytest |

### Build batches 21–24 (IDs 501–600)


| ID | Runbook tag | Rollback |
|---:|---|---|
| 501 | cap-501 institutional_delivery | batch01–24 pytest |
| 502 | cap-502 benchmark_administration_metadata | batch01–24 pytest |
| 503 | cap-503 cross_market_data_intelligence | batch01–24 pytest |
| 504 | cap-504 unified_exchange_connector_layer | batch01–24 pytest |
| 505 | cap-505 tick_trade_data | batch01–24 pytest |
| 506 | cap-506 quote_data | batch01–24 pytest |
| 507 | cap-507 ohlcv | batch01–24 pytest |
| 508 | cap-508 l1_order_book | batch01–24 pytest |
| 509 | cap-509 l2_order_book | batch01–24 pytest |
| 510 | cap-510 l3_order_book | batch01–24 pytest |
| 511 | cap-511 options_market_data | batch01–24 pytest |
| 512 | cap-512 funding_oi_liquidation_metrics | batch01–24 pytest |
| 513 | cap-513 asset_symbol_metadata | batch01–24 pytest |
| 514 | cap-514 historical_flat_files | batch01–24 pytest |
| 515 | cap-515 rest_api | batch01–24 pytest |
| 516 | cap-516 websocket_streaming | batch01–24 pytest |
| 517 | cap-517 fix_connectivity | batch01–24 pytest |
| 518 | cap-518 mcp_for_ai | batch01–24 pytest |
| 519 | cap-519 exchange_rates_vwap | batch01–24 pytest |
| 520 | cap-520 indexes | batch01–24 pytest |
| 521 | cap-521 volatility_index | batch01–24 pytest |
| 522 | cap-522 ems_integration_boundary | batch01–24 pytest |
| 523 | cap-523 data_health_sla_monitoring | batch01–24 pytest |
| 524 | cap-524 symbol_mapping_engine | batch01–24 pytest |
| 525 | cap-525 cross_venue_data_quality_score | batch01–24 pytest |
| 526 | cap-526 ai_market_data_grounding_layer | batch01–24 pytest |
| 527 | cap-527 liquidation_heatmap | batch01–24 pytest |
| 528 | cap-528 liquidation_levels | batch01–24 pytest |
| 529 | cap-529 liquidation_cascade_model | batch01–24 pytest |
| 530 | cap-530 global_liquidation_metrics | batch01–24 pytest |
| 531 | cap-531 open_interest | batch01–24 pytest |
| 532 | cap-532 funding_rates | batch01–24 pytest |
| 533 | cap-533 order_flow_intelligence | batch01–24 pytest |
| 534 | cap-534 bucketed_cvd | batch01–24 pytest |
| 535 | cap-535 whale_vs_retail_flow | batch01–24 pytest |
| 536 | cap-536 slippage_intelligence | batch01–24 pytest |
| 537 | cap-537 global_order_book_metrics | batch01–24 pytest |
| 538 | cap-538 order_book_imbalance | batch01–24 pytest |
| 539 | cap-539 liquidity_zones | batch01–24 pytest |
| 540 | cap-540 bot_activity_detection | batch01–24 pytest |
| 541 | cap-541 market_positioning | batch01–24 pytest |
| 542 | cap-542 liquidation_pressure_score | batch01–24 pytest |
| 543 | cap-543 orderflow_anomaly_detection | batch01–24 pytest |
| 544 | cap-544 api_indicator_platform | batch01–24 pytest |
| 545 | cap-545 trader_cohort_intelligence | batch01–24 pytest |
| 546 | cap-546 cross_derivatives_decision_intelligence | batch01–24 pytest |
| 547 | cap-547 high_resolution_multi_pane_charts | batch01–24 pytest |
| 548 | cap-548 derivatives_dashboard | batch01–24 pytest |
| 549 | cap-549 funding_rate_intelligence | batch01–24 pytest |
| 550 | cap-550 open_interest_intelligence | batch01–24 pytest |
| 551 | cap-551 reserved_slot_551 | batch01–24 pytest |
| 552 | cap-552 reserved_slot_552 | batch01–24 pytest |
| 553 | cap-553 reserved_slot_553 | batch01–24 pytest |
| 554 | cap-554 reserved_slot_554 | batch01–24 pytest |
| 555 | cap-555 reserved_slot_555 | batch01–24 pytest |
| 556 | cap-556 reserved_slot_556 | batch01–24 pytest |
| 557 | cap-557 reserved_slot_557 | batch01–24 pytest |
| 558 | cap-558 reserved_slot_558 | batch01–24 pytest |
| 559 | cap-559 reserved_slot_559 | batch01–24 pytest |
| 560 | cap-560 reserved_slot_560 | batch01–24 pytest |
| 561 | cap-561 reserved_slot_561 | batch01–24 pytest |
| 562 | cap-562 reserved_slot_562 | batch01–24 pytest |
| 563 | cap-563 reserved_slot_563 | batch01–24 pytest |
| 564 | cap-564 reserved_slot_564 | batch01–24 pytest |
| 565 | cap-565 reserved_slot_565 | batch01–24 pytest |
| 566 | cap-566 reserved_slot_566 | batch01–24 pytest |
| 567 | cap-567 reserved_slot_567 | batch01–24 pytest |
| 568 | cap-568 reserved_slot_568 | batch01–24 pytest |
| 569 | cap-569 reserved_slot_569 | batch01–24 pytest |
| 570 | cap-570 reserved_slot_570 | batch01–24 pytest |
| 571 | cap-571 reserved_slot_571 | batch01–24 pytest |
| 572 | cap-572 reserved_slot_572 | batch01–24 pytest |
| 573 | cap-573 reserved_slot_573 | batch01–24 pytest |
| 574 | cap-574 reserved_slot_574 | batch01–24 pytest |
| 575 | cap-575 reserved_slot_575 | batch01–24 pytest |
| 576 | cap-576 reserved_slot_576 | batch01–24 pytest |
| 577 | cap-577 reserved_slot_577 | batch01–24 pytest |
| 578 | cap-578 reserved_slot_578 | batch01–24 pytest |
| 579 | cap-579 reserved_slot_579 | batch01–24 pytest |
| 580 | cap-580 reserved_slot_580 | batch01–24 pytest |
| 581 | cap-581 reserved_slot_581 | batch01–24 pytest |
| 582 | cap-582 reserved_slot_582 | batch01–24 pytest |
| 583 | cap-583 reserved_slot_583 | batch01–24 pytest |
| 584 | cap-584 reserved_slot_584 | batch01–24 pytest |
| 585 | cap-585 reserved_slot_585 | batch01–24 pytest |
| 586 | cap-586 reserved_slot_586 | batch01–24 pytest |
| 587 | cap-587 reserved_slot_587 | batch01–24 pytest |
| 588 | cap-588 reserved_slot_588 | batch01–24 pytest |
| 589 | cap-589 reserved_slot_589 | batch01–24 pytest |
| 590 | cap-590 reserved_slot_590 | batch01–24 pytest |
| 591 | cap-591 reserved_slot_591 | batch01–24 pytest |
| 592 | cap-592 reserved_slot_592 | batch01–24 pytest |
| 593 | cap-593 reserved_slot_593 | batch01–24 pytest |
| 594 | cap-594 reserved_slot_594 | batch01–24 pytest |
| 595 | cap-595 reserved_slot_595 | batch01–24 pytest |
| 596 | cap-596 reserved_slot_596 | batch01–24 pytest |
| 597 | cap-597 reserved_slot_597 | batch01–24 pytest |
| 598 | cap-598 reserved_slot_598 | batch01–24 pytest |
| 599 | cap-599 reserved_slot_599 | batch01–24 pytest |
| 600 | cap-600 reserved_slot_600 | batch01–24 pytest |

### Build batch 25 (IDs 601–650)


| ID | Runbook tag | Rollback |
|---:|---|---|
| 601 | cap-601 reserved_slot_601 | batch01–25 pytest |
| 602 | cap-602 reserved_slot_602 | batch01–25 pytest |
| 603 | cap-603 reserved_slot_603 | batch01–25 pytest |
| 604 | cap-604 reserved_slot_604 | batch01–25 pytest |
| 605 | cap-605 reserved_slot_605 | batch01–25 pytest |
| 606 | cap-606 reserved_slot_606 | batch01–25 pytest |
| 607 | cap-607 reserved_slot_607 | batch01–25 pytest |
| 608 | cap-608 reserved_slot_608 | batch01–25 pytest |
| 609 | cap-609 reserved_slot_609 | batch01–25 pytest |
| 610 | cap-610 reserved_slot_610 | batch01–25 pytest |
| 611 | cap-611 reserved_slot_611 | batch01–25 pytest |
| 612 | cap-612 reserved_slot_612 | batch01–25 pytest |
| 613 | cap-613 reserved_slot_613 | batch01–25 pytest |
| 614 | cap-614 reserved_slot_614 | batch01–25 pytest |
| 615 | cap-615 reserved_slot_615 | batch01–25 pytest |
| 616 | cap-616 reserved_slot_616 | batch01–25 pytest |
| 617 | cap-617 reserved_slot_617 | batch01–25 pytest |
| 618 | cap-618 reserved_slot_618 | batch01–25 pytest |
| 619 | cap-619 reserved_slot_619 | batch01–25 pytest |
| 620 | cap-620 reserved_slot_620 | batch01–25 pytest |
| 621 | cap-621 reserved_slot_621 | batch01–25 pytest |
| 622 | cap-622 reserved_slot_622 | batch01–25 pytest |
| 623 | cap-623 reserved_slot_623 | batch01–25 pytest |
| 624 | cap-624 reserved_slot_624 | batch01–25 pytest |
| 625 | cap-625 reserved_slot_625 | batch01–25 pytest |
| 626 | cap-626 reserved_slot_626 | batch01–25 pytest |
| 627 | cap-627 reserved_slot_627 | batch01–25 pytest |
| 628 | cap-628 reserved_slot_628 | batch01–25 pytest |
| 629 | cap-629 reserved_slot_629 | batch01–25 pytest |
| 630 | cap-630 reserved_slot_630 | batch01–25 pytest |
| 631 | cap-631 reserved_slot_631 | batch01–25 pytest |
| 632 | cap-632 reserved_slot_632 | batch01–25 pytest |
| 633 | cap-633 reserved_slot_633 | batch01–25 pytest |
| 634 | cap-634 reserved_slot_634 | batch01–25 pytest |
| 635 | cap-635 reserved_slot_635 | batch01–25 pytest |
| 636 | cap-636 reserved_slot_636 | batch01–25 pytest |
| 637 | cap-637 reserved_slot_637 | batch01–25 pytest |
| 638 | cap-638 reserved_slot_638 | batch01–25 pytest |
| 639 | cap-639 reserved_slot_639 | batch01–25 pytest |
| 640 | cap-640 reserved_slot_640 | batch01–25 pytest |
| 641 | cap-641 reserved_slot_641 | batch01–25 pytest |
| 642 | cap-642 reserved_slot_642 | batch01–25 pytest |
| 643 | cap-643 reserved_slot_643 | batch01–25 pytest |
| 644 | cap-644 reserved_slot_644 | batch01–25 pytest |
| 645 | cap-645 reserved_slot_645 | batch01–25 pytest |
| 646 | cap-646 reserved_slot_646 | batch01–25 pytest |
| 647 | cap-647 real_time_feed | batch01–25 pytest |
| 648 | cap-648 datashare_connector | batch01–25 pytest |
| 649 | cap-649 reserved_slot_649 | batch01–25 pytest |
| 650 | cap-650 reserved_slot_650 | batch01–25 pytest |
