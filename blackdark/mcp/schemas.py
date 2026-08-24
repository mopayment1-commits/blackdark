"""
MCP tool schemas — Feature #179.

Read-only tools with clear JSON Schema definitions for AI agents.
"""

from __future__ import annotations

from typing import Any

MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "get_price",
        "description": "Get aggregated spot price for a crypto asset with source and freshness metadata. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {
                    "type": "string",
                    "description": "Asset symbol e.g. BTC, ETH",
                    "default": "BTC",
                }
            },
            "required": [],
        },
    },
    {
        "name": "get_market_health",
        "description": "Get market health score and pillar breakdown for an asset. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "Asset symbol", "default": "BTC"}
            },
            "required": [],
        },
    },
    {
        "name": "get_risk_score",
        "description": "Get experimental risk/confidence score for an asset. Read-only — not investment advice.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "Asset symbol", "default": "BTC"}
            },
            "required": [],
        },
    },
    {
        "name": "get_connector_registry",
        "description": "Get connector health registry (exchange coverage and freshness). Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "asset": {"type": "string", "description": "Probe asset for certification", "default": "BTC"}
            },
            "required": [],
        },
    },
    {
        "name": "get_daily_brief",
        "description": "Get latest BLACKDARK Daily Brief insight with evidence-linked claims. Read-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max insights", "default": 3, "minimum": 1, "maximum": 10}
            },
            "required": [],
        },
    },
]
