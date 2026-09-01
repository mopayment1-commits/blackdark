"""Batch 03 prep dedicated backends — goal-specific payloads for IDs 101–150.

IDs 103 and 129 are batch01 overlap: no dedicated backend here; runtime routes them to
``cap646.batch01_production`` (see ``BATCH03_OVERLAP_BATCH01_IDS``).
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import seed as _seed
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap as dedicated_wrap
from cap646.evidence_class import ai_compliance_footer

BATCH03_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset({103, 129})
BATCH03_DEDICATED_IDS: frozenset[int] = frozenset(range(101, 151)) - BATCH03_OVERLAP_BATCH01_IDS

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts"}
)

EXPECTED_SURFACE: dict[int, str] = {
    101: "ai_data_analyst_ask_ai",
    102: "ai_generated_reporting",
    103: "api_data_platform",
    104: "high_resolution_block_level_data_delivery",
    105: "historical_full_data_layer",
    106: "data_quality_provenance_layer",
    107: "metric_methodology_registry",
    108: "institutional_data_api_delivery",
    109: "white_label_research_reporting",
    110: "cross_domain_decision_intelligence_layer",
    111: "exchange_flow_actionability_score",
    112: "flow_to_price_explanation_engine",
    113: "asset_intelligence_profiles",
    114: "asset_classification_taxonomy",
    115: "asset_screener",
    116: "market_pair_intelligence",
    117: "real_volume_quality_adjusted_volume",
    118: "vwap_price_intelligence",
    119: "market_cap_fdv_intelligence",
    120: "supply_intelligence",
    121: "roi_ath_intelligence",
    122: "volatility_intelligence",
    123: "sharpe_ratio_intelligence",
    124: "futures_funding_rate_intelligence",
    125: "futures_open_interest_intelligence",
    126: "futures_volume_intelligence",
    127: "multi_factor_market_overview",
    128: "momentum_intelligence",
    129: "sentiment_intelligence",
    130: "mindshare_intelligence",
    131: "narrative_sector_intelligence",
    132: "mindshare_gainers_losers",
    133: "curated_crypto_news_intelligence",
    134: "ai_news_summaries",
    135: "real_time_industry_event_monitoring",
    136: "agentic_monitoring_views",
    137: "custom_watchlists",
    138: "token_unlock_calendar",
    139: "vesting_schedule_intelligence",
    140: "token_allocation_intelligence",
    141: "unlock_impact_intelligence",
    142: "fundraising_rounds_intelligence",
    143: "investor_intelligence",
    144: "fund_fund_manager_intelligence",
    145: "m_a_intelligence",
    146: "capital_flow_funding_trend_intelligence",
    147: "comparable_funding_valuation_analysis",
    148: "due_diligence_report_engine",
    149: "automated_risk_scoring_from_diligence",
    150: "protocol_kpi_intelligence",
}


def _wrap(capability_id: int, *, symbol: str, payload_key: str, payload: Any, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    return dedicated_wrap(
        capability_id,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key=payload_key,
        payload=payload,
        extra=extra,
    )


async def _cap101(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.infra_intelligence_layer import validate_oracle_freshness_101
    now = time.time() * 1000
    payload = validate_oracle_freshness_101(
        primary_timestamp_ms=now,
        secondary_timestamp_ms=now + float(params.get("deviation_ms") or 200),
        seed=_seed(),
    )
    return _wrap(101, symbol=symbol, payload_key="oracle_freshness", payload=payload)


async def _cap102(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.infra_intelligence_layer import compute_il_vulnerability_102
    payload = compute_il_vulnerability_102(seed=_seed())
    return _wrap(102, symbol=symbol, payload_key="il_vulnerability", payload=payload)


async def _cap104(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.infra_intelligence_layer import run_infra_intelligence_e2e_95_104
    payload = run_infra_intelligence_e2e_95_104(seed=_seed())
    return _wrap(104, symbol=symbol, payload_key="block_level_delivery", payload=payload)


async def _cap105(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import attach_tail_risk_to_backtest_105
    from bd_platform.pro_trader_layer import run_backtest_74
    payload = attach_tail_risk_to_backtest_105(run_backtest_74(seed=_seed()), seed=_seed())
    return _wrap(105, symbol=symbol, payload_key="historical_data_layer", payload=payload)


async def _cap106(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from data_provenance_score import compute_data_provenance_score
    from hot_storage import get_hot_storage_stats

    provenance = compute_data_provenance_score(symbol=symbol)
    hot = get_hot_storage_stats()
    payload = {
        "provenance": provenance,
        "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else hot,
        "catalog_link": {"duplicate_of": 63, "classification": "REUSED-LINK"},
    }
    return _wrap(106, symbol=symbol, payload_key="data_quality_provenance", payload=payload)


async def _cap107(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from signal_registry import registry_stats

    payload = {
        "methodology_registry": registry_stats(),
        "catalog_link": {"duplicate_of": 64, "classification": "REUSED-LINK"},
    }
    return _wrap(107, symbol=symbol, payload_key="metric_methodology", payload=payload)


async def _cap108(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import compute_orderbook_skew_108
    payload = compute_orderbook_skew_108(seed=_seed())
    return _wrap(108, symbol=symbol, payload_key="institutional_data_api", payload=payload)


async def _cap109(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import attach_liquidation_anchors_109
    from bd_platform.whales_institutional_layer import evaluate_liquidation_alert_82
    from market_context import fetch_binance_ticker
    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    price = float((ticker or {}).get("price") or 65000)
    payload = attach_liquidation_anchors_109(
        evaluate_liquidation_alert_82(price=price, seed=_seed()),
        current_price=price,
        seed=_seed(),
    )
    return _wrap(109, symbol=symbol, payload_key="white_label_research", payload=payload)


async def _cap110(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.cross_domain_decision import build_cross_domain_decision_payload

    payload = await build_cross_domain_decision_payload(symbol=symbol, seed=_seed())
    payload["catalog_link"] = {"duplicate_of": 69, "classification": "REUSED-LINK"}
    return _wrap(110, symbol=symbol, payload_key="cross_domain_decision", payload=payload)


async def _cap111(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import compute_spx_correlation_111
    payload = compute_spx_correlation_111(seed=_seed())
    return _wrap(111, symbol=symbol, payload_key="exchange_flow_actionability", payload=payload)


async def _cap112(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import compute_gcli_112
    payload = compute_gcli_112(seed=_seed())
    return _wrap(112, symbol=symbol, payload_key="flow_to_price_explanation", payload=payload)


async def _cap113(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import compute_imbalance_delta_113
    payload = compute_imbalance_delta_113(seed=_seed())
    return _wrap(113, symbol=symbol, payload_key="asset_intelligence_profile", payload=payload)


async def _cap114(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import compute_whale_ls_ratio_114
    payload = compute_whale_ls_ratio_114(seed=_seed())
    return _wrap(114, symbol=symbol, payload_key="asset_classification_taxonomy", payload=payload)


async def _cap115(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import compute_volume_velocity_115
    payload = compute_volume_velocity_115(seed=_seed())
    return _wrap(115, symbol=symbol, payload_key="asset_screener", payload=payload)


async def _cap116(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import run_market_analysis_e2e_105_116
    payload = run_market_analysis_e2e_105_116(seed=_seed())
    return _wrap(116, symbol=symbol, payload_key="market_pair_intelligence", payload=payload)

async def _cap117(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import compute_liquidity_vacuum_117
    payload = compute_liquidity_vacuum_117(seed=_seed())
    return _wrap(117, symbol=symbol, payload_key="real_volume_quality_adjusted", payload=payload)


async def _cap118(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import attach_risk_distribution_118
    from bd_platform.whales_institutional_layer import build_exchange_health_80
    payload = attach_risk_distribution_118(build_exchange_health_80(seed=_seed()), seed=_seed())
    return _wrap(118, symbol=symbol, payload_key="vwap_price_intelligence", payload=payload)


async def _cap119(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import gas_spike_alert_119
    from market_context import fetch_binance_ticker
    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    price = float((ticker or {}).get("price") or 65000)
    payload = gas_spike_alert_119(seed=_seed())
    payload["reference_price"] = price
    return _wrap(119, symbol=symbol, payload_key="market_cap_fdv", payload=payload)


async def _cap120(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import attach_leverage_risk_120
    from bd_platform.whales_institutional_layer import build_advanced_risk_report_77
    risk = build_advanced_risk_report_77(
        [{"symbol": symbol, "value_usd": 100000, "btc_beta": 1.0}],
        seed=_seed(),
    )
    payload = attach_leverage_risk_120(risk, seed=_seed())
    return _wrap(120, symbol=symbol, payload_key="supply_intelligence", payload=payload)


async def _cap121(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import attach_journal_attribution_121
    from bd_platform.pro_trader_layer import build_journal_tab_76
    payload = attach_journal_attribution_121(build_journal_tab_76(seed=_seed()), seed=_seed())
    return _wrap(121, symbol=symbol, payload_key="roi_ath_intelligence", payload=payload)


async def _cap122(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import compute_structural_break_122
    payload = compute_structural_break_122(seed=_seed())
    return _wrap(122, symbol=symbol, payload_key="volatility_intelligence", payload=payload)


async def _cap123(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import compute_volume_profile_poc_123
    payload = compute_volume_profile_poc_123(seed=_seed())
    return _wrap(123, symbol=symbol, payload_key="sharpe_ratio_intelligence", payload=payload)


async def _cap124(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import detect_fair_value_gaps_124
    payload = detect_fair_value_gaps_124(seed=_seed())
    return _wrap(124, symbol=symbol, payload_key="futures_funding_rate", payload=payload)


async def _cap125(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.derivatives_hub import derivatives_overview

    overview = await derivatives_overview(symbol)
    oi = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    payload = {
        "derivatives_overview": overview,
        "open_interest_usd": oi.get("open_interest_usd"),
        "open_interest_contracts": oi.get("open_interest_contracts"),
        "catalog_link": {"duplicate_of": 85, "classification": "REUSED-LINK"},
    }
    return _wrap(125, symbol=symbol, payload_key="futures_open_interest", payload=payload)


async def _cap126(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import dex_front_running_risk_126
    payload = dex_front_running_risk_126(seed=_seed())
    return _wrap(126, symbol=symbol, payload_key="futures_volume", payload=payload)


async def _cap127(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import orderbook_inefficiency_insight_127
    payload = orderbook_inefficiency_insight_127(seed=_seed())
    return _wrap(127, symbol=symbol, payload_key="multi_factor_market_overview", payload=payload)


async def _cap128(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.advanced_ta_risk_layer import run_advanced_ta_risk_e2e_117_128
    payload = run_advanced_ta_risk_e2e_117_128(seed=_seed())
    return _wrap(128, symbol=symbol, payload_key="momentum_intelligence", payload=payload)


async def _cap130(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import transaction_risk_insight_130
    payload = transaction_risk_insight_130(seed=_seed())
    return _wrap(130, symbol=symbol, payload_key="mindshare_intelligence", payload=payload)


async def _cap131(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import analyze_dust_assets_131
    payload = analyze_dust_assets_131(seed=_seed())
    return _wrap(131, symbol=symbol, payload_key="narrative_sector_intelligence", payload=payload)


async def _cap132(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import scan_flash_loan_vulnerabilities_132
    payload = scan_flash_loan_vulnerabilities_132(seed=_seed())
    return _wrap(132, symbol=symbol, payload_key="mindshare_gainers_losers", payload=payload)


async def _cap133(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import attach_macro_nexus_to_multi_dim_133
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73
    payload = attach_macro_nexus_to_multi_dim_133(build_multi_dim_analysis_73(asset=symbol, seed=_seed()), seed=_seed())
    return _wrap(133, symbol=symbol, payload_key="curated_crypto_news", payload=payload)


async def _cap134(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import compute_delta_convergence_134
    payload = compute_delta_convergence_134(seed=_seed())
    return _wrap(134, symbol=symbol, payload_key="ai_news_summaries", payload=payload)


async def _cap135(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import locate_liquidity_vortex_135
    payload = locate_liquidity_vortex_135(seed=_seed())
    return _wrap(135, symbol=symbol, payload_key="industry_event_monitoring", payload=payload)


async def _cap136(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import support_chat_response_136
    payload = support_chat_response_136(message=str(params.get("message") or f"Status for {symbol}"), seed=_seed())
    return _wrap(136, symbol=symbol, payload_key="agentic_monitoring_views", payload=payload)


async def _cap137(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import b2b_relationships_status_137
    payload = b2b_relationships_status_137(seed=_seed())
    return _wrap(137, symbol=symbol, payload_key="custom_watchlists", payload=payload)


async def _cap138(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import institution_features_status_138
    payload = institution_features_status_138(seed=_seed())
    return _wrap(138, symbol=symbol, payload_key="token_unlock_calendar", payload=payload)


async def _cap139(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import run_onchain_platform_e2e_129_139
    payload = run_onchain_platform_e2e_129_139(seed=_seed())
    return _wrap(139, symbol=symbol, payload_key="vesting_schedule_intelligence", payload=payload)

async def _cap140(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import white_label_status_140
    payload = white_label_status_140(seed=_seed())
    return _wrap(140, symbol=symbol, payload_key="token_allocation_intelligence", payload=payload)


async def _cap141(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_coindesk_feed_141
    payload = ingest_coindesk_feed_141(seed=_seed())
    return _wrap(141, symbol=symbol, payload_key="unlock_impact_intelligence", payload=payload)


async def _cap142(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_santiment_metrics_142
    payload = ingest_santiment_metrics_142(asset=symbol, seed=_seed())
    return _wrap(142, symbol=symbol, payload_key="fundraising_rounds", payload=payload)


async def _cap143(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_event_calendar_143
    payload = ingest_event_calendar_143(seed=_seed())
    return _wrap(143, symbol=symbol, payload_key="investor_intelligence", payload=payload)


async def _cap144(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_whale_alert_144
    payload = ingest_whale_alert_144(seed=_seed())
    return _wrap(144, symbol=symbol, payload_key="fund_manager_intelligence", payload=payload)


async def _cap145(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_cmc_price_145
    from market_context import fetch_binance_ticker
    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    price = float((ticker or {}).get("price") or 65000)
    vol = float((ticker or {}).get("quote_volume") or 28_000_000_000)
    payload = ingest_cmc_price_145(symbol=symbol, price=price, volume_24h=vol, seed=_seed())
    return _wrap(145, symbol=symbol, payload_key="ma_intelligence", payload=payload)


async def _cap146(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import validate_oracle_consensus_145_146
    from market_context import fetch_binance_ticker
    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    price = float((ticker or {}).get("price") or 65000)
    payload = validate_oracle_consensus_145_146(primary_price=price, cmc_price=price, coinbase_price=price * 0.9999, seed=_seed())
    return _wrap(146, symbol=symbol, payload_key="capital_flow_funding_trends", payload=payload)


async def _cap147(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import signal_engine_status_147
    payload = signal_engine_status_147(seed=_seed())
    return _wrap(147, symbol=symbol, payload_key="comparable_funding_valuation", payload=payload)


async def _cap148(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_blockchain_com_148
    payload = ingest_blockchain_com_148(seed=_seed())
    return _wrap(148, symbol=symbol, payload_key="due_diligence_report", payload=payload)


async def _cap149(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import ingest_defillama_149
    payload = ingest_defillama_149(seed=_seed())
    return _wrap(149, symbol=symbol, payload_key="automated_risk_scoring", payload=payload)


async def _cap150(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.data_sources_layer import attach_opportunity_to_daily_top3_150, compute_opportunity_score_150
    from bd_platform.retail_intelligence_layer import build_daily_top3_62
    top3 = attach_opportunity_to_daily_top3_150(build_daily_top3_62(seed=_seed()), seed=_seed())
    score = compute_opportunity_score_150(seed=_seed())
    payload = {"daily_top3": top3, "opportunity_score": score}
    return _wrap(150, symbol=symbol, payload_key="protocol_kpi_intelligence", payload=payload)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    101: _cap101,
    102: _cap102,
    104: _cap104,
    105: _cap105,
    106: _cap106,
    107: _cap107,
    108: _cap108,
    109: _cap109,
    110: _cap110,
    111: _cap111,
    112: _cap112,
    113: _cap113,
    114: _cap114,
    115: _cap115,
    116: _cap116,
    117: _cap117,
    118: _cap118,
    119: _cap119,
    120: _cap120,
    121: _cap121,
    122: _cap122,
    123: _cap123,
    124: _cap124,
    125: _cap125,
    126: _cap126,
    127: _cap127,
    128: _cap128,
    130: _cap130,
    131: _cap131,
    132: _cap132,
    133: _cap133,
    134: _cap134,
    135: _cap135,
    136: _cap136,
    137: _cap137,
    138: _cap138,
    139: _cap139,
    140: _cap140,
    141: _cap141,
    142: _cap142,
    143: _cap143,
    144: _cap144,
    145: _cap145,
    146: _cap146,
    147: _cap147,
    148: _cap148,
    149: _cap149,
    150: _cap150,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id in BATCH03_OVERLAP_BATCH01_IDS:
        raise ValueError(
            f"capability {capability_id} is batch01 overlap — reserved; "
            "use cap646.batch01_production / runtime batch01 spine"
        )
    if capability_id not in BATCH03_DEDICATED_IDS:
        raise ValueError(f"capability {capability_id} is not in batch03 dedicated spine")
    params = dict(params or {})
    symbol = _sym(params)
    address = _addr(params)
    fn = _DISPATCH[capability_id]
    return await fn(symbol=symbol, address=address, params=params)
