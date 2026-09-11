"""Official Batch 13 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 13 (IDs 301–325).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH13_IDS: frozenset[int] = frozenset(range(301, 326))
BATCH13_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH13_DEDICATED_IDS: frozenset[int] = frozenset({301, 302, 303, 304, 305, 306, 309, 310, 311, 312, 313, 314, 315, 316, 317, 318, 319, 320, 321, 322, 323, 324, 325})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

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

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap301(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        301,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="multi_chart_layouts",
        params=params,
    )

async def _cap302(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        302,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="technical_indicator_library",
        params=params,
    )

async def _cap303(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        303,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="custom_indicator_scripting",
        params=params,
    )

async def _cap304(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        304,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="strategy_backtesting",
        params=params,
    )

async def _cap305(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        305,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="market_screener",
        params=params,
    )

async def _cap306(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        306,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="pine_style_screener",
        params=params,
    )

async def _cap309(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        309,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="economic_calendar",
        params=params,
    )

async def _cap310(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        310,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="crypto_calendar_events",
        params=params,
    )

async def _cap311(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        311,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="news_integration",
        params=params,
    )

async def _cap312(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        312,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="heatmaps",
        params=params,
    )

async def _cap313(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        313,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="technical_ratings",
        params=params,
    )

async def _cap314(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        314,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="drawing_tools",
        params=params,
    )

async def _cap315(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        315,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="replay_mode",
        params=params,
    )

async def _cap316(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        316,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="idea_chart_sharing",
        params=params,
    )

async def _cap317(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        317,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="community_scripts",
        params=params,
    )

async def _cap318(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        318,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="broker_comparison",
        params=params,
    )

async def _cap319(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        319,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="paper_trading_simulation",
        params=params,
    )

async def _cap320(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        320,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_market_workspace",
        params=params,
    )

async def _cap321(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        321,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="custom_intelligence_screener",
        params=params,
    )

async def _cap322(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        322,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="decision_first_mode",
        params=params,
    )

async def _cap323(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        323,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="institutional_l1_l2_market_data",
        params=params,
    )

async def _cap324(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        324,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="reference_data_registry",
        params=params,
    )

async def _cap325(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        325,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="spot_derivatives_coverage",
        params=params,
    )

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
        overlap_error="batch01 overlap for batch13",
        not_dedicated_error=f"batch13: not a dedicated capability",
    )
