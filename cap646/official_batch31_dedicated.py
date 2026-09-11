"""Official batch 31 — from-scratch dedicated backends (IDs 751–775)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH31_IDS: frozenset[int] = frozenset(range(751, 776))
BATCH31_DEDICATED_IDS: frozenset[int] = frozenset({751, 752, 753, 754, 755, 756, 757, 758, 759, 760, 761, 762, 763, 764, 765, 766, 767, 768, 769, 770, 771, 772, 773, 774, 775})
BATCH31_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    751: "ohlcv_data",
    752: "derivatives_data",
    753: "open_interest_data",
    754: "funding_rate_data",
    755: "index_data",
    756: "reference_pricing",
    757: "exchange_metadata",
    758: "asset_metadata",
    759: "historical_market_archive",
    760: "real_time_streams",
    761: "market_aggregates",
    762: "liquidity_analytics",
    763: "volatility_analytics",
    764: "market_cap_supply",
    765: "etf_etp_data",
    766: "api_coverage_registry",
    767: "data_quality_normalization",
    768: "institutional_delivery",
    769: "benchmark_administration_metadata",
    770: "cross_market_data_intelligence",
    771: "unified_exchange_connector_layer",
    772: "tick_trade_data",
    773: "quote_data",
    774: "ohlcv",
    775: "l1_order_book",
}

async def _cap751(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap751 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap752(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap752 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap753(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap753 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap754(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap754 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap755(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap755 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap756(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap756 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap757(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap757 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap758(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap758 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap759(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap759 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap760(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap760 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap761(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap761 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap762(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap762 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap763(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap763 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap764(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap764 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap765(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap765 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap766(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap766 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap767(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap767 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap768(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap768 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap769(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap769 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap770(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap770 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap771(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap771 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap772(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap772 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap773(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap773 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap774(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap774 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap775(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch31_dedicated import _cap775 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    751: _cap751,
    752: _cap752,
    753: _cap753,
    754: _cap754,
    755: _cap755,
    756: _cap756,
    757: _cap757,
    758: _cap758,
    759: _cap759,
    760: _cap760,
    761: _cap761,
    762: _cap762,
    763: _cap763,
    764: _cap764,
    765: _cap765,
    766: _cap766,
    767: _cap767,
    768: _cap768,
    769: _cap769,
    770: _cap770,
    771: _cap771,
    772: _cap772,
    773: _cap773,
    774: _cap774,
    775: _cap775,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH31_DEDICATED_IDS,
        overlap_batch01_ids=BATCH31_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch31",
        not_dedicated_error=f"official batch31: not dedicated",
    )
