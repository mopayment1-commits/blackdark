"""Official batch 25 — from-scratch dedicated backends (IDs 601–625)."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from cap646.dedicated_common import addr as _addr
from cap646.dedicated_common import execute_dedicated_caps
from cap646.dedicated_common import sym as _sym

OFFICIAL_BATCH25_IDS: frozenset[int] = frozenset(range(601, 626))
BATCH25_DEDICATED_IDS: frozenset[int] = frozenset({601, 602, 603, 604, 605, 606, 607, 608, 609, 610, 611, 612, 613, 614, 615, 616, 617, 618, 619, 620, 621, 622, 623, 624, 625})
BATCH25_OVERLAP_BATCH01_IDS: frozenset[int] = frozenset()

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

async def _cap601(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap601 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap602(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap602 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap603(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap603 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap604(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap604 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap605(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap605 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap606(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap606 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap607(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap607 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap608(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap608 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap609(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap609 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap610(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap610 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap611(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap611 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap612(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap612 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap613(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap613 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap614(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap614 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap615(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap615 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap616(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap616 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap617(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap617 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap618(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap618 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap619(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap619 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap620(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap620 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap621(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap621 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap622(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap622 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap623(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap623 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap624(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap624 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

async def _cap625(*, symbol: str, address: str, params: dict[str, Any]) -> dict[str, Any]:
    from cap646.batch25_dedicated import _cap625 as _legacy_handler
    result = await _legacy_handler(symbol=symbol, address=address, params=params)
    from cap646.batch_spine import _enrich_v6_evidence
    return _enrich_v6_evidence(result, symbol=symbol)

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
        overlap_error="batch01 overlap for official batch25",
        not_dedicated_error=f"official batch25: not dedicated",
    )
