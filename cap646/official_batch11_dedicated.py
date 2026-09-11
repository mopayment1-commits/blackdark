"""Official batch 11 — from-scratch dedicated backends (IDs 251–275)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH11_IDS: frozenset[int] = frozenset(range(251, 276))
BATCH11_DEDICATED_IDS: frozenset[int] = frozenset({252, 253, 254, 258, 259, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 273, 274})
BATCH11_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    252: "liquidation_heatmap",
    253: "liquidation_map_levels",
    254: "real_time_liquidation_events",
    258: "top_trader_positioning",
    259: "futures_basis_intelligence",
    261: "futures_cvd_taker_flow",
    262: "options_open_interest",
    263: "options_volume",
    264: "options_iv_skew",
    265: "max_pain_gamma_context",
    266: "spot_market_intelligence",
    267: "order_book_market_depth",
    268: "historical_derivatives_data",
    269: "exchange_comparison",
    270: "liquidation_cascade_proximity",
    271: "leverage_pressure_score",
    273: "multi_model_liquidation_comparison",
    274: "derivatives_alerts",
}

async def _cap252(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap252 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap253(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap253 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap254(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap254 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap258(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap258 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap259(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap259 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap261(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap261 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap262(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap262 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap263(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap263 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap264(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap264 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap265(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap265 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap266(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap266 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap267(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap267 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap268(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap268 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap269(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap269 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap270(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap270 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap271(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap271 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap273(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap273 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap274(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch11_dedicated import _cap274 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    252: _cap252,
    253: _cap253,
    254: _cap254,
    258: _cap258,
    259: _cap259,
    261: _cap261,
    262: _cap262,
    263: _cap263,
    264: _cap264,
    265: _cap265,
    266: _cap266,
    267: _cap267,
    268: _cap268,
    269: _cap269,
    270: _cap270,
    271: _cap271,
    273: _cap273,
    274: _cap274,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH11_DEDICATED_IDS,
        overlap_batch01_ids=BATCH11_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch11",
        not_dedicated_error=f"official batch11: not dedicated",
    )
