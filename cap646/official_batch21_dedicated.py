"""Official batch 21 — from-scratch dedicated backends (IDs 501–525)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH21_IDS: frozenset[int] = frozenset(range(501, 526))
BATCH21_DEDICATED_IDS: frozenset[int] = frozenset({501, 502, 503, 504, 505, 506, 507, 508, 509, 510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521, 522, 523, 524, 525})
BATCH21_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    501: "institutional_delivery",
    502: "benchmark_administration_metadata",
    503: "cross_market_data_intelligence",
    504: "unified_exchange_connector_layer",
    505: "tick_trade_data",
    506: "quote_data",
    507: "ohlcv",
    508: "l1_order_book",
    509: "l2_order_book",
    510: "l3_order_book",
    511: "options_market_data",
    512: "funding_oi_liquidation_metrics",
    513: "asset_symbol_metadata",
    514: "historical_flat_files",
    515: "rest_api",
    516: "websocket_streaming",
    517: "fix_connectivity",
    518: "mcp_for_ai",
    519: "exchange_rates_vwap",
    520: "indexes",
    521: "volatility_index",
    522: "ems_integration_boundary",
    523: "data_health_sla_monitoring",
    524: "symbol_mapping_engine",
    525: "cross_venue_data_quality_score",
}

async def _cap501(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap501 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap502(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap502 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap503(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap503 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap504(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap504 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap505(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap505 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap506(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap506 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap507(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap507 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap508(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap508 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap509(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap509 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap510(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap510 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap511(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap511 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap512(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap512 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap513(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap513 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap514(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap514 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap515(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap515 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap516(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap516 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap517(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap517 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap518(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap518 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap519(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap519 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap520(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap520 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap521(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap521 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap522(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap522 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap523(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap523 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap524(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap524 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap525(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch21_dedicated import _cap525 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    501: _cap501,
    502: _cap502,
    503: _cap503,
    504: _cap504,
    505: _cap505,
    506: _cap506,
    507: _cap507,
    508: _cap508,
    509: _cap509,
    510: _cap510,
    511: _cap511,
    512: _cap512,
    513: _cap513,
    514: _cap514,
    515: _cap515,
    516: _cap516,
    517: _cap517,
    518: _cap518,
    519: _cap519,
    520: _cap520,
    521: _cap521,
    522: _cap522,
    523: _cap523,
    524: _cap524,
    525: _cap525,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH21_DEDICATED_IDS,
        overlap_batch01_ids=BATCH21_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch21",
        not_dedicated_error=f"official batch21: not dedicated",
    )
