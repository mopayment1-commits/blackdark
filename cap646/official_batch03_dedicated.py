"""Official batch 03 — from-scratch dedicated backends (IDs 51–75)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

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

async def _cap51(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap051 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap52(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap052 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap53(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap053 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap54(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap054 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap55(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap055_nvt_fair_value as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap56(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap056_token_screener as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap57(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap057 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap58(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap058 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap59(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap059_research_dashboards as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap60(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap060_metric_smart_alerts as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap61(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap061 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap62(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap062 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap63(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap063 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap65(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap065 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap66(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap066 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap67(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap067 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap68(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap068 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap70(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap070 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap71(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap071 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap72(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap072 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap73(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap073 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap74(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap074 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap75(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch02_dedicated import _cap075 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

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
        overlap_error="batch01 overlap for official batch03",
        not_dedicated_error=f"official batch03: not dedicated",
    )
