"""Batch 06 prep dedicated backends — IDs 251–300 (Run 015 opening)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.batch06_underlying import invoke_underlying
from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym

BATCH06_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()  # WF-027: zero overlap in 251–300
OFFICIAL_BATCH06_IDS: frozenset[int] = frozenset(range(251, 301))
BATCH06_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH06_IDS

EXPECTED_SURFACE: dict[int, str] = {
    251: 'cross_domain_decision_intelligence',
    252: 'liquidation_heatmap',
    253: 'liquidation_map_levels',
    254: 'real_time_liquidation_events',
    255: 'open_interest_intelligence',
    256: 'funding_rate_intelligence',
    257: 'long_short_ratio_intelligence',
    258: 'top_trader_positioning',
    259: 'futures_basis_intelligence',
    260: 'futures_volume_intelligence',
    261: 'futures_cvd_taker_flow',
    262: 'options_open_interest',
    263: 'options_volume',
    264: 'options_iv_skew',
    265: 'max_pain_gamma_context',
    266: 'spot_market_intelligence',
    267: 'order_book_market_depth',
    268: 'historical_derivatives_data',
    269: 'exchange_comparison',
    270: 'liquidation_cascade_proximity',
    271: 'leverage_pressure_score',
    272: 'api_data_platform',
    273: 'multi_model_liquidation_comparison',
    274: 'derivatives_alerts',
    275: 'cross_domain_decision_intelligence',
    276: 'entity_resolution_engine',
    277: 'address_labeling_system',
    278: 'entity_profiles',
    279: 'transaction_search',
    280: 'portfolio_holdings',
    281: 'balance_history',
    282: 'entity_pnl',
    283: 'exchange_usage_intelligence',
    284: 'top_counterparties',
    285: 'visualizer_network_graph',
    286: 'automated_trace_path_finding',
    287: 'cross_chain_trace',
    288: 'token_top_holders',
    289: 'token_exchange_flows',
    290: 'token_transaction_explorer',
    291: 'custom_dashboards',
    292: 'custom_alerts',
    293: 'private_labels',
    294: 'archive_historical_portfolio_snapshot',
    295: 'ai_market_insights',
    296: 'whale_movement_intelligence',
    297: 'fraud_suspicious_activity_intelligence',
    298: 'api_on_chain_intelligence',
    299: 'cross_entity_decision_intelligence',
    300: 'advanced_multi_asset_charting',
}

_base_wrap = make_wrap_binding(EXPECTED_SURFACE)


def _wrap(
    capability_id: int,
    *,
    symbol: str,
    payload_key: str,
    payload: Any,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Batch06 wrap — BCBS 239 top-level provenance (Run 015)."""
    merged: dict[str, Any] = dict(extra or {})
    if isinstance(payload, dict):
        src = payload.get("data_source") or payload.get("source")
        if src and not merged.get("data_source"):
            merged["data_source"] = src
        ts = payload.get("timestamp") or payload.get("attached_at")
        if ts and not merged.get("timestamp"):
            merged["timestamp"] = ts
    if not merged.get("data_source"):
        merged["data_source"] = f"cap646.batch06_dedicated#cap{capability_id:03d}"
    if not merged.get("timestamp"):
        merged["timestamp"] = datetime.now(UTC).isoformat()
    return _base_wrap(
        capability_id, symbol=symbol, payload_key=payload_key, payload=payload, extra=merged,
    )


async def _cap251(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(251, params={**params, "symbol": symbol})
    return _wrap(251, symbol=symbol, payload_key="cross_domain_decision_intelligence", payload=payload)

async def _cap252(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(252, params={**params, "symbol": symbol})
    return _wrap(252, symbol=symbol, payload_key="liquidation_heatmap", payload=payload)

async def _cap253(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(253, params={**params, "symbol": symbol})
    return _wrap(253, symbol=symbol, payload_key="liquidation_map_levels", payload=payload)

async def _cap254(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(254, params={**params, "symbol": symbol})
    return _wrap(254, symbol=symbol, payload_key="real_time_liquidation_events", payload=payload)

async def _cap255(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(255, params={**params, "symbol": symbol})
    return _wrap(255, symbol=symbol, payload_key="open_interest_intelligence", payload=payload)

async def _cap256(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(256, params={**params, "symbol": symbol})
    return _wrap(256, symbol=symbol, payload_key="funding_rate_intelligence", payload=payload)

async def _cap257(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(257, params={**params, "symbol": symbol})
    return _wrap(257, symbol=symbol, payload_key="long_short_ratio_intelligence", payload=payload)

async def _cap258(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(258, params={**params, "symbol": symbol})
    return _wrap(258, symbol=symbol, payload_key="top_trader_positioning", payload=payload)

async def _cap259(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(259, params={**params, "symbol": symbol})
    return _wrap(259, symbol=symbol, payload_key="futures_basis_intelligence", payload=payload)

async def _cap260(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(260, params={**params, "symbol": symbol})
    return _wrap(260, symbol=symbol, payload_key="futures_volume_intelligence", payload=payload)

async def _cap261(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(261, params={**params, "symbol": symbol})
    return _wrap(261, symbol=symbol, payload_key="futures_cvd_taker_flow", payload=payload)

async def _cap262(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(262, params={**params, "symbol": symbol})
    return _wrap(262, symbol=symbol, payload_key="options_open_interest", payload=payload)

async def _cap263(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(263, params={**params, "symbol": symbol})
    return _wrap(263, symbol=symbol, payload_key="options_volume", payload=payload)

async def _cap264(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(264, params={**params, "symbol": symbol})
    return _wrap(264, symbol=symbol, payload_key="options_iv_skew", payload=payload)

async def _cap265(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(265, params={**params, "symbol": symbol})
    return _wrap(265, symbol=symbol, payload_key="max_pain_gamma_context", payload=payload)

async def _cap266(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(266, params={**params, "symbol": symbol})
    return _wrap(266, symbol=symbol, payload_key="spot_market_intelligence", payload=payload)

async def _cap267(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(267, params={**params, "symbol": symbol})
    return _wrap(267, symbol=symbol, payload_key="order_book_market_depth", payload=payload)

async def _cap268(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(268, params={**params, "symbol": symbol})
    return _wrap(268, symbol=symbol, payload_key="historical_derivatives_data", payload=payload)

async def _cap269(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(269, params={**params, "symbol": symbol})
    return _wrap(269, symbol=symbol, payload_key="exchange_comparison", payload=payload)

async def _cap270(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(270, params={**params, "symbol": symbol})
    return _wrap(270, symbol=symbol, payload_key="liquidation_cascade_proximity", payload=payload)

async def _cap271(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(271, params={**params, "symbol": symbol})
    return _wrap(271, symbol=symbol, payload_key="leverage_pressure_score", payload=payload)

async def _cap272(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(272, params={**params, "symbol": symbol})
    return _wrap(272, symbol=symbol, payload_key="api_data_platform", payload=payload)

async def _cap273(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(273, params={**params, "symbol": symbol})
    return _wrap(273, symbol=symbol, payload_key="multi_model_liquidation_comparison", payload=payload)

async def _cap274(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(274, params={**params, "symbol": symbol})
    return _wrap(274, symbol=symbol, payload_key="derivatives_alerts", payload=payload)

async def _cap275(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(275, params={**params, "symbol": symbol})
    return _wrap(275, symbol=symbol, payload_key="cross_domain_decision_intelligence", payload=payload)

async def _cap276(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(276, params={**params, "symbol": symbol})
    return _wrap(276, symbol=symbol, payload_key="entity_resolution_engine", payload=payload)

async def _cap277(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(277, params={**params, "symbol": symbol})
    return _wrap(277, symbol=symbol, payload_key="address_labeling_system", payload=payload)

async def _cap278(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(278, params={**params, "symbol": symbol})
    return _wrap(278, symbol=symbol, payload_key="entity_profiles", payload=payload)

async def _cap279(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(279, params={**params, "symbol": symbol})
    return _wrap(279, symbol=symbol, payload_key="transaction_search", payload=payload)

async def _cap280(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(280, params={**params, "symbol": symbol})
    return _wrap(280, symbol=symbol, payload_key="portfolio_holdings", payload=payload)

async def _cap281(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(281, params={**params, "symbol": symbol})
    return _wrap(281, symbol=symbol, payload_key="balance_history", payload=payload)

async def _cap282(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(282, params={**params, "symbol": symbol})
    return _wrap(282, symbol=symbol, payload_key="entity_pnl", payload=payload)

async def _cap283(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(283, params={**params, "symbol": symbol})
    return _wrap(283, symbol=symbol, payload_key="exchange_usage_intelligence", payload=payload)

async def _cap284(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(284, params={**params, "symbol": symbol})
    return _wrap(284, symbol=symbol, payload_key="top_counterparties", payload=payload)

async def _cap285(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(285, params={**params, "symbol": symbol})
    return _wrap(285, symbol=symbol, payload_key="visualizer_network_graph", payload=payload)

async def _cap286(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(286, params={**params, "symbol": symbol})
    return _wrap(286, symbol=symbol, payload_key="automated_trace_path_finding", payload=payload)

async def _cap287(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(287, params={**params, "symbol": symbol})
    return _wrap(287, symbol=symbol, payload_key="cross_chain_trace", payload=payload)

async def _cap288(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(288, params={**params, "symbol": symbol})
    return _wrap(288, symbol=symbol, payload_key="token_top_holders", payload=payload)

async def _cap289(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(289, params={**params, "symbol": symbol})
    return _wrap(289, symbol=symbol, payload_key="token_exchange_flows", payload=payload)

async def _cap290(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(290, params={**params, "symbol": symbol})
    return _wrap(290, symbol=symbol, payload_key="token_transaction_explorer", payload=payload)

async def _cap291(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(291, params={**params, "symbol": symbol})
    return _wrap(291, symbol=symbol, payload_key="custom_dashboards", payload=payload)

async def _cap292(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(292, params={**params, "symbol": symbol})
    return _wrap(292, symbol=symbol, payload_key="custom_alerts", payload=payload)

async def _cap293(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(293, params={**params, "symbol": symbol})
    return _wrap(293, symbol=symbol, payload_key="private_labels", payload=payload)

async def _cap294(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(294, params={**params, "symbol": symbol})
    return _wrap(294, symbol=symbol, payload_key="archive_historical_portfolio_snapshot", payload=payload)

async def _cap295(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(295, params={**params, "symbol": symbol})
    return _wrap(295, symbol=symbol, payload_key="ai_market_insights", payload=payload)

async def _cap296(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(296, params={**params, "symbol": symbol})
    return _wrap(296, symbol=symbol, payload_key="whale_movement_intelligence", payload=payload)

async def _cap297(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(297, params={**params, "symbol": symbol})
    return _wrap(297, symbol=symbol, payload_key="fraud_suspicious_activity_intelligence", payload=payload)

async def _cap298(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(298, params={**params, "symbol": symbol})
    return _wrap(298, symbol=symbol, payload_key="api_on_chain_intelligence", payload=payload)

async def _cap299(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(299, params={**params, "symbol": symbol})
    return _wrap(299, symbol=symbol, payload_key="cross_entity_decision_intelligence", payload=payload)

async def _cap300(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(300, params={**params, "symbol": symbol})
    return _wrap(300, symbol=symbol, payload_key="advanced_multi_asset_charting", payload=payload)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    251: _cap251,
    252: _cap252,
    253: _cap253,
    254: _cap254,
    255: _cap255,
    256: _cap256,
    257: _cap257,
    258: _cap258,
    259: _cap259,
    260: _cap260,
    261: _cap261,
    262: _cap262,
    263: _cap263,
    264: _cap264,
    265: _cap265,
    266: _cap266,
    267: _cap267,
    268: _cap268,
    269: _cap269,
    270: _cap270,
    271: _cap271,
    272: _cap272,
    273: _cap273,
    274: _cap274,
    275: _cap275,
    276: _cap276,
    277: _cap277,
    278: _cap278,
    279: _cap279,
    280: _cap280,
    281: _cap281,
    282: _cap282,
    283: _cap283,
    284: _cap284,
    285: _cap285,
    286: _cap286,
    287: _cap287,
    288: _cap288,
    289: _cap289,
    290: _cap290,
    291: _cap291,
    292: _cap292,
    293: _cap293,
    294: _cap294,
    295: _cap295,
    296: _cap296,
    297: _cap297,
    298: _cap298,
    299: _cap299,
    300: _cap300,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH06_DEDICATED_IDS,
        overlap_batch01_ids=BATCH06_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch06: ID in batch01 overlap — CROSS-SPINE-001",
        not_dedicated_error="capability not in batch06 dedicated set",
    )
