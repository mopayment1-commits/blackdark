"""Official Batch 08 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 08 (IDs 176–200).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH08_IDS: frozenset[int] = frozenset(range(176, 201))
BATCH08_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH08_DEDICATED_IDS: frozenset[int] = frozenset({176, 177, 178, 179, 180, 181, 182, 183, 184, 185, 186, 187, 188, 189, 190, 191, 192, 193, 194, 195, 196, 197, 198, 199, 200})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

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

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap176(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        176,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="weighted_social_sentiment",
        params=params,
    )

async def _cap177(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        177,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="social_sentiment_balance",
        params=params,
    )

async def _cap178(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        178,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="social_source_breakdown",
        params=params,
    )

async def _cap179(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        179,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="development_activity_intelligence",
        params=params,
    )

async def _cap180(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        180,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="development_activity_contributors",
        params=params,
    )

async def _cap181(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        181,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="ecosystem_development_dashboard",
        params=params,
    )

async def _cap182(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        182,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="developer_activity_change_detection",
        params=params,
    )

async def _cap183(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        183,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="whale_transaction_intelligence",
        params=params,
    )

async def _cap184(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        184,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="whale_shark_holder_cohorts",
        params=params,
    )

async def _cap185(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        185,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="top_holders_intelligence",
        params=params,
    )

async def _cap186(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        186,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="historical_wallet_balance_tool",
        params=params,
    )

async def _cap187(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        187,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="exchange_inflow_intelligence",
        params=params,
    )

async def _cap188(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        188,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="exchange_outflow_intelligence",
        params=params,
    )

async def _cap189(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        189,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="exchange_netflow_intelligence",
        params=params,
    )

async def _cap190(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        190,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="exchange_supply_balance_intelligence",
        params=params,
    )

async def _cap191(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        191,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="exchange_user_activity",
        params=params,
    )

async def _cap192(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        192,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="network_activity_intelligence",
        params=params,
    )

async def _cap193(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        193,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="transaction_volume_intelligence",
        params=params,
    )

async def _cap194(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        194,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="nvt_intelligence",
        params=params,
    )

async def _cap195(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        195,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="mvrv_intelligence",
        params=params,
    )

async def _cap196(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        196,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="realized_cap_realized_value_intelligence",
        params=params,
    )

async def _cap197(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        197,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="daily_active_addresses",
        params=params,
    )

async def _cap198(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        198,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="age_consumed_dormancy_intelligence",
        params=params,
    )

async def _cap199(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        199,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="mean_dollar_invested_age",
        params=params,
    )

async def _cap200(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        200,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="token_circulation_intelligence",
        params=params,
    )

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
        overlap_error="batch01 overlap for batch08",
        not_dedicated_error=f"batch08: not a dedicated capability",
    )
