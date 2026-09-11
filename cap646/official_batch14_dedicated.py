"""Official batch 14 — from-scratch dedicated backends (IDs 326–350)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH14_IDS: frozenset[int] = frozenset(range(326, 351))
BATCH14_DEDICATED_IDS: frozenset[int] = frozenset({326, 327, 328, 329, 330, 331, 332, 333, 334, 335, 336, 337, 338, 339, 340, 341, 342, 343, 344, 345, 346, 347, 348, 349, 350})
BATCH14_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    326: "defi_market_data",
    327: "market_depth_liquidity_intelligence",
    328: "fair_market_value_pricing",
    329: "best_execution_pricing",
    330: "reference_rates",
    331: "etf_reference_rates_inav",
    332: "commodity_tradfi_reference_rates",
    333: "indices",
    334: "risk_analytics",
    335: "derivatives_listing_analytics",
    336: "market_surveillance",
    337: "aml_cft_on_chain_monitoring",
    338: "data_quality_pipeline",
    339: "data_provenance_audit",
    340: "real_time_rest_grpc_streaming",
    341: "historical_data_archive",
    342: "venue_quality_ranking",
    343: "execution_quality_analytics",
    344: "institutional_sla_monitoring",
    345: "cross_market_institutional_decision_layer",
    346: "standardized_financial_metrics",
    347: "fees_intelligence",
    348: "revenue_intelligence",
    349: "token_incentives",
    350: "earnings_economic_profit_proxy",
}

async def _cap326(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap326 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap327(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap327 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap328(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap328 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap329(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap329 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap330(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap330 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap331(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap331 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap332(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap332 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap333(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap333 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap334(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap334 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap335(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap335 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap336(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap336 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap337(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap337 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap338(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap338 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap339(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap339 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap340(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap340 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap341(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap341 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap342(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap342 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap343(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap343 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap344(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap344 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap345(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap345 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap346(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap346 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap347(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap347 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap348(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap348 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap349(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap349 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap350(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch14_dedicated import _cap350 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
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
        dedicated_ids=BATCH14_DEDICATED_IDS,
        overlap_batch01_ids=BATCH14_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch14",
        not_dedicated_error=f"official batch14: not dedicated",
    )
