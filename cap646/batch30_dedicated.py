"""Official Batch 30 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 30 (IDs 726–750).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH30_IDS: frozenset[int] = frozenset(range(726, 751))
BATCH30_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH30_DEDICATED_IDS: frozenset[int] = frozenset({726, 727, 728, 729, 730, 731, 732, 733, 734, 735, 736, 737, 738, 739, 740, 741, 742, 743, 744, 745, 746, 747, 748, 749, 750})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    726: "network_data_pro_metrics",
    727: "atlas_blockchain_search",
    728: "address_balance_search",
    729: "transaction_search",
    730: "block_search",
    731: "balance_updates",
    732: "stablecoin_network_metrics",
    733: "market_data_feed",
    734: "market_data_pro",
    735: "reference_rates",
    736: "indexes",
    737: "realized_metrics",
    738: "supply_metrics",
    739: "mining_validator_metrics",
    740: "fee_metrics",
    741: "activity_metrics",
    742: "custom_metric_workbench",
    743: "community_charts_api",
    744: "market_network_join",
    745: "data_quality_methodologies",
    746: "historical_research_dataset",
    747: "institutional_apis",
    748: "cross_network_decision_intelligence",
    749: "institutional_trade_data",
    750: "order_book_data",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap726(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        726,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="network_data_pro_metrics",
        params=params,
    )

async def _cap727(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        727,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="atlas_blockchain_search",
        params=params,
    )

async def _cap728(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        728,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="address_balance_search",
        params=params,
    )

async def _cap729(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        729,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="transaction_search",
        params=params,
    )

async def _cap730(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        730,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="block_search",
        params=params,
    )

async def _cap731(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        731,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="balance_updates",
        params=params,
    )

async def _cap732(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        732,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="stablecoin_network_metrics",
        params=params,
    )

async def _cap733(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        733,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="market_data_feed",
        params=params,
    )

async def _cap734(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        734,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="market_data_pro",
        params=params,
    )

async def _cap735(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        735,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="reference_rates",
        params=params,
    )

async def _cap736(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        736,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="indexes",
        params=params,
    )

async def _cap737(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        737,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="realized_metrics",
        params=params,
    )

async def _cap738(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        738,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="supply_metrics",
        params=params,
    )

async def _cap739(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        739,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="mining_validator_metrics",
        params=params,
    )

async def _cap740(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        740,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="fee_metrics",
        params=params,
    )

async def _cap741(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        741,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="activity_metrics",
        params=params,
    )

async def _cap742(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        742,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="custom_metric_workbench",
        params=params,
    )

async def _cap743(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        743,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="community_charts_api",
        params=params,
    )

async def _cap744(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        744,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="market_network_join",
        params=params,
    )

async def _cap745(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        745,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="data_quality_methodologies",
        params=params,
    )

async def _cap746(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        746,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="historical_research_dataset",
        params=params,
    )

async def _cap747(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        747,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="institutional_apis",
        params=params,
    )

async def _cap748(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        748,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_network_decision_intelligence",
        params=params,
    )

async def _cap749(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        749,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="institutional_trade_data",
        params=params,
    )

async def _cap750(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        750,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="order_book_data",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    726: _cap726,
    727: _cap727,
    728: _cap728,
    729: _cap729,
    730: _cap730,
    731: _cap731,
    732: _cap732,
    733: _cap733,
    734: _cap734,
    735: _cap735,
    736: _cap736,
    737: _cap737,
    738: _cap738,
    739: _cap739,
    740: _cap740,
    741: _cap741,
    742: _cap742,
    743: _cap743,
    744: _cap744,
    745: _cap745,
    746: _cap746,
    747: _cap747,
    748: _cap748,
    749: _cap749,
    750: _cap750,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH30_DEDICATED_IDS,
        overlap_batch01_ids=BATCH30_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch30",
        not_dedicated_error=f"batch30: not a dedicated capability",
    )
