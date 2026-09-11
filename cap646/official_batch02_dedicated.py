"""Official batch 02 — from-scratch dedicated backends (IDs 26–50)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH02_IDS: frozenset[int] = frozenset(range(26, 51))
BATCH02_DEDICATED_IDS: frozenset[int] = frozenset({26, 27, 28, 29, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50})
BATCH02_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    26: "price_move_explanation",
    27: "smart_money_historical_trend_analysis",
    28: "smart_money_conviction_engine",
    29: "cross_market_decision_intelligence_engine",
    31: "cross_signal_confirmation",
    32: "contradiction_detection",
    33: "smart_money_actionability_score",
    34: "beginner_decision_mode",
    35: "market_compass_market_regime_engine",
    36: "on_chain_metrics_library",
    37: "entity_adjusted_metrics",
    38: "cost_basis_distribution",
    39: "realized_cap_realized_price_intelligence",
    40: "mvrv_mvrv_z_score_suite",
    41: "sopr_profitability_intelligence",
    42: "holder_cohort_intelligence",
    43: "supply_dynamics_intelligence",
    44: "exchange_balance_netflow_intelligence",
    45: "etf_flow_intelligence",
    46: "digital_asset_treasury_company_intelligence",
    47: "spot_market_metrics_suite",
    48: "futures_intelligence_suite",
    49: "options_intelligence_suite",
    50: "order_book_intelligence",
}

async def _cap26(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap026_price_move_explanation as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap27(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap027_smart_money_historical_trend as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap28(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap028_smart_money_conviction as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap29(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap029_cross_market_decision as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap31(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap031_cross_signal_confirmation as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap32(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap032_contradiction_detection as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap33(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap033_actionability_score as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap34(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap034_beginner_decision_mode as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap35(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap035_market_compass_regime as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap36(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap036_on_chain_metrics_library as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap37(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap037_entity_adjusted_metrics as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap38(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        38,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="cost_basis_distribution",
        capability_name="Cost Basis Distribution",
        track="T09",
    )

async def _cap39(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        39,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="realized_cap_realized_price_intelligence",
        capability_name="Realized Cap & Realized Price Intelligence",
        track="T09",
    )

async def _cap40(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap040_mvrv_suite as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap41(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap041_sopr_profitability as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap42(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap042_holder_cohort_intelligence as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap43(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap043_supply_dynamics_intelligence as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap44(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap044_exchange_balance_netflow as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap45(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        45,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="etf_flow_intelligence",
        capability_name="ETF Flow Intelligence",
        track="T04",
    )

async def _cap46(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap046_treasury_company as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap47(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        47,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="spot_market_metrics_suite",
        capability_name="Spot Market Metrics Suite",
        track="T04",
    )

async def _cap48(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        48,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="futures_intelligence_suite",
        capability_name="Futures Intelligence Suite",
        track="T05",
    )

async def _cap49(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        49,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="options_intelligence_suite",
        capability_name="Options Intelligence Suite",
        track="T08",
    )

async def _cap50(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch01_dedicated import _cap050_order_book_intelligence as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    26: _cap26,
    27: _cap27,
    28: _cap28,
    29: _cap29,
    31: _cap31,
    32: _cap32,
    33: _cap33,
    34: _cap34,
    35: _cap35,
    36: _cap36,
    37: _cap37,
    38: _cap38,
    39: _cap39,
    40: _cap40,
    41: _cap41,
    42: _cap42,
    43: _cap43,
    44: _cap44,
    45: _cap45,
    46: _cap46,
    47: _cap47,
    48: _cap48,
    49: _cap49,
    50: _cap50,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH02_DEDICATED_IDS,
        overlap_batch01_ids=BATCH02_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch02",
        not_dedicated_error=f"official batch02: not dedicated",
    )
