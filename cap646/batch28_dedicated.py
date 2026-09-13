"""Official Batch 28 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 28 (IDs 676–700).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH28_IDS: frozenset[int] = frozenset(range(676, 701))
BATCH28_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH28_DEDICATED_IDS: frozenset[int] = frozenset({676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    676: "unlocks",
    677: "treasury_intelligence",
    678: "airdrop_incentive_intelligence",
    679: "capital_formation_radar",
    680: "defi_opportunity_screener",
    681: "defi_risk_passport",
    682: "api_aggregation_layer",
    683: "cross_defi_decision_intelligence",
    684: "cross_chain_fundamentals",
    685: "protocol_fundamentals",
    686: "stablecoin_intelligence",
    687: "stablecoin_activity_breakdown",
    688: "developer_activity",
    689: "sector_ecosystem_comparables",
    690: "equities_crypto_research",
    691: "consensus_estimates",
    692: "ai_analyst",
    693: "thesis_research_workspace",
    694: "comparable_company_protocol_analysis",
    695: "excel_sheets_integration",
    696: "api_data_platform",
    697: "research_templates",
    698: "dashboards",
    699: "stablecoin_payment_intelligence",
    700: "on_chain_usage_intelligence",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap676(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        676,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="unlocks",
        params=params,
    )

async def _cap677(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        677,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="treasury_intelligence",
        params=params,
    )

async def _cap678(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        678,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="airdrop_incentive_intelligence",
        params=params,
    )

async def _cap679(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        679,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="capital_formation_radar",
        params=params,
    )

async def _cap680(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        680,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="defi_opportunity_screener",
        params=params,
    )

async def _cap681(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        681,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="defi_risk_passport",
        params=params,
    )

async def _cap682(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        682,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="api_aggregation_layer",
        params=params,
    )

async def _cap683(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        683,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_defi_decision_intelligence",
        params=params,
    )

async def _cap684(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        684,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_chain_fundamentals",
        params=params,
    )

async def _cap685(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        685,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="protocol_fundamentals",
        params=params,
    )

async def _cap686(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        686,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoin_intelligence",
        params=params,
    )

async def _cap687(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        687,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoin_activity_breakdown",
        params=params,
    )

async def _cap688(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        688,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="developer_activity",
        params=params,
    )

async def _cap689(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        689,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="sector_ecosystem_comparables",
        params=params,
    )

async def _cap690(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        690,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="equities_crypto_research",
        params=params,
    )

async def _cap691(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        691,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="consensus_estimates",
        params=params,
    )

async def _cap692(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        692,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="ai_analyst",
        params=params,
    )

async def _cap693(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        693,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="thesis_research_workspace",
        params=params,
    )

async def _cap694(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        694,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="comparable_company_protocol_analysis",
        params=params,
    )

async def _cap695(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        695,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="excel_sheets_integration",
        params=params,
    )

async def _cap696(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        696,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="api_data_platform",
        params=params,
    )

async def _cap697(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        697,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="research_templates",
        params=params,
    )

async def _cap698(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        698,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dashboards",
        params=params,
    )

async def _cap699(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        699,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoin_payment_intelligence",
        params=params,
    )

async def _cap700(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        700,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="on_chain_usage_intelligence",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    676: _cap676,
    677: _cap677,
    678: _cap678,
    679: _cap679,
    680: _cap680,
    681: _cap681,
    682: _cap682,
    683: _cap683,
    684: _cap684,
    685: _cap685,
    686: _cap686,
    687: _cap687,
    688: _cap688,
    689: _cap689,
    690: _cap690,
    691: _cap691,
    692: _cap692,
    693: _cap693,
    694: _cap694,
    695: _cap695,
    696: _cap696,
    697: _cap697,
    698: _cap698,
    699: _cap699,
    700: _cap700,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH28_DEDICATED_IDS,
        overlap_batch01_ids=BATCH28_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch28",
        not_dedicated_error=f"batch28: not a dedicated capability",
    )
