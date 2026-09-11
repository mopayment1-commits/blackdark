"""Official batch 06 — from-scratch dedicated backends (IDs 126–150)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH06_IDS: frozenset[int] = frozenset(range(126, 151))
BATCH06_DEDICATED_IDS: frozenset[int] = frozenset({126, 127, 128, 129, 130, 131, 132, 133, 134, 135, 136, 137, 138, 139, 140, 141, 142, 143, 144, 145, 146, 147, 148, 149, 150})
BATCH06_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    126: "futures_volume_intelligence",
    127: "multi_factor_market_overview",
    128: "momentum_intelligence",
    129: "sentiment_intelligence",
    130: "mindshare_intelligence",
    131: "narrative_sector_intelligence",
    132: "mindshare_gainers_losers",
    133: "curated_crypto_news_intelligence",
    134: "ai_news_summaries",
    135: "real_time_industry_event_monitoring",
    136: "agentic_monitoring_views",
    137: "custom_watchlists",
    138: "token_unlock_calendar",
    139: "vesting_schedule_intelligence",
    140: "token_allocation_intelligence",
    141: "unlock_impact_intelligence",
    142: "fundraising_rounds_intelligence",
    143: "investor_intelligence",
    144: "fund_fund_manager_intelligence",
    145: "m_a_intelligence",
    146: "capital_flow_funding_trend_intelligence",
    147: "comparable_funding_valuation_analysis",
    148: "due_diligence_report_engine",
    149: "automated_risk_scoring_from_diligence",
    150: "protocol_kpi_intelligence",
}

async def _cap126(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap126 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap127(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap127 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap128(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap128 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap129(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.dedicated_from_scratch import execute_from_scratch
    return await execute_from_scratch(
        129,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        address=address,
        params=params,
        payload_key="sentiment_intelligence",
        capability_name="Sentiment Intelligence",
        track="T04",
    )

async def _cap130(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap130 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap131(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap131 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap132(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap132 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap133(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap133 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap134(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap134 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap135(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap135 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap136(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap136 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap137(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap137 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap138(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap138 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap139(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap139 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap140(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap140 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap141(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap141 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap142(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap142 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap143(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap143 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap144(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap144 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap145(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap145 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap146(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap146 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap147(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap147 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap148(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap148 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap149(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap149 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap150(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch03_dedicated import _cap150 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    126: _cap126,
    127: _cap127,
    128: _cap128,
    129: _cap129,
    130: _cap130,
    131: _cap131,
    132: _cap132,
    133: _cap133,
    134: _cap134,
    135: _cap135,
    136: _cap136,
    137: _cap137,
    138: _cap138,
    139: _cap139,
    140: _cap140,
    141: _cap141,
    142: _cap142,
    143: _cap143,
    144: _cap144,
    145: _cap145,
    146: _cap146,
    147: _cap147,
    148: _cap148,
    149: _cap149,
    150: _cap150,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH06_DEDICATED_IDS,
        overlap_batch01_ids=BATCH06_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch06",
        not_dedicated_error=f"official batch06: not dedicated",
    )
