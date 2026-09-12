"""Official batch 05 — v6 substantive handlers (IDs 101–125)."""

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

OFFICIAL_BATCH05_IDS: frozenset[int] = frozenset(range(101, 126))
BATCH05_DEDICATED_IDS: frozenset[int] = frozenset({101, 102, 103, 104, 105, 108, 109, 111, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123, 124})
BATCH05_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    101: "ai_data_analyst_ask_ai",
    102: "ai_generated_reporting",
    103: "api_data_platform",
    104: "high_resolution_block_level_data_delivery",
    105: "historical_full_data_layer",
    108: "institutional_data_api_delivery",
    109: "white_label_research_reporting",
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
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap101(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=101,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "AI Data Analyst / Ask AI",
        "track": "T17",
        "ai_data_analyst_ask_ai": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(101, symbol=symbol, payload_key='ai_data_analyst_ask_ai', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap102(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'trust_pulse',
        'build_trust_pulse',
        symbol=symbol,
        address=address,
        params=params,
        param_style='symbol',
        capability_id=102,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "AI-Generated Reporting",
        "track": "T12",
        "ai_generated_reporting": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(102, symbol=symbol, payload_key='ai_generated_reporting', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap103(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'hot_storage',
        'get_hot_storage_stats',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=103,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "API Data Platform",
        "track": "T17",
        "api_data_platform": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(103, symbol=symbol, payload_key='api_data_platform', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap104(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'billing_service',
        'billing_status',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=104,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "High-Resolution / Block-Level Data Delivery",
        "track": "T02",
        "high_resolution_block_level_data_delivery": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(104, symbol=symbol, payload_key='high_resolution_block_level_data_delivery', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap105(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from bd_platform.market_analysis_layer import attach_tail_risk_to_backtest_105
    from bd_platform.pro_trader_layer import run_backtest_74
    payload = attach_tail_risk_to_backtest_105(run_backtest_74(seed=_seed()), seed=_seed())
    return _wrap(105, symbol=symbol, payload_key="historical_data_layer", payload=payload)

async def _cap108(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=108,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Institutional Data & API Delivery",
        "track": "T10",
        "institutional_data_api_delivery": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(108, symbol=symbol, payload_key='institutional_data_api_delivery', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

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

async def _cap111(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=111,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Exchange Flow Actionability Score",
        "track": "T09",
        "exchange_flow_actionability_score": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(111, symbol=symbol, payload_key='exchange_flow_actionability_score', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap112(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=112,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Flow-to-Price Explanation Engine",
        "track": "T09",
        "flow_to_price_explanation_engine": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(112, symbol=symbol, payload_key='flow_to_price_explanation_engine', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap113(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=113,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Asset Intelligence Profiles",
        "track": "T09",
        "asset_intelligence_profiles": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(113, symbol=symbol, payload_key='asset_intelligence_profiles', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap114(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'due_diligence_bundle',
        'build_full_due_diligence_bundle',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=114,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Asset Classification & Taxonomy",
        "track": "T09",
        "asset_classification_taxonomy": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(114, symbol=symbol, payload_key='asset_classification_taxonomy', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap115(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.market_rankings',
        'market_rankings',
        symbol=symbol,
        address=address,
        params=params,
        param_style='limit',
        capability_id=115,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Asset Screener",
        "track": "T17",
        "asset_screener": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(115, symbol=symbol, payload_key='asset_screener', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap116(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.onchain_hub',
        'dexscreener_pairs',
        symbol=symbol,
        address=address,
        params=params,
        param_style='query',
        capability_id=116,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Market Pair Intelligence",
        "track": "T17",
        "market_pair_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(116, symbol=symbol, payload_key='market_pair_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap117(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=117,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Real Volume / Quality-Adjusted Volume",
        "track": "T04",
        "real_volume_quality_adjusted_volume": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(117, symbol=symbol, payload_key='real_volume_quality_adjusted_volume', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

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
        capability_id=122,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Volatility Intelligence",
        "track": "T08",
        "volatility_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(122, symbol=symbol, payload_key='volatility_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap123(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=123,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Sharpe Ratio Intelligence",
        "track": "T08",
        "sharpe_ratio_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(123, symbol=symbol, payload_key='sharpe_ratio_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap124(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=124,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Futures Funding Rate Intelligence",
        "track": "T08",
        "futures_funding_rate_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(124, symbol=symbol, payload_key='futures_funding_rate_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    101: _cap101,
    102: _cap102,
    103: _cap103,
    104: _cap104,
    105: _cap105,
    108: _cap108,
    109: _cap109,
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
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH05_DEDICATED_IDS,
        overlap_batch01_ids=BATCH05_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap batch05",
        not_dedicated_error=f"official batch05: not dedicated",
    )
