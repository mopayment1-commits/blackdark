"""Official Batch 25 dedicated backends — goal-specific payloads (v6 §2.1).

Auto-generated — institutional 25-cap batch 25 (IDs 601–625).
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import make_wrap_binding
from cap646.dedicated_common import sym as _sym
from cap646.dedicated_common import wrap_with_backend

OFFICIAL_BATCH25_IDS: frozenset[int] = frozenset(range(601, 626))
BATCH25_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()
BATCH25_DEDICATED_IDS: frozenset[int] = frozenset({601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625})

GENERIC_SURFACES = frozenset(
    {"onchain_intelligence", "ai_decision_intelligence", "market_data", "smart_alerts", "platform_codepath"}
)

EXPECTED_SURFACE: dict[int, str] = {
    601: "visual_transaction_graph",
    602: "developer_wallet_tracker",
    603: "miner_flow_monitor",
    604: "token_unlock_forecaster",
    605: "governance_sentiment_monitor",
    606: "dev_health_score",
    607: "financial_health_scoring",
    608: "custom_ratio_engine",
    609: "funding_rate_listener",
    610: "funding_arbitrage_engine",
    611: "funding_rate_heatmap_engine",
    612: "spread_calculation_engine",
    613: "liquidation_screener",
    614: "dex_liquidity_listener",
    615: "gas_cost_predictor",
    616: "yield_delta_listener",
    617: "yield_arbitrage_engine",
    618: "yield_optimization_module",
    619: "trend_metric_collector",
    620: "mtf_core_logic",
    621: "pattern_recognition_engine",
    622: "prediction_trend_analyzer",
    623: "execution_latency_monitor",
    624: "low_latency_execution_node",
    625: "rust_execution_module",
}

_wrap = make_wrap_binding(EXPECTED_SURFACE)

async def _cap601(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        601,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="visual_transaction_graph",
        params=params,
    )

async def _cap602(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        602,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="developer_wallet_tracker",
        params=params,
    )

async def _cap603(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        603,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="miner_flow_monitor",
        params=params,
    )

async def _cap604(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        604,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="token_unlock_forecaster",
        params=params,
    )

async def _cap605(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        605,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="governance_sentiment_monitor",
        params=params,
    )

async def _cap606(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        606,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dev_health_score",
        params=params,
    )

async def _cap607(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        607,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="financial_health_scoring",
        params=params,
    )

async def _cap608(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        608,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="custom_ratio_engine",
        params=params,
    )

async def _cap609(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        609,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="funding_rate_listener",
        params=params,
    )

async def _cap610(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        610,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="funding_arbitrage_engine",
        params=params,
    )

async def _cap611(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        611,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="funding_rate_heatmap_engine",
        params=params,
    )

async def _cap612(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        612,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="spread_calculation_engine",
        params=params,
    )

async def _cap613(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        613,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="liquidation_screener",
        params=params,
    )

async def _cap614(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        614,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="dex_liquidity_listener",
        params=params,
    )

async def _cap615(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.fallbacks import resolve_gas_usd

    chain = str(params.get("chain") or "ethereum")
    gas = await resolve_gas_usd(chain)
    body = _wrap(
        615,
        symbol=symbol,
        payload_key="gas_cost_predictor",
        payload={**gas, "chain": chain, "symbol": symbol},
    )
    body["gas_usd"] = gas.get("gas_usd")
    return body

async def _cap616(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        616,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="yield_delta_listener",
        params=params,
    )

async def _cap617(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        617,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="yield_arbitrage_engine",
        params=params,
    )

async def _cap618(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        618,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="yield_optimization_module",
        params=params,
    )

async def _cap619(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        619,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="trend_metric_collector",
        params=params,
    )

async def _cap620(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        620,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="mtf_core_logic",
        params=params,
    )

async def _cap621(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        621,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="pattern_recognition_engine",
        params=params,
    )

async def _cap622(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        622,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="prediction_trend_analyzer",
        params=params,
    )

async def _cap623(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        623,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="execution_latency_monitor",
        params=params,
    )

async def _cap624(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        624,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="low_latency_execution_node",
        params=params,
    )

async def _cap625(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    return await wrap_with_backend(
        625,
        expected_surface=EXPECTED_SURFACE,
        symbol=symbol,
        payload_key="rust_execution_module",
        params=params,
    )

_DISPATCH: dict[int, Callable[..., Awaitable[dict[str, Any]]]] = {
    601: _cap601,
    602: _cap602,
    603: _cap603,
    604: _cap604,
    605: _cap605,
    606: _cap606,
    607: _cap607,
    608: _cap608,
    609: _cap609,
    610: _cap610,
    611: _cap611,
    612: _cap612,
    613: _cap613,
    614: _cap614,
    615: _cap615,
    616: _cap616,
    617: _cap617,
    618: _cap618,
    619: _cap619,
    620: _cap620,
    621: _cap621,
    622: _cap622,
    623: _cap623,
    624: _cap624,
    625: _cap625,
}


async def execute(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    return await execute_dedicated_caps(
        capability_id,
        params=params,
        dedicated_ids=BATCH25_DEDICATED_IDS,
        overlap_batch01_ids=BATCH25_OVERLAP_BATCH01_IDS,
        dispatch=_DISPATCH,
        overlap_error="batch01 overlap for batch25",
        not_dedicated_error=f"batch25: not a dedicated capability",
    )
