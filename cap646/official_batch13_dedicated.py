"""Official batch 13 — from-scratch dedicated backends (IDs 301–325)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH13_IDS: frozenset[int] = frozenset(range(301, 326))
BATCH13_DEDICATED_IDS: frozenset[int] = frozenset({301, 302, 303, 304, 305, 306, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325})
BATCH13_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    301: "multi_chart_layouts",
    302: "technical_indicator_library",
    303: "custom_indicator_scripting",
    304: "strategy_backtesting",
    305: "market_screener",
    306: "pine_style_screener",
    309: "economic_calendar",
    310: "crypto_calendar_events",
    311: "news_integration",
    312: "heatmaps",
    313: "technical_ratings",
    314: "drawing_tools",
    315: "replay_mode",
    316: "idea_chart_sharing",
    317: "community_scripts",
    318: "broker_comparison",
    319: "paper_trading_simulation",
    320: "cross_market_workspace",
    321: "custom_intelligence_screener",
    322: "decision_first_mode",
    323: "institutional_l1_l2_market_data",
    324: "reference_data_registry",
    325: "spot_derivatives_coverage",
}

async def _cap301(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap301 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap302(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap302 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap303(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap303 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap304(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap304 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap305(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap305 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap306(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap306 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap309(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap309 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap310(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap310 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap311(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap311 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap312(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap312 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap313(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap313 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap314(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap314 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap315(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap315 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap316(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap316 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap317(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap317 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap318(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap318 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap319(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap319 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap320(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap320 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap321(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap321 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap322(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap322 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap323(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap323 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap324(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap324 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap325(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch13_dedicated import _cap325 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    301: _cap301,
    302: _cap302,
    303: _cap303,
    304: _cap304,
    305: _cap305,
    306: _cap306,
    309: _cap309,
    310: _cap310,
    311: _cap311,
    312: _cap312,
    313: _cap313,
    314: _cap314,
    315: _cap315,
    316: _cap316,
    317: _cap317,
    318: _cap318,
    319: _cap319,
    320: _cap320,
    321: _cap321,
    322: _cap322,
    323: _cap323,
    324: _cap324,
    325: _cap325,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH13_DEDICATED_IDS,
        overlap_batch01_ids=BATCH13_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch13",
        not_dedicated_error=f"official batch13: not dedicated",
    )
