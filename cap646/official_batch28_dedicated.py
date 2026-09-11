"""Official batch 28 — from-scratch dedicated backends (IDs 676–700)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH28_IDS: frozenset[int] = frozenset(range(676, 701))
BATCH28_DEDICATED_IDS: frozenset[int] = frozenset({676, 677, 678, 679, 680, 681, 682, 683, 684, 685, 686, 687, 688, 689, 690, 691, 692, 693, 694, 695, 696, 697, 698, 699, 700})
BATCH28_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

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

async def _cap676(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap676 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap677(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap677 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap678(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap678 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap679(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap679 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap680(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap680 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap681(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap681 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap682(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap682 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap683(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap683 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap684(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap684 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap685(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap685 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap686(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap686 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap687(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap687 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap688(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap688 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap689(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap689 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap690(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap690 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap691(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap691 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap692(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap692 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap693(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap693 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap694(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap694 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap695(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap695 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap696(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap696 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap697(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap697 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap698(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap698 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap699(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap699 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap700(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch28_dedicated import _cap700 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

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
        overlap_error="batch01 overlap for official batch28",
        not_dedicated_error=f"official batch28: not dedicated",
    )
