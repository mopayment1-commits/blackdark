"""Official batch 05 — from-scratch dedicated backends (IDs 101–125)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

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

async def _cap101(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap101 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap102(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap102 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap103(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        103,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="api_data_platform",
        capability_name="API Data Platform",
        track="T17",
    )

async def _cap104(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap104 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap105(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap105 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap108(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap108 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap109(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap109 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap111(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap111 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap112(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap112 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap113(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap113 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap114(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap114 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap115(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap115 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap116(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap116 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap117(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap117 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap118(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap118 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap119(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap119 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap120(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap120 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap121(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap121 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap122(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap122 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap123(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap123 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap124(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap124 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

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
        overlap_error="batch01 overlap for official batch05",
        not_dedicated_error=f"official batch05: not dedicated",
    )
