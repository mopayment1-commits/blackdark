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
