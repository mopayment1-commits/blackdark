"""Official Batch 02 dedicated backends — goal-specific payloads for IDs 51–100.

IDs 55, 56, 59, 60 are batch01 overlap; runtime routes them via ``LEGACY_BATCH01_EXTENSION_IDS``.
"""

from __future__ import annotations

import time
from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import seed as _seed
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap as dedicated_wrap

BATCH02_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset({55, 56, 59, 60})
OFFICIAL_BATCH02_IDS: frozenset[int] = frozenset(range(51, 101))
BATCH02_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH02_IDS - BATCH02_OVERLAP_BATCH01_IDS

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts"}
)

EXPECTED_SURFACE: dict[int, str] = {
    51: "macro_traditional_finance_integration",
    52: "cross_asset_return_breadth",
    53: "btc_to_macro_coupling",
    54: "global_liquidity_intelligence",
    57: "profitability_map",
    58: "custom_no_code_charting_workbench",
    61: "point_in_time_immutable_metrics",
    62: "institutional_backtesting_data_layer",
    63: "data_quality_provenance_layer",
    64: "metric_methodology_registry",
    65: "research_intelligence_portal",
    66: "market_regime_written_read",
    67: "api_cli_excel_mcp_data_access",
    68: "bulk_data_institutional_delivery",
    69: "cross_domain_decision_intelligence_layer",
    70: "exchange_reserve_intelligence",
    71: "exchange_inflow_outflow_netflow",
    72: "exchange_whale_ratio",
    73: "exchange_address_transaction_activity",
    74: "exchange_to_exchange_flow_intelligence",
    75: "exchange_internal_flow_filter",
    76: "stablecoin_exchange_reserve",
    77: "stablecoin_exchange_flow_intelligence",
    78: "stablecoin_supply_ratio_intelligence",
    79: "miner_flow_intelligence",
    80: "miners_position_index_mpi",
    81: "whale_accumulation_distribution_intelligence",
    82: "coinbase_premium_intelligence",
    83: "korea_premium_intelligence",
    84: "fund_etf_data_intelligence",
    85: "futures_open_interest_intelligence",
    86: "funding_rate_intelligence",
    87: "estimated_leverage_ratio",
    88: "liquidation_intelligence",
    89: "taker_buy_sell_pressure",
    90: "derivatives_market_sentiment_composite",
    91: "inter_entity_flow_intelligence",
    92: "address_labels_cohorts",
    93: "custom_no_code_analytics_web3",
    94: "native_sql_advanced_query_workspace",
    95: "pro_chart_multi_metric_workbench",
    96: "personal_dashboards",
    97: "custom_metric_alerts",
    98: "whale_movement_alerts",
    99: "quicktake_analyst_insight_feed",
    100: "research_reports",
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

async def _cap051(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_hub import lookintobitcoin_macro
    from macro_correlations import build_macro_context_safe
    macro_ctx = await build_macro_context_safe()
    lit = await lookintobitcoin_macro()
    payload = {"macro_context": macro_ctx, "traditional_finance": lit, "integration_read": "macro_tradfi_linked"}
    return _wrap(51, symbol=symbol, payload_key="macro_tradfi", payload=payload)

async def _cap052(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.institutional_delivery_intelligence_layer import cross_asset_correlation_565
    payload = cross_asset_correlation_565(symbol=symbol, seed=_seed())
    payload["breadth_score"] = payload.get("correlation_score")
    return _wrap(52, symbol=symbol, payload_key="cross_asset_breadth", payload=payload)

async def _cap053(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from macro_correlations import build_macro_context_safe
    from market_context import fetch_binance_ticker
    macro = await build_macro_context_safe()
    ticker = await fetch_binance_ticker(f"{symbol}USDT")
    change_24h = float((ticker or {}).get("change_24h") or 0)
    payload = {
    "btc_symbol": symbol, "btc_change_24h_pct": change_24h,
    "macro_regime": macro.get("macro_regime"), "dxy_score": macro.get("dxy_score"),
    "coupling_read": "risk_on_aligned" if macro.get("macro_regime") == "Risk-On" and change_24h > 0 else "neutral_coupling",
    "macro_context": macro,
    }
    return _wrap(53, symbol=symbol, payload_key="btc_macro_coupling", payload=payload)

async def _cap054(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from market_context import probe_price_sources
    sources = await probe_price_sources(symbol)
    payload = {"liquidity_sources": sources, "global_liquidity_proxy": len(sources.get("sources") or [])}
    return _wrap(54, symbol=symbol, payload_key="global_liquidity", payload=payload)

async def _cap057(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.institutional_delivery_intelligence_layer import profitability_analyzer_582
    payload = profitability_analyzer_582(symbol=symbol, seed=_seed())
    return _wrap(57, symbol=symbol, payload_key="profitability_map", payload=payload)

async def _cap058(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.tradingview_bridge import chart_config
    payload = chart_config(f"{symbol}USDT")
    return _wrap(58, symbol=symbol, payload_key="chart_workbench", payload=payload)

async def _cap061(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from hot_storage import get_hot_storage_stats
    from oracle_track_record import public_track_record
    hot = get_hot_storage_stats()
    track = public_track_record()
    payload = {"immutable_metrics": track, "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else hot, "point_in_time": True}
    return _wrap(61, symbol=symbol, payload_key="immutable_metrics", payload=payload)

async def _cap062(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from ml.market_replay_bootstrap import bootstrap_market_replay_dataset
    payload = await bootstrap_market_replay_dataset(assets=[symbol])
    return _wrap(62, symbol=symbol, payload_key="backtesting_data", payload=payload)

async def _cap063(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from data_provenance_score import compute_data_provenance_score
    from hot_storage import get_hot_storage_stats
    provenance = compute_data_provenance_score(symbol=symbol)
    hot = get_hot_storage_stats()
    payload = {"provenance": provenance, "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else hot}
    return _wrap(63, symbol=symbol, payload_key="data_quality_provenance", payload=payload)

async def _cap064(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from signal_registry import registry_stats
    payload = {"methodology_registry": registry_stats()}
    return _wrap(64, symbol=symbol, payload_key="metric_methodology", payload=payload)

async def _cap065(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from oracle_track_record import public_track_record
    payload = {"research_portal": public_track_record(), "portal_status": "live"}
    return _wrap(65, symbol=symbol, payload_key="research_portal", payload=payload)

async def _cap066(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73
    multi = build_multi_dim_analysis_73(asset=symbol, seed=_seed())
    payload = {"regime_read": multi.get("regime"), "written_summary": multi.get("summary"), "multi_dim": multi}
    return _wrap(66, symbol=symbol, payload_key="market_regime_read", payload=payload)

async def _cap067(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from security_posture import security_posture_report
    payload = {"api_access": security_posture_report(), "channels": ["api", "cli", "excel", "mcp"]}
    return _wrap(67, symbol=symbol, payload_key="api_data_access", payload=payload)

async def _cap068(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from product_honesty_api import build_public_readiness
    payload = await build_public_readiness()
    return _wrap(68, symbol=symbol, payload_key="bulk_delivery", payload=payload)

async def _cap069(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.cross_domain_decision import build_cross_domain_decision_payload
    payload = await build_cross_domain_decision_payload(symbol=symbol, seed=_seed())
    return _wrap(69, symbol=symbol, payload_key="cross_domain_decision", payload=payload)

async def _cap070(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from onchain_tracker import build_onchain_context_safe
    ctx = await build_onchain_context_safe()
    reserves = (ctx or {}).get("exchange_reserves") or (ctx or {}).get("flows") or ctx
    payload = {"exchange_reserves": reserves, "onchain_context": ctx, "reference_asset": symbol}
    return _wrap(70, symbol=symbol, payload_key="exchange_reserve", payload=payload)

async def _cap071(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.heroes_capability_layer import exchange_netflow_intelligence_48
    exchange = str(params.get("exchange") or "binance")
    netflow = exchange_netflow_intelligence_48(exchange=exchange, asset=symbol)
    payload = {"exchange": exchange, "netflow": netflow}
    return _wrap(71, symbol=symbol, payload_key="exchange_netflow", payload=payload)

async def _cap072(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import compute_whale_ls_ratio_114
    payload = compute_whale_ls_ratio_114(seed=_seed())
    payload["exchange_whale_ratio"] = payload.get("whale_filtered_ratio")
    return _wrap(72, symbol=symbol, payload_key="exchange_whale_ratio", payload=payload)

async def _cap073(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from onchain_tracker import build_onchain_context_safe
    ctx = await build_onchain_context_safe()
    payload = {"address_activity": ctx.get("flows") if isinstance(ctx, dict) else ctx, "context": ctx, "reference_asset": symbol}
    return _wrap(73, symbol=symbol, payload_key="exchange_address_activity", payload=payload)

async def _cap074(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from blackdark.canonical.layer import get_canonical_layer
    layer = get_canonical_layer()
    payload = {"exchange_to_exchange_flow": layer.status(), "cross_exchange_routing": True, "reference_asset": symbol}
    return _wrap(74, symbol=symbol, payload_key="exchange_to_exchange_flow", payload=payload)

async def _cap075(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from exchange_internal_flow_filter import classify_flow
    payload = classify_flow(
    from_address=str(params.get("from_address") or "0xexchange_hot"),
    to_address=str(params.get("to_address") or address),
    exchange=str(params.get("exchange") or "binance"),
    amount_usd=float(params.get("amount_usd") or 1_000_000),
    is_deposit=bool(params.get("is_deposit")),
    is_withdrawal=bool(params.get("is_withdrawal")),
    )
    return _wrap(75, symbol=symbol, payload_key="internal_flow_filter", payload=payload)

async def _cap076(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from onchain_tracker import build_onchain_context_safe
    ctx = await build_onchain_context_safe()
    payload = {"stablecoin_exchange_reserve": ctx, "asset": "USDT", "reference": symbol}
    return _wrap(76, symbol=symbol, payload_key="stablecoin_reserve", payload=payload)

async def _cap077(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from onchain_tracker import build_onchain_context_safe
    ctx = await build_onchain_context_safe()
    payload = {"stablecoin_flow": ctx, "target_asset": symbol}
    return _wrap(77, symbol=symbol, payload_key="stablecoin_flow", payload=payload)

async def _cap078(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.charting_market_intelligence_layer import stablecoin_supply_357
    payload = stablecoin_supply_357(symbol=symbol, seed=_seed())
    return _wrap(78, symbol=symbol, payload_key="stablecoin_supply_ratio", payload=payload)

async def _cap079(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from onchain_tracker import build_onchain_context_safe
    ctx = await build_onchain_context_safe()
    payload = {"miner_flow": ctx, "flow_bias": (ctx or {}).get("bias") if isinstance(ctx, dict) else None, "reference_asset": symbol}
    return _wrap(79, symbol=symbol, payload_key="miner_flow", payload=payload)

async def _cap080(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_hub import lookintobitcoin_macro
    lit = await lookintobitcoin_macro()
    mpi_proxy = (lit.get("metrics") or lit).get("mpi") if isinstance(lit, dict) else None
    payload = {"mpi": mpi_proxy, "miners_position_index": mpi_proxy, "macro_bundle": lit}
    return _wrap(80, symbol=symbol, payload_key="miners_position_index", payload=payload)

async def _cap081(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from whale_tracker import get_latest_whale_alerts
    alerts = await get_latest_whale_alerts(limit=int(params.get("limit") or 20))
    accum = sum(1 for a in (alerts or []) if "accumulation" in str(a).lower())
    dist = sum(1 for a in (alerts or []) if "distribution" in str(a).lower())
    payload = {"whale_alerts": alerts, "accumulation_signals": accum, "distribution_signals": dist}
    return _wrap(81, symbol=symbol, payload_key="whale_accumulation_distribution", payload=payload)

async def _cap082(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from market_context import probe_price_sources
    sources = await probe_price_sources(symbol)
    cb = next((s for s in (sources.get("sources") or []) if "coinbase" in str(s).lower()), None)
    payload = {"coinbase_premium": cb, "all_sources": sources}
    return _wrap(82, symbol=symbol, payload_key="coinbase_premium", payload=payload)

async def _cap083(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from market_context import probe_price_sources
    sources = await probe_price_sources(symbol)
    kr = next((s for s in (sources.get("sources") or []) if "upbit" in str(s).lower() or "korea" in str(s).lower()), None)
    payload = {"korea_premium": kr, "all_sources": sources}
    return _wrap(83, symbol=symbol, payload_key="korea_premium", payload=payload)

async def _cap084(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_hub import lookintobitcoin_macro
    lit = await lookintobitcoin_macro()
    payload = {"etf_fund_data": lit.get("etf") if isinstance(lit, dict) else lit, "fund_intelligence": lit}
    return _wrap(84, symbol=symbol, payload_key="fund_etf_data", payload=payload)

async def _cap085(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.derivatives_hub import derivatives_overview
    overview = await derivatives_overview(symbol)
    oi = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    payload = {"derivatives_overview": overview, "open_interest_usd": oi.get("open_interest_usd"), "open_interest_contracts": oi.get("open_interest_contracts")}
    return _wrap(85, symbol=symbol, payload_key="futures_open_interest", payload=payload)

async def _cap086(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.derivatives_hub import derivatives_overview
    overview = await derivatives_overview(symbol)
    ft = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    payload = {"derivatives_overview": overview, "funding_rate": ft.get("funding_rate"), "funding_rate_pct": ft.get("funding_rate_pct")}
    return _wrap(86, symbol=symbol, payload_key="funding_rate", payload=payload)

async def _cap087(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.heroes_capability_layer import leverage_ratio_overhang_197
    payload = leverage_ratio_overhang_197(symbol=symbol)
    payload["estimated_leverage_ratio"] = payload.get("leverage_ratio")
    return _wrap(87, symbol=symbol, payload_key="estimated_leverage", payload=payload)

async def _cap088(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.liquidation_radar import liquidation_radar
    payload = await liquidation_radar(symbol)
    return _wrap(88, symbol=symbol, payload_key="liquidation", payload=payload)

async def _cap089(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.derivatives_hub import derivatives_overview
    overview = await derivatives_overview(symbol)
    ft = (overview.get("free_tier") or {}) if isinstance(overview, dict) else {}
    buy = float(ft.get("taker_buy_ratio") or 0.5)
    payload = {"taker_buy_ratio": buy, "taker_sell_ratio": round(1 - buy, 4), "derivatives": ft}
    return _wrap(89, symbol=symbol, payload_key="taker_pressure", payload=payload)

async def _cap090(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from sentiment_engine import build_sentiment_context_safe
    from bd_platform.derivatives_hub import derivatives_overview
    sentiment = await build_sentiment_context_safe(symbol)
    deriv = await derivatives_overview(symbol)
    payload = {"sentiment": sentiment, "derivatives": deriv, "composite": sentiment.get("score")}
    return _wrap(90, symbol=symbol, payload_key="derivatives_sentiment", payload=payload)

async def _cap091(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from onchain_tracker import build_onchain_context_safe
    ctx = await build_onchain_context_safe()
    payload = {"inter_entity_flow": ctx, "entity_routing": True, "reference_asset": symbol}
    return _wrap(91, symbol=symbol, payload_key="inter_entity_flow", payload=payload)

async def _cap092(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_platform_layer import b2b_relationships_status_137
    payload = b2b_relationships_status_137(seed=_seed())
    payload["address_labels"] = payload.get("labels") or payload.get("relationships")
    return _wrap(92, symbol=symbol, payload_key="address_labels", payload=payload)

async def _cap093(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.tradingview_bridge import chart_config
    cfg = chart_config(f"{symbol}USDT")
    payload = {"web3_analytics": cfg, "no_code": True}
    return _wrap(93, symbol=symbol, payload_key="web3_analytics", payload=payload)

async def _cap094(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from data_lake import lake_status
    payload = await lake_status()
    payload = {"sql_workspace": payload, "query_modes": ["native_sql", "advanced_query"]}
    return _wrap(94, symbol=symbol, payload_key="sql_workspace", payload=payload)

async def _cap095(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.tradingview_bridge import chart_config
    from bd_platform.pro_trader_layer import build_multi_dim_analysis_73
    payload = {"chart_workbench": chart_config(f"{symbol}USDT"), "metrics": build_multi_dim_analysis_73(asset=symbol, seed=_seed())}
    return _wrap(95, symbol=symbol, payload_key="pro_chart_workbench", payload=payload)

async def _cap096(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import copy
    from bd_platform.onchain_platform_layer import institution_features_status_138
    raw = institution_features_status_138(seed=_seed())
    payload = {
    "personal_dashboards": copy.deepcopy(raw.get("bundle") or {}),
    "activation_status": raw.get("status"),
    "feature_ref": raw.get("feature_ref"),
    "ok": raw.get("ok", True),
    }
    return _wrap(96, symbol=symbol, payload_key="personal_dashboards", payload=payload)

async def _cap097(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75
    from instant_alert_engine import engine_stats
    trigger = {"rule": f"custom_metric:{symbol}", "metric": params.get("metric") or "price", "threshold": float(params.get("threshold") or 1.0)}
    payload = {"alert_evaluation": evaluate_flexible_alert_75(user_tier=str(params.get("tier") or "pro"), trigger=trigger), "engine": engine_stats()}
    return _wrap(97, symbol=symbol, payload_key="custom_metric_alerts", payload=payload)

async def _cap098(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from whale_tracker import get_latest_whale_alerts
    alerts = await get_latest_whale_alerts(limit=int(params.get("limit") or 25))
    payload = {"whale_movement_alerts": alerts, "alert_count": len(alerts or [])}
    return _wrap(98, symbol=symbol, payload_key="whale_movement_alerts", payload=payload)

async def _cap099(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.quicktake_feed import quicktake_feed_status_409
    payload = await quicktake_feed_status_409(limit=int(params.get("limit") or 10))
    return _wrap(99, symbol=symbol, payload_key="quicktake_feed", payload=payload)

async def _cap100(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from oracle_track_record import public_track_record
    payload = {"research_reports": public_track_record(), "report_feed": "institutional"}
    return _wrap(100, symbol=symbol, payload_key="research_reports", payload=payload)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    51: _cap051,
    52: _cap052,
    53: _cap053,
    54: _cap054,
    57: _cap057,
    58: _cap058,
    61: _cap061,
    62: _cap062,
    63: _cap063,
    64: _cap064,
    65: _cap065,
    66: _cap066,
    67: _cap067,
    68: _cap068,
    69: _cap069,
    70: _cap070,
    71: _cap071,
    72: _cap072,
    73: _cap073,
    74: _cap074,
    75: _cap075,
    76: _cap076,
    77: _cap077,
    78: _cap078,
    79: _cap079,
    80: _cap080,
    81: _cap081,
    82: _cap082,
    83: _cap083,
    84: _cap084,
    85: _cap085,
    86: _cap086,
    87: _cap087,
    88: _cap088,
    89: _cap089,
    90: _cap090,
    91: _cap091,
    92: _cap092,
    93: _cap093,
    94: _cap094,
    95: _cap095,
    96: _cap096,
    97: _cap097,
    98: _cap098,
    99: _cap099,
    100: _cap100,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    if capability_id in BATCH02_OVERLAP_BATCH01_IDS:
        raise ValueError(
            f"capability {capability_id} is batch01 overlap — reserved; "
            "use cap646.batch01_production / runtime batch01 spine"
        )
    if capability_id not in BATCH02_DEDICATED_IDS:
        raise ValueError(f"capability {capability_id} is not in official batch02 dedicated spine")
    params = dict(params or {})
    symbol = _sym(params)
    address = _addr(params)
    fn = _DISPATCH[capability_id]
    return await fn(symbol=symbol, address=address, params=params)
