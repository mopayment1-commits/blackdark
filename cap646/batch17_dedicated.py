"""Official Batch 17 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 17 (IDs 401–425).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH17_IDS: frozenset[int] = frozenset(range(401, 426))
BATCH17_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH17_DEDICATED_IDS: frozenset[int] = frozenset({401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421, 422, 423, 424, 425})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    401: "bridges_intelligence",
    402: "yields_screener",
    403: "yield_history",
    404: "borrowing_rates",
    405: "liquid_staking_intelligence",
    406: "rwa_intelligence",
    407: "raises_funding_rounds",
    408: "investor_profiles",
    409: "unlocks",
    410: "treasury_intelligence",
    411: "airdrop_incentive_intelligence",
    412: "capital_formation_radar",
    413: "defi_opportunity_screener",
    414: "defi_risk_passport",
    415: "api_aggregation_layer",
    416: "cross_defi_decision_intelligence",
    417: "cross_chain_fundamentals",
    418: "protocol_fundamentals",
    419: "stablecoin_intelligence",
    420: "stablecoin_activity_breakdown",
    421: "developer_activity",
    422: "sector_ecosystem_comparables",
    423: "equities_crypto_research",
    424: "consensus_estimates",
    425: "ai_analyst",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap401(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        401,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="bridges_intelligence",
        params=params,
    )

async def _cap402(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        402,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="yields_screener",
        params=params,
    )

async def _cap403(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        403,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="yield_history",
        params=params,
    )

async def _cap404(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        404,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="borrowing_rates",
        params=params,
    )

async def _cap405(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        405,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="liquid_staking_intelligence",
        params=params,
    )

async def _cap406(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        406,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="rwa_intelligence",
        params=params,
    )

async def _cap407(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        407,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="raises_funding_rounds",
        params=params,
    )

async def _cap408(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        408,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="investor_profiles",
        params=params,
    )

async def _cap409(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        409,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="unlocks",
        params=params,
    )

async def _cap410(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        410,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="treasury_intelligence",
        params=params,
    )

async def _cap411(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        411,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="airdrop_incentive_intelligence",
        params=params,
    )

async def _cap412(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        412,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="capital_formation_radar",
        params=params,
    )

async def _cap413(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        413,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="defi_opportunity_screener",
        params=params,
    )

async def _cap414(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        414,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="defi_risk_passport",
        params=params,
    )

async def _cap415(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        415,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="api_aggregation_layer",
        params=params,
    )

async def _cap416(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        416,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_defi_decision_intelligence",
        params=params,
    )

async def _cap417(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        417,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_chain_fundamentals",
        params=params,
    )

async def _cap418(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        418,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="protocol_fundamentals",
        params=params,
    )

async def _cap419(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        419,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoin_intelligence",
        params=params,
    )

async def _cap420(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        420,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoin_activity_breakdown",
        params=params,
    )

async def _cap421(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        421,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="developer_activity",
        params=params,
    )

async def _cap422(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        422,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="sector_ecosystem_comparables",
        params=params,
    )

async def _cap423(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        423,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="equities_crypto_research",
        params=params,
    )

async def _cap424(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        424,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="consensus_estimates",
        params=params,
    )

async def _cap425(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        425,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="ai_analyst",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    401: _cap401,
    402: _cap402,
    403: _cap403,
    404: _cap404,
    405: _cap405,
    406: _cap406,
    407: _cap407,
    408: _cap408,
    409: _cap409,
    410: _cap410,
    411: _cap411,
    412: _cap412,
    413: _cap413,
    414: _cap414,
    415: _cap415,
    416: _cap416,
    417: _cap417,
    418: _cap418,
    419: _cap419,
    420: _cap420,
    421: _cap421,
    422: _cap422,
    423: _cap423,
    424: _cap424,
    425: _cap425,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH17_DEDICATED_IDS,
        overlap_batch01_ids=BATCH17_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch17",
        not_dedicated_error=f"batch17: not a dedicated capability",
    )
