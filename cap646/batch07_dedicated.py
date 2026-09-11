"""Batch 07 prep dedicated backends — IDs 301–350 (Run 021)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Awaitable, Callable

from cap646.batch07_underlying import invoke_underlying
from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym

BATCH07_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
OFFICIAL_BATCH07_IDS: frozenset[int] = frozenset(range(301, 351))
BATCH07_DEDICATED_IDS: frozenset[int] = OFFICIAL_BATCH07_IDS

EXPECTED_SURFACE: dict[int, str] = {
    301: 'multi_chart_layouts',
    302: 'technical_indicator_library',
    303: 'custom_indicator_scripting',
    304: 'strategy_backtesting',
    305: 'market_screener',
    306: 'pine_style_screener',
    307: 'smart_alerts',
    308: 'watchlists',
    309: 'economic_calendar',
    310: 'crypto_calendar_events',
    311: 'news_integration',
    312: 'heatmaps',
    313: 'technical_ratings',
    314: 'drawing_tools',
    315: 'replay_mode',
    316: 'idea_chart_sharing',
    317: 'community_scripts',
    318: 'broker_comparison',
    319: 'paper_trading_simulation',
    320: 'cross_market_workspace',
    321: 'custom_intelligence_screener',
    322: 'decision_first_mode',
    323: 'institutional_l1_l2_market_data',
    324: 'reference_data_registry',
    325: 'spot_derivatives_coverage',
    326: 'defi_market_data',
    327: 'market_depth_liquidity_intelligence',
    328: 'fair_market_value_pricing',
    329: 'best_execution_pricing',
    330: 'reference_rates',
    331: 'etf_reference_rates_inav',
    332: 'commodity_tradfi_reference_rates',
    333: 'indices',
    334: 'risk_analytics',
    335: 'derivatives_listing_analytics',
    336: 'market_surveillance',
    337: 'aml_cft_on_chain_monitoring',
    338: 'data_quality_pipeline',
    339: 'data_provenance_audit',
    340: 'real_time_rest_grpc_streaming',
    341: 'historical_data_archive',
    342: 'venue_quality_ranking',
    343: 'execution_quality_analytics',
    344: 'institutional_sla_monitoring',
    345: 'cross_market_institutional_decision_layer',
    346: 'standardized_financial_metrics',
    347: 'fees_intelligence',
    348: 'revenue_intelligence',
    349: 'token_incentives',
    350: 'earnings_economic_profit_proxy',
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
    """Batch wrap — BCBS 239 top-level provenance."""
    merged: dict[str, Any] = dict(extra or {})
    if isinstance(payload, dict):
        src = payload.get("data_source") or payload.get("source")
        if src and not merged.get("data_source"):
            merged["data_source"] = src
        ts = payload.get("timestamp") or payload.get("attached_at")
        if ts and not merged.get("timestamp"):
            merged["timestamp"] = ts
    if not merged.get("data_source"):
        merged["data_source"] = f"cap646.batch07_dedicated#cap{capability_id:03d}"
    if not merged.get("timestamp"):
        merged["timestamp"] = datetime.now(UTC).isoformat()
    return _base_wrap(
        capability_id, symbol=symbol, payload_key=payload_key, payload=payload, extra=merged,
    )


async def _cap301(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(301, params={**params, "symbol": symbol})
    return _wrap(301, symbol=symbol, payload_key="multi_chart_layouts", payload=payload)

async def _cap302(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(302, params={**params, "symbol": symbol})
    return _wrap(302, symbol=symbol, payload_key="technical_indicator_library", payload=payload)

async def _cap303(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(303, params={**params, "symbol": symbol})
    return _wrap(303, symbol=symbol, payload_key="custom_indicator_scripting", payload=payload)

async def _cap304(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(304, params={**params, "symbol": symbol})
    return _wrap(304, symbol=symbol, payload_key="strategy_backtesting", payload=payload)

async def _cap305(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(305, params={**params, "symbol": symbol})
    return _wrap(305, symbol=symbol, payload_key="market_screener", payload=payload)

async def _cap306(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(306, params={**params, "symbol": symbol})
    return _wrap(306, symbol=symbol, payload_key="pine_style_screener", payload=payload)

async def _cap307(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(307, params={**params, "symbol": symbol})
    return _wrap(307, symbol=symbol, payload_key="smart_alerts", payload=payload)

async def _cap308(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(308, params={**params, "symbol": symbol})
    return _wrap(308, symbol=symbol, payload_key="watchlists", payload=payload)

async def _cap309(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(309, params={**params, "symbol": symbol})
    return _wrap(309, symbol=symbol, payload_key="economic_calendar", payload=payload)

async def _cap310(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(310, params={**params, "symbol": symbol})
    return _wrap(310, symbol=symbol, payload_key="crypto_calendar_events", payload=payload)

async def _cap311(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(311, params={**params, "symbol": symbol})
    return _wrap(311, symbol=symbol, payload_key="news_integration", payload=payload)

async def _cap312(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(312, params={**params, "symbol": symbol})
    return _wrap(312, symbol=symbol, payload_key="heatmaps", payload=payload)

async def _cap313(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(313, params={**params, "symbol": symbol})
    return _wrap(313, symbol=symbol, payload_key="technical_ratings", payload=payload)

async def _cap314(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(314, params={**params, "symbol": symbol})
    return _wrap(314, symbol=symbol, payload_key="drawing_tools", payload=payload)

async def _cap315(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(315, params={**params, "symbol": symbol})
    return _wrap(315, symbol=symbol, payload_key="replay_mode", payload=payload)

async def _cap316(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(316, params={**params, "symbol": symbol})
    return _wrap(316, symbol=symbol, payload_key="idea_chart_sharing", payload=payload)

async def _cap317(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(317, params={**params, "symbol": symbol})
    return _wrap(317, symbol=symbol, payload_key="community_scripts", payload=payload)

async def _cap318(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(318, params={**params, "symbol": symbol})
    return _wrap(318, symbol=symbol, payload_key="broker_comparison", payload=payload)

async def _cap319(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(319, params={**params, "symbol": symbol})
    return _wrap(319, symbol=symbol, payload_key="paper_trading_simulation", payload=payload)

async def _cap320(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(320, params={**params, "symbol": symbol})
    return _wrap(320, symbol=symbol, payload_key="cross_market_workspace", payload=payload)

async def _cap321(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(321, params={**params, "symbol": symbol})
    return _wrap(321, symbol=symbol, payload_key="custom_intelligence_screener", payload=payload)

async def _cap322(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(322, params={**params, "symbol": symbol})
    return _wrap(322, symbol=symbol, payload_key="decision_first_mode", payload=payload)

async def _cap323(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(323, params={**params, "symbol": symbol})
    return _wrap(323, symbol=symbol, payload_key="institutional_l1_l2_market_data", payload=payload)

async def _cap324(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(324, params={**params, "symbol": symbol})
    return _wrap(324, symbol=symbol, payload_key="reference_data_registry", payload=payload)

async def _cap325(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(325, params={**params, "symbol": symbol})
    return _wrap(325, symbol=symbol, payload_key="spot_derivatives_coverage", payload=payload)

async def _cap326(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(326, params={**params, "symbol": symbol})
    return _wrap(326, symbol=symbol, payload_key="defi_market_data", payload=payload)

async def _cap327(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(327, params={**params, "symbol": symbol})
    return _wrap(327, symbol=symbol, payload_key="market_depth_liquidity_intelligence", payload=payload)

async def _cap328(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(328, params={**params, "symbol": symbol})
    return _wrap(328, symbol=symbol, payload_key="fair_market_value_pricing", payload=payload)

async def _cap329(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(329, params={**params, "symbol": symbol})
    return _wrap(329, symbol=symbol, payload_key="best_execution_pricing", payload=payload)

async def _cap330(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(330, params={**params, "symbol": symbol})
    return _wrap(330, symbol=symbol, payload_key="reference_rates", payload=payload)

async def _cap331(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(331, params={**params, "symbol": symbol})
    return _wrap(331, symbol=symbol, payload_key="etf_reference_rates_inav", payload=payload)

async def _cap332(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(332, params={**params, "symbol": symbol})
    return _wrap(332, symbol=symbol, payload_key="commodity_tradfi_reference_rates", payload=payload)

async def _cap333(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(333, params={**params, "symbol": symbol})
    return _wrap(333, symbol=symbol, payload_key="indices", payload=payload)

async def _cap334(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(334, params={**params, "symbol": symbol})
    return _wrap(334, symbol=symbol, payload_key="risk_analytics", payload=payload)

async def _cap335(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(335, params={**params, "symbol": symbol})
    return _wrap(335, symbol=symbol, payload_key="derivatives_listing_analytics", payload=payload)

async def _cap336(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(336, params={**params, "symbol": symbol})
    return _wrap(336, symbol=symbol, payload_key="market_surveillance", payload=payload)

async def _cap337(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(337, params={**params, "symbol": symbol})
    return _wrap(337, symbol=symbol, payload_key="aml_cft_on_chain_monitoring", payload=payload)

async def _cap338(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(338, params={**params, "symbol": symbol})
    return _wrap(338, symbol=symbol, payload_key="data_quality_pipeline", payload=payload)

async def _cap339(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(339, params={**params, "symbol": symbol})
    return _wrap(339, symbol=symbol, payload_key="data_provenance_audit", payload=payload)

async def _cap340(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(340, params={**params, "symbol": symbol})
    return _wrap(340, symbol=symbol, payload_key="real_time_rest_grpc_streaming", payload=payload)

async def _cap341(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(341, params={**params, "symbol": symbol})
    return _wrap(341, symbol=symbol, payload_key="historical_data_archive", payload=payload)

async def _cap342(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(342, params={**params, "symbol": symbol})
    return _wrap(342, symbol=symbol, payload_key="venue_quality_ranking", payload=payload)

async def _cap343(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(343, params={**params, "symbol": symbol})
    return _wrap(343, symbol=symbol, payload_key="execution_quality_analytics", payload=payload)

async def _cap344(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(344, params={**params, "symbol": symbol})
    return _wrap(344, symbol=symbol, payload_key="institutional_sla_monitoring", payload=payload)

async def _cap345(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(345, params={**params, "symbol": symbol})
    return _wrap(345, symbol=symbol, payload_key="cross_market_institutional_decision_layer", payload=payload)

async def _cap346(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(346, params={**params, "symbol": symbol})
    return _wrap(346, symbol=symbol, payload_key="standardized_financial_metrics", payload=payload)

async def _cap347(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(347, params={**params, "symbol": symbol})
    return _wrap(347, symbol=symbol, payload_key="fees_intelligence", payload=payload)

async def _cap348(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(348, params={**params, "symbol": symbol})
    return _wrap(348, symbol=symbol, payload_key="revenue_intelligence", payload=payload)

async def _cap349(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(349, params={**params, "symbol": symbol})
    return _wrap(349, symbol=symbol, payload_key="token_incentives", payload=payload)

async def _cap350(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    payload = await invoke_underlying(350, params={**params, "symbol": symbol})
    return _wrap(350, symbol=symbol, payload_key="earnings_economic_profit_proxy", payload=payload)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    301: _cap301,
    302: _cap302,
    303: _cap303,
    304: _cap304,
    305: _cap305,
    306: _cap306,
    307: _cap307,
    308: _cap308,
    309: _cap309,
    310: _cap310,
    311: _cap311,
    312: _cap312,
    313: _cap313,
    314: _cap314,
    315: _cap315,
    316: _cap316,
    317: _cap317,
    318: _cap318,
    319: _cap319,
    320: _cap320,
    321: _cap321,
    322: _cap322,
    323: _cap323,
    324: _cap324,
    325: _cap325,
    326: _cap326,
    327: _cap327,
    328: _cap328,
    329: _cap329,
    330: _cap330,
    331: _cap331,
    332: _cap332,
    333: _cap333,
    334: _cap334,
    335: _cap335,
    336: _cap336,
    337: _cap337,
    338: _cap338,
    339: _cap339,
    340: _cap340,
    341: _cap341,
    342: _cap342,
    343: _cap343,
    344: _cap344,
    345: _cap345,
    346: _cap346,
    347: _cap347,
    348: _cap348,
    349: _cap349,
    350: _cap350,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH07_DEDICATED_IDS,
        overlap_batch01_ids=BATCH07_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch07: ID in batch01 overlap — CROSS-SPINE-001",
        not_dedicated_error="capability not in batch07 dedicated set",
    )
