"""
MCP tool handlers — Feature #179.

Read-only wrappers around canonical intelligence service.
No execution permissions — data access only.
"""

from __future__ import annotations

import logging
from typing import Any

from blackdark.api.canonical_intelligence import (
    get_market_health_intelligence,
    get_price_intelligence,
    get_risk_score_intelligence,
)

logger = logging.getLogger("BLACKDARK.MCP.Tools")

_FEATURE_ID = 179


async def call_tool(name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
    """Dispatch MCP tool call — returns structured content with freshness metadata."""
    args = arguments or {}
    asset = str(args.get("asset") or "BTC").upper()

    if name == "get_price":
        data = await get_price_intelligence(asset)
    elif name == "get_market_health":
        data = await get_market_health_intelligence(asset)
    elif name == "get_risk_score":
        data = await get_risk_score_intelligence(asset)
    elif name == "get_connector_registry":
        from bd_platform.flexible_connector_microservice import connector_registry_dashboard

        data = await connector_registry_dashboard(asset)
    elif name == "get_daily_brief":
        from bd_platform.quicktake_insight_feed import list_published_insights

        limit = int(args.get("limit") or 3)
        data = list_published_insights(limit=limit)
    else:
        return {
            "ok": False,
            "error": "unknown_tool",
            "tool": name,
            "feature_id": _FEATURE_ID,
        }

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "tool": name,
        "read_only": True,
        "execution_allowed": False,
        "result": data,
        "freshness": data.get("freshness") if isinstance(data, dict) else None,
        "source_metadata": {
            "product": "BLACKDARK MCP",
            "wrapper": "canonical_intelligence_service",
            "no_synthetic_success": True,
        },
    }


def list_tools() -> list[dict[str, Any]]:
    from blackdark.mcp.schemas import MCP_TOOLS

    return MCP_TOOLS
