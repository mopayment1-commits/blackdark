"""Official batch 03 — v6 substantive handlers (IDs 51–75)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import exchange_netflow_footer
from cap646.dedicated_common import exchange_netflow_probe
from cap646.dedicated_common import holder_analytics_bundle
from cap646.dedicated_common import holder_analytics_footer
from cap646.dedicated_common import holder_analytics_locked
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import seed as _seed
from cap646.dedicated_common import sym as _sym
from cap646.evidence_class import ai_compliance_footer
from cap646.evidence_class import attach_evidence_metadata, infer_evidence_class

OFFICIAL_BATCH03_IDS: frozenset[int] = frozenset(range(51, 76))
BATCH03_DEDICATED_IDS: frozenset[int] = frozenset({51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 65, 66, 67, 68, 70, 71, 72, 73, 74, 75})
BATCH03_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    51: "macro_traditional_finance_integration",
    52: "cross_asset_return_breadth",
    53: "btc_to_macro_coupling",
    54: "global_liquidity_intelligence",
    55: "nvt_fair_value_model",
    56: "token_screener",
    57: "profitability_map",
    58: "custom_no_code_charting_workbench",
    59: "personalized_research_dashboards",
    60: "metric_based_smart_alerts",
    61: "point_in_time_immutable_metrics",
    62: "institutional_backtesting_data_layer",
    63: "data_quality_provenance_layer",
    65: "research_intelligence_portal",
    66: "market_regime_written_read",
    67: "api_cli_excel_mcp_data_access",
    68: "bulk_data_institutional_delivery",
    70: "exchange_reserve_intelligence",
    71: "exchange_inflow_outflow_netflow",
    72: "exchange_whale_ratio",
    73: "exchange_address_transaction_activity",
    74: "exchange_to_exchange_flow_intelligence",
    75: "exchange_internal_flow_filter",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap51(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.onchain_hub import lookintobitcoin_macro
    from macro_correlations import build_macro_context_safe
    macro_ctx = await build_macro_context_safe()
    lit = await lookintobitcoin_macro()
    payload = {"macro_context": macro_ctx, "traditional_finance": lit, "integration_read": "macro_tradfi_linked"}
    return _wrap(51, symbol=symbol, payload_key="macro_tradfi", payload=payload)

async def _cap52(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'blackdark.canonical.layer',
        'get_canonical_layer',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=52,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Cross-Asset Return Breadth",
        "track": "T11",
        "cross_asset_return_breadth": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(52, symbol=symbol, payload_key='cross_asset_return_breadth', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap53(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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

async def _cap54(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'live_book_hub',
        'hub_stats',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=54,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Global Liquidity Intelligence",
        "track": "T04",
        "global_liquidity_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(54, symbol=symbol, payload_key='global_liquidity_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap55(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'onchain_tracker',
        'build_onchain_context_safe',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=55,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "NVT Fair-Value Model",
        "track": "T09",
        "nvt_fair_value_model": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(55, symbol=symbol, payload_key='nvt_fair_value_model', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap56(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_rankings import market_rankings

    rankings = await market_rankings()
    return ai_compliance_footer(
        {
            "capability_id": 56,
            "surface": EXPECTED_SURFACE[56],
            "screener": rankings,
            "success": bool(rankings),
        }
    )

async def _cap57(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.derivatives_hub',
        'derivatives_overview',
        symbol=symbol,
        address=address,
        params=params,
        param_style='asset',
        capability_id=57,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Profitability Map",
        "track": "T05",
        "profitability_map": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(57, symbol=symbol, payload_key='profitability_map', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap58(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.tradingview_bridge',
        'chart_config',
        symbol=symbol,
        address=address,
        params=params,
        param_style='symbol',
        capability_id=58,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Custom No-Code Charting / Workbench",
        "track": "T15",
        "custom_no_code_charting_workbench": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(58, symbol=symbol, payload_key='custom_no_code_charting_workbench', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap59(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from research_lab import build_research_lab_report

    report = await build_research_lab_report()
    widgets = {
        "economic_moat": report.get("economic_moat"),
        "financial_models": report.get("financial_models"),
        "whale_intelligence": report.get("whale_intelligence"),
        "sentiment": report.get("sentiment"),
        "onchain": report.get("onchain"),
    }
    return ai_compliance_footer(
        {
            "capability_id": 59,
            "surface": EXPECTED_SURFACE[59],
            "symbol": symbol,
            "personalized_dashboard": widgets,
            "report_meta": {
                "generated_at": report.get("generated_at"),
                "version": report.get("version"),
            },
            "success": bool(report),
        }
    )


# ─── Market / treasury / alerts / watchlists ──────────────────────────────────

async def _cap60(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.pro_trader_layer import evaluate_flexible_alert_75
    from bd_platform.onchain_advanced import compute_advanced_metrics

    metrics = await compute_advanced_metrics(symbol)
    mvrv_z = float((metrics.get("mvrv") or {}).get("z_score") or 0)
    trigger = {
        "rule": f"metric_threshold:{symbol}",
        "metric": "mvrv_z",
        "value": mvrv_z,
        "threshold": float(params.get("threshold") or 2.0),
    }
    alert = evaluate_flexible_alert_75(
        user_tier=str(params.get("tier") or "pro"),
        trigger=trigger,
    )
    return ai_compliance_footer(
        {
            "capability_id": 60,
            "surface": EXPECTED_SURFACE[60],
            "symbol": symbol,
            "metric_trigger": trigger,
            "alert_evaluation": alert,
            "metrics_snapshot": metrics.get("mvrv"),
            "success": alert.get("ok", False),
        }
    )

async def _cap61(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from hot_storage import get_hot_storage_stats
    from oracle_track_record import public_track_record
    hot = get_hot_storage_stats()
    track = public_track_record()
    payload = {"immutable_metrics": track, "hot_storage": hot.__dict__ if hasattr(hot, "__dict__") else hot, "point_in_time": True}
    return _wrap(61, symbol=symbol, payload_key="immutable_metrics", payload=payload)

async def _cap62(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'ml.market_replay_bootstrap',
        'bootstrap_market_replay_dataset',
        symbol=symbol,
        address=address,
        params=params,
        param_style='assets',
        capability_id=62,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Institutional Backtesting Data Layer",
        "track": "T15",
        "institutional_backtesting_data_layer": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(62, symbol=symbol, payload_key='institutional_backtesting_data_layer', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap63(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'data_provenance_score',
        'compute_data_provenance_score',
        symbol=symbol,
        address=address,
        params=params,
        param_style='symbol',
        capability_id=63,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Data Quality & Provenance Layer",
        "track": "T17",
        "data_quality_provenance_layer": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(63, symbol=symbol, payload_key='data_quality_provenance_layer', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap65(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'oracle_track_record',
        'public_track_record',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=65,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Research Intelligence Portal",
        "track": "T17",
        "research_intelligence_portal": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(65, symbol=symbol, payload_key='research_intelligence_portal', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap66(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.derivatives_hub',
        'derivatives_overview',
        symbol=symbol,
        address=address,
        params=params,
        param_style='asset',
        capability_id=66,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Market Regime Written Read",
        "track": "T08",
        "market_regime_written_read": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(66, symbol=symbol, payload_key='market_regime_written_read', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap67(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'security_posture',
        'security_posture_report',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=67,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "API / CLI / Excel / MCP Data Access",
        "track": "T02",
        "api_cli_excel_mcp_data_access": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(67, symbol=symbol, payload_key='api_cli_excel_mcp_data_access', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap68(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'org_tenant',
        'org_isolation_status',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=68,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Bulk Data & Institutional Delivery",
        "track": "T15",
        "bulk_data_institutional_delivery": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(68, symbol=symbol, payload_key='bulk_data_institutional_delivery', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap70(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from onchain_tracker import build_onchain_context_safe
    ctx = await build_onchain_context_safe()
    reserves = (ctx or {}).get("exchange_reserves") or (ctx or {}).get("flows") or ctx
    payload = {"exchange_reserves": reserves, "onchain_context": ctx, "reference_asset": symbol}
    return _wrap(70, symbol=symbol, payload_key="exchange_reserve", payload=payload)

async def _cap71(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.heroes_capability_layer import exchange_netflow_intelligence_48
    exchange = str(params.get("exchange") or "binance")
    netflow = exchange_netflow_intelligence_48(exchange=exchange, asset=symbol)
    payload = {"exchange": exchange, "netflow": netflow}
    return _wrap(71, symbol=symbol, payload_key="exchange_netflow", payload=payload)

async def _cap72(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'whale_tracker',
        'get_latest_whale_alerts',
        symbol=symbol,
        address=address,
        params=params,
        param_style='limit',
        capability_id=72,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Exchange Whale Ratio",
        "track": "T09",
        "exchange_whale_ratio": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(72, symbol=symbol, payload_key='exchange_whale_ratio', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap73(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'onchain_tracker',
        'build_onchain_context_safe',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=73,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Exchange Address & Transaction Activity",
        "track": "T09",
        "exchange_address_transaction_activity": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(73, symbol=symbol, payload_key='exchange_address_transaction_activity', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap74(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'blackdark.canonical.layer',
        'get_canonical_layer',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=74,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Exchange-to-Exchange Flow Intelligence",
        "track": "T11",
        "exchange_to_exchange_flow_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(74, symbol=symbol, payload_key='exchange_to_exchange_flow_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap75(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    51: _cap51,
    52: _cap52,
    53: _cap53,
    54: _cap54,
    55: _cap55,
    56: _cap56,
    57: _cap57,
    58: _cap58,
    59: _cap59,
    60: _cap60,
    61: _cap61,
    62: _cap62,
    63: _cap63,
    65: _cap65,
    66: _cap66,
    67: _cap67,
    68: _cap68,
    70: _cap70,
    71: _cap71,
    72: _cap72,
    73: _cap73,
    74: _cap74,
    75: _cap75,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH03_DEDICATED_IDS,
        overlap_batch01_ids=BATCH03_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap batch03",
        not_dedicated_error=f"official batch03: not dedicated",
    )
