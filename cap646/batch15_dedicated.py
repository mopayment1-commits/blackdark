"""Official Batch 15 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 15 (IDs 351–375).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH15_IDS: frozenset[int] = frozenset(range(351, 376))
BATCH15_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH15_DEDICATED_IDS: frozenset[int] = frozenset({351, 352, 353, 354, 355, 356, 357, 358, 359, 360, 361, 362, 363, 364, 365, 366, 367, 368, 369, 370, 371, 372, 373, 374, 375})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    351: "active_users",
    352: "core_developers",
    353: "code_commits",
    354: "tvl_intelligence",
    355: "borrowed_loans_outstanding",
    356: "dex_volume",
    357: "stablecoin_supply",
    358: "valuation_multiples",
    359: "growth_metrics",
    360: "margins_take_rate",
    361: "project_comparables",
    362: "sector_comparables",
    363: "tokenized_asset_coverage",
    364: "fundamental_screener",
    365: "financial_statement_view",
    366: "data_methodology_registry",
    367: "source_data_provenance",
    368: "api_data_export",
    369: "cross_fundamental_decision_intelligence",
    370: "sql_on_chain_query_workspace",
    371: "curated_data_models",
    372: "decoded_smart_contract_tables",
    373: "cross_chain_data_warehouse",
    374: "visualization_builder",
    375: "dashboard_builder",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap351(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        351,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="active_users",
        params=params,
    )

async def _cap352(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        352,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="core_developers",
        params=params,
    )

async def _cap353(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        353,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="code_commits",
        params=params,
    )

async def _cap354(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        354,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="tvl_intelligence",
        params=params,
    )

async def _cap355(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        355,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="borrowed_loans_outstanding",
        params=params,
    )

async def _cap356(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        356,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dex_volume",
        params=params,
    )

async def _cap357(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        357,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoin_supply",
        params=params,
    )

async def _cap358(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        358,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="valuation_multiples",
        params=params,
    )

async def _cap359(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        359,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="growth_metrics",
        params=params,
    )

async def _cap360(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        360,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="margins_take_rate",
        params=params,
    )

async def _cap361(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        361,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="project_comparables",
        params=params,
    )

async def _cap362(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        362,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="sector_comparables",
        params=params,
    )

async def _cap363(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        363,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="tokenized_asset_coverage",
        params=params,
    )

async def _cap364(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        364,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="fundamental_screener",
        params=params,
    )

async def _cap365(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        365,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="financial_statement_view",
        params=params,
    )

async def _cap366(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        366,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="data_methodology_registry",
        params=params,
    )

async def _cap367(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        367,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="source_data_provenance",
        params=params,
    )

async def _cap368(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        368,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="api_data_export",
        params=params,
    )

async def _cap369(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        369,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_fundamental_decision_intelligence",
        params=params,
    )

async def _cap370(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        370,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="sql_on_chain_query_workspace",
        params=params,
    )

async def _cap371(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        371,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="curated_data_models",
        params=params,
    )

async def _cap372(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        372,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="decoded_smart_contract_tables",
        params=params,
    )

async def _cap373(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        373,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_chain_data_warehouse",
        params=params,
    )

async def _cap374(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        374,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="visualization_builder",
        params=params,
    )

async def _cap375(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        375,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dashboard_builder",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    351: _cap351,
    352: _cap352,
    353: _cap353,
    354: _cap354,
    355: _cap355,
    356: _cap356,
    357: _cap357,
    358: _cap358,
    359: _cap359,
    360: _cap360,
    361: _cap361,
    362: _cap362,
    363: _cap363,
    364: _cap364,
    365: _cap365,
    366: _cap366,
    367: _cap367,
    368: _cap368,
    369: _cap369,
    370: _cap370,
    371: _cap371,
    372: _cap372,
    373: _cap373,
    374: _cap374,
    375: _cap375,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH15_DEDICATED_IDS,
        overlap_batch01_ids=BATCH15_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch15",
        not_dedicated_error=f"batch15: not a dedicated capability",
    )
