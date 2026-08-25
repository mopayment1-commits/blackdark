"""
AI Market Data Grounding Layer — Feature #230 Middleware (Sprint 1).

Middleware between AI surfaces and Verifiable AI Engine. Ensures tool-grounded
retrieval across Portfolio AI, Market Radar, Smart Alert Engine, Scenario Engine,
and Thesis Workspace. NOT a standalone product.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("BLACKDARK.AIGroundingMiddleware")

_FEATURE_ID = 230
_GROUNDING_LAYER_NAME = "AI Market Data Grounding Layer"
_STANDALONE = False

SUPPORTED_SURFACES = (
    "portfolio_ai",
    "market_radar",
    "smart_alert_engine",
    "scenario_engine",
    "thesis_workspace",
    "ai_chatbot",
    "decision_intelligence_engine",
    "mcp_ai_server",
)


async def ground_surface_response(
    surface: str,
    query: str,
    *,
    asset: str | None = None,
    answer: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Middleware entry — all AI surfaces must route market-fact queries through here.
    Fail-closed: tool failure yields no model-only facts.
    """
    from bd_platform.verifiable_ai_engine import ground_ai_response

    if surface not in SUPPORTED_SURFACES:
        logger.warning("grounding middleware: unregistered surface %s", surface)

    result = await ground_ai_response(
        query,
        asset=asset,
        answer=answer,
        context={"surface": surface, "middleware": _GROUNDING_LAYER_NAME},
    )

    if payload:
        merged = {**payload, **result}
    else:
        merged = result

    merged["ai_grounding"] = {
        "feature_id": _FEATURE_ID,
        "layer": _GROUNDING_LAYER_NAME,
        "surface": surface,
        "middleware": True,
        "tool_grounded": bool(result.get("evidence")),
        "fail_closed": result.get("fail_closed", False),
        "oracle_api_parity": True,
    }
    return merged


def grounding_middleware_status() -> dict[str, Any]:
    from bd_platform.verifiable_ai_engine import verifiable_ai_status

    base = verifiable_ai_status()
    return {
        **base,
        "grounding_layer_name": _GROUNDING_LAYER_NAME,
        "middleware": True,
        "supported_surfaces": list(SUPPORTED_SURFACES),
        "mcp_relationship": {
            "feature_230": "Internal grounding — ensures AI response quality",
            "feature_262": "External MCP access — developer-facing agents",
            "shared_rule": "No model-only market facts",
            "same_data_path": True,
        },
        "not_standalone": _STANDALONE,
    }
