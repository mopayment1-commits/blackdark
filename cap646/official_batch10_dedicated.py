"""Official batch 10 — from-scratch dedicated backends (IDs 226–250)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH10_IDS: frozenset[int] = frozenset(range(226, 251))
BATCH10_DEDICATED_IDS: frozenset[int] = frozenset({227, 229, 230, 231, 234, 235, 236, 237, 238, 239, 240, 242, 243, 244, 245, 246, 247, 248, 249, 250})
BATCH10_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    227: "unified_trading_intelligence_workspace",
    229: "cross_exchange_funding_arbitrage_scanner",
    230: "spot_perp_arbitrage_scanner",
    231: "futures_basis_term_structure",
    234: "cvd_intelligence",
    235: "long_short_ratio_intelligence",
    236: "dex_screener",
    237: "token_risk_scoring",
    238: "pump_dump_detection",
    239: "narrative_tracking",
    240: "sector_rotation_intelligence",
    242: "price_prediction_multi_signal_forecast",
    243: "correlation_matrix",
    244: "new_listings_intelligence",
    245: "market_health_freshness",
    246: "coverage_metadata_registry",
    247: "public_rest_api",
    248: "mcp_server_for_ai_agents",
    249: "cli_access",
    250: "openapi_sdk_generation",
}

async def _cap227(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap227 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap229(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap229 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap230(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap230 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap231(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap231 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap234(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap234 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap235(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap235 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap236(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap236 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap237(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap237 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap238(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap238 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap239(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap239 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap240(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap240 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap242(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap242 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap243(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap243 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap244(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap244 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap245(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap245 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap246(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap246 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap247(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap247 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap248(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap248 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap249(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap249 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap250(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch10_dedicated import _cap250 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    227: _cap227,
    229: _cap229,
    230: _cap230,
    231: _cap231,
    234: _cap234,
    235: _cap235,
    236: _cap236,
    237: _cap237,
    238: _cap238,
    239: _cap239,
    240: _cap240,
    242: _cap242,
    243: _cap243,
    244: _cap244,
    245: _cap245,
    246: _cap246,
    247: _cap247,
    248: _cap248,
    249: _cap249,
    250: _cap250,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH10_DEDICATED_IDS,
        overlap_batch01_ids=BATCH10_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch10",
        not_dedicated_error=f"official batch10: not dedicated",
    )
