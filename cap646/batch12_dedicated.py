"""Official Batch 12 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 12 (IDs 276–300).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH12_IDS: frozenset[int] = frozenset(range(276, 301))
BATCH12_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH12_DEDICATED_IDS: frozenset[int] = frozenset({276, 277, 278, 279, 280, 281, 282, 283, 284, 285, 286, 287, 288, 289, 290, 291, 292, 293, 294, 295, 296, 297, 298, 299, 300})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    276: "entity_resolution_engine",
    277: "address_labeling_system",
    278: "entity_profiles",
    279: "transaction_search",
    280: "portfolio_holdings",
    281: "balance_history",
    282: "entity_pnl",
    283: "exchange_usage_intelligence",
    284: "top_counterparties",
    285: "visualizer_network_graph",
    286: "automated_trace_path_finding",
    287: "cross_chain_trace",
    288: "token_top_holders",
    289: "token_exchange_flows",
    290: "token_transaction_explorer",
    291: "custom_dashboards",
    292: "custom_alerts",
    293: "private_labels",
    294: "archive_historical_portfolio_snapshot",
    295: "ai_market_insights",
    296: "whale_movement_intelligence",
    297: "fraud_suspicious_activity_intelligence",
    298: "api_on_chain_intelligence",
    299: "cross_entity_decision_intelligence",
    300: "advanced_multi_asset_charting",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap276(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        276,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="entity_resolution_engine",
        params=params,
    )

async def _cap277(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        277,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="address_labeling_system",
        params=params,
    )

async def _cap278(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        278,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="entity_profiles",
        params=params,
    )

async def _cap279(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        279,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="transaction_search",
        params=params,
    )

async def _cap280(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        280,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="portfolio_holdings",
        params=params,
    )

async def _cap281(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        281,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="balance_history",
        params=params,
    )

async def _cap282(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        282,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="entity_pnl",
        params=params,
    )

async def _cap283(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        283,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="exchange_usage_intelligence",
        params=params,
    )

async def _cap284(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        284,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="top_counterparties",
        params=params,
    )

async def _cap285(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        285,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="visualizer_network_graph",
        params=params,
    )

async def _cap286(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        286,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="automated_trace_path_finding",
        params=params,
    )

async def _cap287(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        287,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_chain_trace",
        params=params,
    )

async def _cap288(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        288,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="token_top_holders",
        params=params,
    )

async def _cap289(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        289,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="token_exchange_flows",
        params=params,
    )

async def _cap290(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        290,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="token_transaction_explorer",
        params=params,
    )

async def _cap291(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        291,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="custom_dashboards",
        params=params,
    )

async def _cap292(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        292,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="custom_alerts",
        params=params,
    )

async def _cap293(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        293,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="private_labels",
        params=params,
    )

async def _cap294(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        294,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="archive_historical_portfolio_snapshot",
        params=params,
    )

async def _cap295(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        295,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="ai_market_insights",
        params=params,
    )

async def _cap296(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        296,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="whale_movement_intelligence",
        params=params,
    )

async def _cap297(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        297,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="fraud_suspicious_activity_intelligence",
        params=params,
    )

async def _cap298(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        298,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="api_on_chain_intelligence",
        params=params,
    )

async def _cap299(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        299,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="cross_entity_decision_intelligence",
        params=params,
    )

async def _cap300(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        300,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="advanced_multi_asset_charting",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    276: _cap276,
    277: _cap277,
    278: _cap278,
    279: _cap279,
    280: _cap280,
    281: _cap281,
    282: _cap282,
    283: _cap283,
    284: _cap284,
    285: _cap285,
    286: _cap286,
    287: _cap287,
    288: _cap288,
    289: _cap289,
    290: _cap290,
    291: _cap291,
    292: _cap292,
    293: _cap293,
    294: _cap294,
    295: _cap295,
    296: _cap296,
    297: _cap297,
    298: _cap298,
    299: _cap299,
    300: _cap300,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH12_DEDICATED_IDS,
        overlap_batch01_ids=BATCH12_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch12",
        not_dedicated_error=f"batch12: not a dedicated capability",
    )
