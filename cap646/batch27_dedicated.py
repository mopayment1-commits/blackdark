"""Official Batch 27 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 27 (IDs 651–675).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH27_IDS: frozenset[int] = frozenset(range(651, 676))
BATCH27_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH27_DEDICATED_IDS: frozenset[int] = frozenset({651, 652, 653, 654, 655, 656, 657, 658, 659, 660, 661, 662, 663, 664, 665, 666, 667, 668, 669, 670, 671, 672, 673, 674, 675})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    651: "mcp_for_ai_agents",
    652: "prompt_to_sql_agent",
    653: "dashboard_from_prompt",
    654: "scheduled_queries",
    655: "alerts_from_query_results",
    656: "data_lineage",
    657: "query_performance_governance",
    658: "white_label_embedded_analytics",
    659: "cross_domain_decision_layer",
    660: "tvl_intelligence",
    661: "chain_tvl_comparison",
    662: "protocol_directory",
    663: "fees_revenue",
    664: "dex_volume",
    665: "perps_volume",
    666: "options_volume",
    667: "stablecoins_intelligence",
    668: "bridges_intelligence",
    669: "yields_screener",
    670: "yield_history",
    671: "borrowing_rates",
    672: "liquid_staking_intelligence",
    673: "rwa_intelligence",
    674: "raises_funding_rounds",
    675: "investor_profiles",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap651(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        651,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="mcp_for_ai_agents",
        params=params,
    )

async def _cap652(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        652,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="prompt_to_sql_agent",
        params=params,
    )

async def _cap653(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        653,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dashboard_from_prompt",
        params=params,
    )

async def _cap654(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        654,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="scheduled_queries",
        params=params,
    )

async def _cap655(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        655,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="alerts_from_query_results",
        params=params,
    )

async def _cap656(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        656,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="data_lineage",
        params=params,
    )

async def _cap657(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        657,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="query_performance_governance",
        params=params,
    )

async def _cap658(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        658,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="white_label_embedded_analytics",
        params=params,
    )

async def _cap659(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        659,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_domain_decision_layer",
        params=params,
    )

async def _cap660(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        660,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="tvl_intelligence",
        params=params,
    )

async def _cap661(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        661,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="chain_tvl_comparison",
        params=params,
    )

async def _cap662(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        662,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="protocol_directory",
        params=params,
    )

async def _cap663(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        663,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="fees_revenue",
        params=params,
    )

async def _cap664(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        664,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dex_volume",
        params=params,
    )

async def _cap665(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        665,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="perps_volume",
        params=params,
    )

async def _cap666(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        666,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="options_volume",
        params=params,
    )

async def _cap667(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        667,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoins_intelligence",
        params=params,
    )

async def _cap668(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        668,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="bridges_intelligence",
        params=params,
    )

async def _cap669(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        669,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="yields_screener",
        params=params,
    )

async def _cap670(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        670,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="yield_history",
        params=params,
    )

async def _cap671(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        671,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="borrowing_rates",
        params=params,
    )

async def _cap672(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        672,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="liquid_staking_intelligence",
        params=params,
    )

async def _cap673(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        673,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="rwa_intelligence",
        params=params,
    )

async def _cap674(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        674,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="raises_funding_rounds",
        params=params,
    )

async def _cap675(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        675,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="investor_profiles",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    651: _cap651,
    652: _cap652,
    653: _cap653,
    654: _cap654,
    655: _cap655,
    656: _cap656,
    657: _cap657,
    658: _cap658,
    659: _cap659,
    660: _cap660,
    661: _cap661,
    662: _cap662,
    663: _cap663,
    664: _cap664,
    665: _cap665,
    666: _cap666,
    667: _cap667,
    668: _cap668,
    669: _cap669,
    670: _cap670,
    671: _cap671,
    672: _cap672,
    673: _cap673,
    674: _cap674,
    675: _cap675,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH27_DEDICATED_IDS,
        overlap_batch01_ids=BATCH27_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch27",
        not_dedicated_error=f"batch27: not a dedicated capability",
    )
