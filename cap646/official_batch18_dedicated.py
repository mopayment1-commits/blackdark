"""Official batch 18 — from-scratch dedicated backends (IDs 426–450)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH18_IDS: frozenset[int] = frozenset(range(426, 451))
BATCH18_DEDICATED_IDS: frozenset[int] = frozenset({426, 427, 428, 430, 431, 432, 433, 434, 435, 436, 437, 438, 439, 440, 441, 442, 443, 444, 445, 446, 447, 448, 449, 450})
BATCH18_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    426: "thesis_research_workspace",
    427: "comparable_company_protocol_analysis",
    428: "excel_sheets_integration",
    430: "research_templates",
    431: "dashboards",
    432: "stablecoin_payment_intelligence",
    433: "on_chain_usage_intelligence",
    434: "revenue_fees_economic_activity",
    435: "cross_market_research_copilot",
    436: "investment_thesis_scoring",
    437: "defi_risk_radar",
    438: "lending_market_risk",
    439: "collateral_risk",
    440: "liquidation_risk",
    441: "oracle_risk",
    442: "liquidity_risk",
    443: "protocol_exploit_intelligence",
    444: "stablecoin_risk_intelligence",
    445: "defi_strategy_risk",
    446: "real_time_risk_alerts",
    447: "dao_treasury_risk",
    448: "institutional_risk_api",
    449: "curated_on_chain_dashboards",
    450: "narrative_driven_research",
}

async def _cap426(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap426 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap427(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap427 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap428(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap428 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap430(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap430 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap431(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap431 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap432(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap432 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap433(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap433 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap434(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap434 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap435(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap435 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap436(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap436 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap437(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap437 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap438(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap438 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap439(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap439 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap440(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap440 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap441(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap441 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap442(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap442 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap443(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap443 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap444(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap444 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap445(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap445 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap446(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap446 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap447(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap447 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap448(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap448 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap449(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap449 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap450(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch18_dedicated import _cap450 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    426: _cap426,
    427: _cap427,
    428: _cap428,
    430: _cap430,
    431: _cap431,
    432: _cap432,
    433: _cap433,
    434: _cap434,
    435: _cap435,
    436: _cap436,
    437: _cap437,
    438: _cap438,
    439: _cap439,
    440: _cap440,
    441: _cap441,
    442: _cap442,
    443: _cap443,
    444: _cap444,
    445: _cap445,
    446: _cap446,
    447: _cap447,
    448: _cap448,
    449: _cap449,
    450: _cap450,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH18_DEDICATED_IDS,
        overlap_batch01_ids=BATCH18_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch18",
        not_dedicated_error=f"official batch18: not dedicated",
    )
