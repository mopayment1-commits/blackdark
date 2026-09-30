"""Official Batch 11 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 11 (IDs 251–275).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH11_IDS: frozenset[int] = frozenset(range(251, 276))
BATCH11_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH11_DEDICATED_IDS: frozenset[int] = frozenset({252, 253, 254, 258, 259, 261, 262, 263, 264, 265, 266, 267, 268, 269, 270, 271, 273, 274})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

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

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap252(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        252,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="liquidation_heatmap",
        params=params,
    )

async def _cap253(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        253,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="liquidation_map_levels",
        params=params,
    )

async def _cap254(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        254,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="real_time_liquidation_events",
        params=params,
    )

async def _cap258(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        258,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="top_trader_positioning",
        params=params,
    )

async def _cap259(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        259,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="futures_basis_intelligence",
        params=params,
    )

async def _cap261(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        261,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="futures_cvd_taker_flow",
        params=params,
    )

async def _cap262(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        262,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="options_open_interest",
        params=params,
    )

async def _cap263(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        263,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="options_volume",
        params=params,
    )

async def _cap264(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        264,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="options_iv_skew",
        params=params,
    )

async def _cap265(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        265,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="max_pain_gamma_context",
        params=params,
    )

async def _cap266(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        266,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="spot_market_intelligence",
        params=params,
    )

async def _cap267(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        267,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="order_book_market_depth",
        params=params,
    )

async def _cap268(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        268,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="historical_derivatives_data",
        params=params,
    )

async def _cap269(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        269,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="exchange_comparison",
        params=params,
    )

async def _cap270(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        270,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="liquidation_cascade_proximity",
        params=params,
    )

async def _cap271(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        271,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="leverage_pressure_score",
        params=params,
    )

async def _cap273(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        273,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="multi_model_liquidation_comparison",
        params=params,
    )

async def _cap274(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        274,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="derivatives_alerts",
        params=params,
    )

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
        overlap_error="batch01 overlap for batch11",
        not_dedicated_error=f"batch11: not a dedicated capability",
    )
