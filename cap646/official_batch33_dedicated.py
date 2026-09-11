"""Official batch 33 — from-scratch dedicated backends (IDs 801–825)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH33_IDS: frozenset[int] = frozenset(range(801, 826))
BATCH33_DEDICATED_IDS: frozenset[int] = frozenset({801, 802, 803, 804, 805, 806, 807, 808, 809, 810, 811, 812, 813, 814, 815, 816, 817, 818, 819, 820, 821, 822, 823, 824, 825})
BATCH33_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    801: "bucketed_cvd",
    802: "whale_vs_retail_flow",
    803: "slippage_intelligence",
    804: "global_order_book_metrics",
    805: "order_book_imbalance",
    806: "liquidity_zones",
    807: "bot_activity_detection",
    808: "market_positioning",
    809: "liquidation_pressure_score",
    810: "orderflow_anomaly_detection",
    811: "api_indicator_platform",
    812: "extension_capability_812",
    813: "extension_capability_813",
    814: "extension_capability_814",
    815: "extension_capability_815",
    816: "funding_rate_intelligence",
    817: "open_interest_intelligence",
    818: "liquidation_intelligence",
    819: "futures_volume",
    820: "basis_intelligence",
    821: "spot_market_data",
    822: "options_analytics",
    823: "options_iv_surface",
    824: "options_skew",
    825: "options_term_structure",
}

async def _cap801(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap801 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap802(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap802 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap803(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap803 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap804(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap804 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap805(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap805 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap806(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap806 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap807(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap807 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap808(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap808 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap809(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap809 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap810(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap810 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap811(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap811 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap812(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap812 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap813(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap813 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap814(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap814 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap815(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap815 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap816(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap816 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap817(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap817 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap818(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap818 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap819(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap819 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap820(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap820 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap821(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap821 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap822(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap822 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap823(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap823 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap824(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap824 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap825(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch33_dedicated import _cap825 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    801: _cap801,
    802: _cap802,
    803: _cap803,
    804: _cap804,
    805: _cap805,
    806: _cap806,
    807: _cap807,
    808: _cap808,
    809: _cap809,
    810: _cap810,
    811: _cap811,
    812: _cap812,
    813: _cap813,
    814: _cap814,
    815: _cap815,
    816: _cap816,
    817: _cap817,
    818: _cap818,
    819: _cap819,
    820: _cap820,
    821: _cap821,
    822: _cap822,
    823: _cap823,
    824: _cap824,
    825: _cap825,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH33_DEDICATED_IDS,
        overlap_batch01_ids=BATCH33_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch33",
        not_dedicated_error=f"official batch33: not dedicated",
    )
