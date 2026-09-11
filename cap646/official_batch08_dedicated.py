"""Official batch 08 — from-scratch dedicated backends (IDs 176–200)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH08_IDS: frozenset[int] = frozenset(range(176, 201))
BATCH08_DEDICATED_IDS: frozenset[int] = frozenset({176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200})
BATCH08_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

EXPECTED_SURFACE: dict[int, str] = {
    176: "weighted_social_sentiment",
    177: "social_sentiment_balance",
    178: "social_source_breakdown",
    179: "development_activity_intelligence",
    180: "development_activity_contributors",
    181: "ecosystem_development_dashboard",
    182: "developer_activity_change_detection",
    183: "whale_transaction_intelligence",
    184: "whale_shark_holder_cohorts",
    185: "top_holders_intelligence",
    186: "historical_wallet_balance_tool",
    187: "exchange_inflow_intelligence",
    188: "exchange_outflow_intelligence",
    189: "exchange_netflow_intelligence",
    190: "exchange_supply_balance_intelligence",
    191: "exchange_user_activity",
    192: "network_activity_intelligence",
    193: "transaction_volume_intelligence",
    194: "nvt_intelligence",
    195: "mvrv_intelligence",
    196: "realized_cap_realized_value_intelligence",
    197: "daily_active_addresses",
    198: "age_consumed_dormancy_intelligence",
    199: "mean_dollar_invested_age",
    200: "token_circulation_intelligence",
}

async def _cap176(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap176 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap177(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap177 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap178(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap178 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap179(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap179 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap180(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap180 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap181(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap181 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap182(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap182 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap183(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap183 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap184(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap184 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap185(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap185 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap186(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap186 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap187(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap187 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap188(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap188 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap189(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap189 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap190(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap190 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap191(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap191 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap192(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap192 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap193(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap193 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap194(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap194 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap195(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap195 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap196(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap196 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap197(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap197 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap198(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap198 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap199(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap199 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap200(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch08_dedicated import _cap200 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    176: _cap176,
    177: _cap177,
    178: _cap178,
    179: _cap179,
    180: _cap180,
    181: _cap181,
    182: _cap182,
    183: _cap183,
    184: _cap184,
    185: _cap185,
    186: _cap186,
    187: _cap187,
    188: _cap188,
    189: _cap189,
    190: _cap190,
    191: _cap191,
    192: _cap192,
    193: _cap193,
    194: _cap194,
    195: _cap195,
    196: _cap196,
    197: _cap197,
    198: _cap198,
    199: _cap199,
    200: _cap200,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH08_DEDICATED_IDS,
        overlap_batch01_ids=BATCH08_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for official batch08",
        not_dedicated_error=f"official batch08: not dedicated",
    )
