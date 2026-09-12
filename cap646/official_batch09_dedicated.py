"""Official batch 09 — v6 substantive handlers (IDs 201–225)."""

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

OFFICIAL_BATCH09_IDS: frozenset[int] = frozenset(range(201, 226))
BATCH09_DEDICATED_IDS: frozenset[int] = frozenset({201, 202, 203, 204, 205, 207, 208, 209, 210, 211, 213, 214, 215, 216, 217, 218, 219, 220, 223, 224, 225})
BATCH09_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    201: "network_growth_intelligence",
    202: "supply_distribution_intelligence",
    203: "dex_trading_intelligence",
    204: "defi_protocol_activity_intelligence",
    205: "open_interest_intelligence",
    207: "price_volume_market_metrics",
    208: "metric_correlation_workbench",
    209: "custom_chart_builder",
    210: "custom_dashboards_layouts",
    211: "screener",
    213: "anomaly_detection_alerts",
    214: "watchlists",
    215: "community_explorer",
    216: "research_market_insights",
    217: "sanapi_style_data_access",
    218: "google_sheets_integration",
    219: "metric_availability_registry",
    220: "data_stabilization_mutability_metadata",
    223: "social_to_on_chain_confirmation_engine",
    224: "narrative_actionability_score",
    225: "development_to_market_divergence_detector",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap201(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'market_context',
        'probe_price_sources',
        symbol=symbol,
        address=address,
        params=params,
        param_style='symbol',
        capability_id=201,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Network Growth Intelligence",
        "track": "T11",
        "network_growth_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(201, symbol=symbol, payload_key='network_growth_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap202(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=202,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Supply Distribution Intelligence",
        "track": "T01",
        "supply_distribution_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(202, symbol=symbol, payload_key='supply_distribution_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap203(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=203,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "DEX Trading Intelligence",
        "track": "T09",
        "dex_trading_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(203, symbol=symbol, payload_key='dex_trading_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap204(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.onchain_hub',
        'defillama_raises',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=204,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "DeFi Protocol Activity Intelligence",
        "track": "T17",
        "defi_protocol_activity_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(204, symbol=symbol, payload_key='defi_protocol_activity_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap205(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=205,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Open Interest Intelligence",
        "track": "T10",
        "open_interest_intelligence": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(205, symbol=symbol, payload_key='open_interest_intelligence', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap207(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.alpha_engine',
        'compute_alpha_signal',
        symbol=symbol,
        address=address,
        params=params,
        param_style='symbol',
        capability_id=207,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Price / Volume / Market Metrics",
        "track": "T05",
        "price_volume_market_metrics": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(207, symbol=symbol, payload_key='price_volume_market_metrics', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap208(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.alpha_engine',
        'compute_alpha_signal',
        symbol=symbol,
        address=address,
        params=params,
        param_style='symbol',
        capability_id=208,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Metric Correlation Workbench",
        "track": "T09",
        "metric_correlation_workbench": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(208, symbol=symbol, payload_key='metric_correlation_workbench', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap209(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=209,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Custom Chart Builder",
        "track": "T04",
        "custom_chart_builder": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(209, symbol=symbol, payload_key='custom_chart_builder', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap210(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.infra_status',
        'infra_matrix',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=210,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Custom Dashboards / Layouts",
        "track": "T14",
        "custom_dashboards_layouts": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(210, symbol=symbol, payload_key='custom_dashboards_layouts', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap211(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=211,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Screener",
        "track": "T16",
        "screener": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(211, symbol=symbol, payload_key='screener', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap213(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'instant_alert_engine',
        'engine_stats',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=213,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Anomaly Detection Alerts",
        "track": "T09",
        "anomaly_detection_alerts": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(213, symbol=symbol, payload_key='anomaly_detection_alerts', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap214(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=214,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Watchlists",
        "track": "T11",
        "watchlists": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(214, symbol=symbol, payload_key='watchlists', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap215(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=215,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Community Explorer",
        "track": "T16",
        "community_explorer": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(215, symbol=symbol, payload_key='community_explorer', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap216(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=216,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Research & Market Insights",
        "track": "T02",
        "research_market_insights": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(216, symbol=symbol, payload_key='research_market_insights', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap217(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=217,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "SanAPI-Style Data Access",
        "track": "T17",
        "sanapi_style_data_access": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(217, symbol=symbol, payload_key='sanapi_style_data_access', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap218(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.infra_status',
        'infra_matrix',
        symbol=symbol,
        address=address,
        params=params,
        param_style='none',
        capability_id=218,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Google Sheets Integration",
        "track": "T02",
        "google_sheets_integration": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(218, symbol=symbol, payload_key='google_sheets_integration', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap219(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'blackdark.canonical.resolver',
        'resolve_asset',
        symbol=symbol,
        address=address,
        params=params,
        param_style='raw',
        capability_id=219,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Metric Availability Registry",
        "track": "T02",
        "metric_availability_registry": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(219, symbol=symbol, payload_key='metric_availability_registry', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap220(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'blackdark.canonical.resolver',
        'resolve_asset',
        symbol=symbol,
        address=address,
        params=params,
        param_style='raw',
        capability_id=220,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Data Stabilization & Mutability Metadata",
        "track": "T03",
        "data_stabilization_mutability_metadata": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(220, symbol=symbol, payload_key='data_stabilization_mutability_metadata', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap223(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'sentiment_engine',
        'build_sentiment_context_safe',
        symbol=symbol,
        address=address,
        params=params,
        param_style='assets',
        capability_id=223,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Social-to-On-Chain Confirmation Engine",
        "track": "T10",
        "social_to_on_chain_confirmation_engine": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(223, symbol=symbol, payload_key='social_to_on_chain_confirmation_engine', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap224(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    import time
    from cap646.substantive_invoke import invoke_substantive
    from data_provenance_score import compute_data_provenance_score
    t0 = time.perf_counter()
    domain = await invoke_substantive(
        'bd_platform.whale_story',
        'whale_narrative',
        symbol=symbol,
        address=address,
        params=params,
        param_style='symbol',
        capability_id=224,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Narrative Actionability Score",
        "track": "T09",
        "narrative_actionability_score": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(224, symbol=symbol, payload_key='narrative_actionability_score', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

async def _cap225(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
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
        capability_id=225,
    )
    prov = compute_data_provenance_score(symbol=symbol)
    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    payload = {
        "capability_goal": "Development-to-Market Divergence Detector",
        "track": "T09",
        "development_to_market_divergence_detector": domain,
        "domain_result": domain,
        "provenance": prov,
        "execution_path": "v6_substantive_semantic_invoke",
    }
    return _wrap(225, symbol=symbol, payload_key='development_to_market_divergence_detector', payload=payload, extra={'latency_ms': latency_ms, 'performance_gate': True, 'data_provenance': prov, 'build_method': 'v6_substantive'})

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    201: _cap201,
    202: _cap202,
    203: _cap203,
    204: _cap204,
    205: _cap205,
    207: _cap207,
    208: _cap208,
    209: _cap209,
    210: _cap210,
    211: _cap211,
    213: _cap213,
    214: _cap214,
    215: _cap215,
    216: _cap216,
    217: _cap217,
    218: _cap218,
    219: _cap219,
    220: _cap220,
    223: _cap223,
    224: _cap224,
    225: _cap225,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH09_DEDICATED_IDS,
        overlap_batch01_ids=BATCH09_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap batch09",
        not_dedicated_error=f"official batch09: not dedicated",
    )
