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