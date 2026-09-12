"""Invoke underlying catalog handlers for batch17 dedicated backends (no spine recursion)."""

from __future__ import annotations

from typing import Any

from cap646.handlers.ai import handle_ai_capability
from cap646.handlers.alerts import handle_alerts_capability
from cap646.handlers.data import handle_data_capability
from cap646.handlers.derivatives import handle_derivatives_capability
from cap646.handlers.execution import handle_execution_capability
from cap646.handlers.institutional import handle_institutional_capability
from cap646.handlers.market import handle_market_capability
from cap646.handlers.onchain import handle_onchain_capability
from cap646.handlers.platform import handle_platform_capability
from cap646.handlers.verified import handle_verified_capability
from cap646.waves import WAVE_D

WAVE_D_SET = set(WAVE_D)
VERIFIED_IDS = frozenset({49, 50, 62, 63, 632, 638, 639, 640, 641})


def _route_underlying_handler(track: str, name: str, capability_id: int):
    """Mirror cap646.runtime._route_handler but NEVER return batch0x spine handlers."""
    nl = name.lower()
    if capability_id == 329:
        return handle_institutional_capability
    if capability_id in VERIFIED_IDS:
        return handle_verified_capability
    if track == "T03" or any(k in nl for k in ("data quality", "ingestion", "freshness", "storage", "pipeline", "normalization", "provenance")):
        return handle_data_capability
    if track in {"T04", "T11"} or any(k in nl for k in ("market", "order book", "spot", "reference rate", "ohlcv", "sentiment intelligence", "dex volume")):
        if "sentiment" in nl and track in {"T12", "T09"}:
            return handle_ai_capability
        return handle_market_capability
    if track in {"T05", "T08", "T10"} and any(k in nl for k in ("futures", "funding", "liquidation", "open interest", "options", "derivative", "perp")):
        return handle_derivatives_capability
    if track in {"T06", "T07", "T08"} and any(k in nl for k in ("arbitrage", "execution", "risk", "spread", "hedge", "trading")):
        return handle_execution_capability
    if track == "T09" or any(k in nl for k in ("on-chain", "on chain", "wallet", "whale", "transaction", "tvl", "gas")):
        if "alert" in nl:
            return handle_alerts_capability
        return handle_onchain_capability
    if track == "T13" or "alert" in nl:
        return handle_alerts_capability
    if track in {"T02", "T15", "T16", "T17", "T01"} and any(
        k in nl for k in ("institutional", "security", "api", "capacity", "chaos", "gateway", "entitlement", "architecture", "encryption", "backtesting", "delivery", "audit")
    ):
        return handle_institutional_capability
    if track in {"T12", "T14", "T16"} or any(k in nl for k in ("ai", "oracle", "decision", "prediction", "signal", "research", "nlp", "mcp")):
        return handle_ai_capability
    if track == "T13":
        return handle_alerts_capability
    if track == "T17" and capability_id in {638, 639, 640, 641, 642}:
        return handle_ai_capability
    if capability_id in WAVE_D_SET:
        return handle_platform_capability
    return handle_platform_capability


async def invoke_underlying(capability_id: int, *, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Call generic domain handler for batch17 IDs — avoids batch spine re-entry."""
    from cap646.catalog import catalog_by_id

    params = dict(params or {})
    row = catalog_by_id().get(capability_id)
    if not row:
        return {"success": False, "error": "unknown_capability_id", "capability_id": capability_id}

    handler = _route_underlying_handler(row["track"], row["capability"], capability_id)
    try:
        if handler is handle_institutional_capability:
            result = await handler(capability_id, params=params, user=None, org_id=None)
        else:
            result = await handler(capability_id, params=params)
    except Exception as exc:
        return {"success": False, "error": str(exc), "handler": handler.__name__, "capability_id": capability_id}

    if not isinstance(result, dict):
        return {"success": False, "result": result, "capability_id": capability_id}
    result.setdefault("capability_id", capability_id)
    if "success" not in result and not result.get("error"):
        result["success"] = True
    return result
