"""Official batch 32 — from-scratch dedicated backends (IDs 776–800)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH32_IDS: frozenset[int] = frozenset(range(776, 801))
BATCH32_DEDICATED_IDS: frozenset[int] = frozenset({776, 777, 778, 779, 780, 781, 782, 783, 784, 785, 786, 787, 788, 789, 790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800})
BATCH32_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    776: "l2_order_book",
    777: "l3_order_book",
    778: "options_market_data",
    779: "funding_oi_liquidation_metrics",
    780: "asset_symbol_metadata",
    781: "historical_flat_files",
    782: "rest_api",
    783: "websocket_streaming",
    784: "fix_connectivity",
    785: "mcp_for_ai",
    786: "exchange_rates_vwap",
    787: "indexes",
    788: "volatility_index",
    789: "ems_integration_boundary",
    790: "data_health_sla_monitoring",
    791: "symbol_mapping_engine",
    792: "cross_venue_data_quality_score",
    793: "ai_market_data_grounding_layer",
    794: "liquidation_heatmap",
    795: "liquidation_levels",
    796: "liquidation_cascade_model",
    797: "global_liquidation_metrics",
    798: "open_interest",
    799: "funding_rates",
    800: "order_flow_intelligence",
}

async def _cap776(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap776 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap777(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap777 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap778(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap778 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap779(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap779 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap780(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap780 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap781(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap781 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap782(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap782 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap783(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap783 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap784(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap784 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap785(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap785 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap786(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap786 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap787(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap787 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap788(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap788 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap789(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap789 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap790(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap790 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap791(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap791 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap792(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap792 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap793(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap793 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap794(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap794 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap795(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap795 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap796(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap796 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap797(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap797 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap798(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap798 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap799(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap799 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap800(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch32_dedicated import _cap800 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    776: _cap776,
    777: _cap777,
    778: _cap778,
    779: _cap779,
    780: _cap780,
    781: _cap781,
    782: _cap782,
    783: _cap783,
    784: _cap784,
    785: _cap785,
    786: _cap786,
    787: _cap787,
    788: _cap788,
    789: _cap789,
    790: _cap790,
    791: _cap791,
    792: _cap792,
    793: _cap793,
    794: _cap794,
    795: _cap795,
    796: _cap796,
    797: _cap797,
    798: _cap798,
    799: _cap799,
    800: _cap800,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH32_DEDICATED_IDS,
        overlap_batch01_ids=BATCH32_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch32",
        not_dedicated_error=f"official batch32: not dedicated",
    )
