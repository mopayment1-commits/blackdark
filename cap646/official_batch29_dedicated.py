"""Official batch 29 — from-scratch dedicated backends (IDs 701–725)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH29_IDS: frozenset[int] = frozenset(range(701, 726))
BATCH29_DEDICATED_IDS: frozenset[int] = frozenset({701, 702, 703, 704, 705, 706, 707, 708, 709, 710, 711, 712, 713, 714, 715, 716, 717, 718, 719, 720, 721, 722, 723, 724, 725})
BATCH29_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    701: "revenue_fees_economic_activity",
    702: "cross_market_research_copilot",
    703: "investment_thesis_scoring",
    704: "extension_capability_704",
    705: "lending_market_risk",
    706: "collateral_risk",
    707: "liquidation_risk",
    708: "extension_capability_708",
    709: "liquidity_risk",
    710: "protocol_exploit_intelligence",
    711: "stablecoin_risk_intelligence",
    712: "defi_strategy_risk",
    713: "real_time_risk_alerts",
    714: "dao_treasury_risk",
    715: "institutional_risk_api",
    716: "curated_on_chain_dashboards",
    717: "narrative_driven_research",
    718: "protocol_dominance",
    719: "aave_multi_chain_analytics",
    720: "risk_curation",
    721: "capital_protection_controls",
    722: "stress_testing",
    723: "cross_protocol_contagion",
    724: "protocol_risk_passport",
    725: "extension_capability_725",
}

async def _cap701(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap701 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap702(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap702 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap703(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap703 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap704(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap704 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap705(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap705 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap706(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap706 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap707(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap707 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap708(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap708 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap709(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap709 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap710(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap710 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap711(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap711 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap712(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap712 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap713(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap713 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap714(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap714 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap715(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap715 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap716(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap716 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap717(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap717 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap718(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap718 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap719(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap719 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap720(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap720 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap721(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap721 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap722(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap722 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap723(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap723 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap724(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap724 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap725(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch29_dedicated import _cap725 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    701: _cap701,
    702: _cap702,
    703: _cap703,
    704: _cap704,
    705: _cap705,
    706: _cap706,
    707: _cap707,
    708: _cap708,
    709: _cap709,
    710: _cap710,
    711: _cap711,
    712: _cap712,
    713: _cap713,
    714: _cap714,
    715: _cap715,
    716: _cap716,
    717: _cap717,
    718: _cap718,
    719: _cap719,
    720: _cap720,
    721: _cap721,
    722: _cap722,
    723: _cap723,
    724: _cap724,
    725: _cap725,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH29_DEDICATED_IDS,
        overlap_batch01_ids=BATCH29_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch29",
        not_dedicated_error=f"official batch29: not dedicated",
    )
