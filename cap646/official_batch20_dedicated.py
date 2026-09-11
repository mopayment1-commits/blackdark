"""Official batch 20 — from-scratch dedicated backends (IDs 476–500)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH20_IDS: frozenset[int] = frozenset(range(476, 501))
BATCH20_DEDICATED_IDS: frozenset[int] = frozenset({476, 477, 478, 479, 480, 481, 482, 483, 484, 485, 486, 487, 488, 489, 490, 491, 492, 493, 494, 495, 496, 497, 498, 499, 500})
BATCH20_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    476: "community_charts_api",
    477: "market_network_join",
    478: "data_quality_methodologies",
    479: "historical_research_dataset",
    480: "institutional_apis",
    481: "cross_network_decision_intelligence",
    482: "institutional_trade_data",
    483: "order_book_data",
    484: "ohlcv_data",
    485: "derivatives_data",
    486: "open_interest_data",
    487: "funding_rate_data",
    488: "index_data",
    489: "reference_pricing",
    490: "exchange_metadata",
    491: "asset_metadata",
    492: "historical_market_archive",
    493: "real_time_streams",
    494: "market_aggregates",
    495: "liquidity_analytics",
    496: "volatility_analytics",
    497: "market_cap_supply",
    498: "etf_etp_data",
    499: "api_coverage_registry",
    500: "data_quality_normalization",
}

async def _cap476(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap476 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap477(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap477 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap478(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap478 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap479(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap479 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap480(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap480 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap481(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap481 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap482(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap482 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap483(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap483 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap484(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap484 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap485(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap485 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap486(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap486 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap487(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap487 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap488(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap488 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap489(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap489 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap490(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap490 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap491(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap491 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap492(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap492 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap493(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap493 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap494(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap494 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap495(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap495 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap496(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap496 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap497(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap497 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap498(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap498 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap499(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap499 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap500(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch20_dedicated import _cap500 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    476: _cap476,
    477: _cap477,
    478: _cap478,
    479: _cap479,
    480: _cap480,
    481: _cap481,
    482: _cap482,
    483: _cap483,
    484: _cap484,
    485: _cap485,
    486: _cap486,
    487: _cap487,
    488: _cap488,
    489: _cap489,
    490: _cap490,
    491: _cap491,
    492: _cap492,
    493: _cap493,
    494: _cap494,
    495: _cap495,
    496: _cap496,
    497: _cap497,
    498: _cap498,
    499: _cap499,
    500: _cap500,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH20_DEDICATED_IDS,
        overlap_batch01_ids=BATCH20_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch20",
        not_dedicated_error=f"official batch20: not dedicated",
    )
