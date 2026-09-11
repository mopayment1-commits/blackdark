"""Official Batch 16 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 16 (IDs 376–400).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH16_IDS: frozenset[int] = frozenset(range(376, 401))
BATCH16_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH16_DEDICATED_IDS: frozenset[int] = frozenset({376, 377, 378, 379, 380, 381, 382, 383, 384, 385, 386, 387, 388, 389, 390, 391, 392, 394, 395, 396, 398, 400})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    376: "public_dashboard_sharing",
    377: "community_discovery",
    378: "query_forking",
    379: "data_api",
    380: "real_time_feed",
    381: "datashare",
    382: "dbt_connector",
    383: "bi_connectors",
    384: "mcp_for_ai_agents",
    385: "prompt_to_sql_agent",
    386: "dashboard_from_prompt",
    387: "scheduled_queries",
    388: "alerts_from_query_results",
    389: "data_lineage",
    390: "query_performance_governance",
    391: "white_label_embedded_analytics",
    392: "cross_domain_decision_layer",
    394: "chain_tvl_comparison",
    395: "protocol_directory",
    396: "fees_revenue",
    398: "perps_volume",
    400: "stablecoins_intelligence",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap376(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        376,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="public_dashboard_sharing",
        params=params,
    )

async def _cap377(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        377,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="community_discovery",
        params=params,
    )

async def _cap378(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        378,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="query_forking",
        params=params,
    )

async def _cap379(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        379,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="data_api",
        params=params,
    )

async def _cap380(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        380,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="real_time_feed",
        params=params,
    )

async def _cap381(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        381,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="datashare",
        params=params,
    )

async def _cap382(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        382,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dbt_connector",
        params=params,
    )

async def _cap383(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        383,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="bi_connectors",
        params=params,
    )

async def _cap384(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        384,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="mcp_for_ai_agents",
        params=params,
    )

async def _cap385(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        385,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="prompt_to_sql_agent",
        params=params,
    )

async def _cap386(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        386,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dashboard_from_prompt",
        params=params,
    )

async def _cap387(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        387,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="scheduled_queries",
        params=params,
    )

async def _cap388(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        388,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="alerts_from_query_results",
        params=params,
    )

async def _cap389(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        389,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="data_lineage",
        params=params,
    )

async def _cap390(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        390,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="query_performance_governance",
        params=params,
    )

async def _cap391(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        391,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="white_label_embedded_analytics",
        params=params,
    )

async def _cap392(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        392,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_domain_decision_layer",
        params=params,
    )

async def _cap394(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        394,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="chain_tvl_comparison",
        params=params,
    )

async def _cap395(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        395,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="protocol_directory",
        params=params,
    )

async def _cap396(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        396,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="fees_revenue",
        params=params,
    )

async def _cap398(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        398,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="perps_volume",
        params=params,
    )

async def _cap400(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        400,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoins_intelligence",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    376: _cap376,
    377: _cap377,
    378: _cap378,
    379: _cap379,
    380: _cap380,
    381: _cap381,
    382: _cap382,
    383: _cap383,
    384: _cap384,
    385: _cap385,
    386: _cap386,
    387: _cap387,
    388: _cap388,
    389: _cap389,
    390: _cap390,
    391: _cap391,
    392: _cap392,
    394: _cap394,
    395: _cap395,
    396: _cap396,
    398: _cap398,
    400: _cap400,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH16_DEDICATED_IDS,
        overlap_batch01_ids=BATCH16_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch16",
        not_dedicated_error=f"batch16: not a dedicated capability",
    )
