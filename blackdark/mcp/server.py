"""
MCP Server for AI Agents — Feature #179.

Minimal JSON-RPC 2.0 MCP-compatible server (stdio + HTTP router).
Read-only tools — no execution permissions.
Auth: X-API-Key / BLACKDARK_MCP_API_KEY required.
"""

from __future__ import annotations

import json
import logging
import os
import sys
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Body, Header, HTTPException

from blackdark.mcp.schemas import MCP_TOOLS
from blackdark.mcp.tools import call_tool, list_tools

logger = logging.getLogger("BLACKDARK.MCP.Server")

_FEATURE_ID = 179
MCP_PROTOCOL_VERSION = "2024-11-05"

mcp_router = APIRouter(tags=["mcp-server"])


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _verify_mcp_auth(api_key: str | None) -> None:
    expected = (
        os.getenv("BLACKDARK_MCP_API_KEY")
        or os.getenv("BLACKDARK_PUBLIC_API_KEY")
        or os.getenv("ADMIN_API_KEY")
        or ""
    ).strip()
    if not expected:
        # Dev mode — allow if key present and long enough
        if not api_key or len(api_key.strip()) < 8:
            raise HTTPException(status_code=401, detail="BLACKDARK_MCP_API_KEY required")
        return
    if not api_key or api_key.strip() != expected:
        raise HTTPException(status_code=401, detail="Invalid MCP API key")


def handle_jsonrpc_sync(request: dict[str, Any], *, api_key: str | None = None) -> dict[str, Any]:
    """Process JSON-RPC for stdio mode (sync wrapper)."""
    import asyncio

    return asyncio.run(handle_jsonrpc_async(request, api_key=api_key))


async def handle_jsonrpc_async(request: dict[str, Any], *, api_key: str | None = None) -> dict[str, Any]:
    """Process single JSON-RPC MCP request."""
    _verify_mcp_auth(api_key)
    req_id = request.get("id")
    method = str(request.get("method") or "")
    params = request.get("params") or {}

    try:
        if method == "initialize":
            result = {
                "protocolVersion": MCP_PROTOCOL_VERSION,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "blackdark-mcp", "version": "1.0.0"},
            }
        elif method == "tools/list":
            result = {"tools": MCP_TOOLS}
        elif method == "tools/call":
            tool_name = str((params.get("name") or ""))
            arguments = params.get("arguments") or {}
            payload = await call_tool(tool_name, arguments)
            result = {
                "content": [{"type": "text", "text": json.dumps(payload, default=str)}],
                "isError": not payload.get("ok", False),
            }
        else:
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }
        return {"jsonrpc": "2.0", "id": req_id, "result": result}
    except HTTPException as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": exc.status_code, "message": str(exc.detail)},
        }
    except Exception as exc:
        logger.exception("MCP handler error")
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32603, "message": str(exc)},
        }


@mcp_router.post("/mcp/jsonrpc")
async def mcp_jsonrpc_http(
    body: dict[str, Any] = Body(...),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    """HTTP JSON-RPC endpoint for MCP clients."""
    return await handle_jsonrpc_async(body, api_key=x_api_key)


@mcp_router.get("/mcp/tools")
async def mcp_tools_list(x_api_key: str | None = Header(None, alias="X-API-Key")):
    """List MCP tool schemas (read-only)."""
    _verify_mcp_auth(x_api_key)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "tools": list_tools(),
        "read_only": True,
        "execution_allowed": False,
        "auth": "X-API-Key required",
        "timestamp": _utcnow(),
    }


@mcp_router.post("/mcp/tools/call")
async def mcp_tool_call_http(
    body: dict[str, Any] = Body(...),
    x_api_key: str | None = Header(None, alias="X-API-Key"),
):
    """Direct HTTP tool invocation for testing."""
    _verify_mcp_auth(x_api_key)
    name = str(body.get("name") or "")
    arguments = body.get("arguments") or {}
    if not name:
        raise HTTPException(status_code=400, detail="tool name required")
    return await call_tool(name, arguments)


@mcp_router.get("/mcp/status")
async def mcp_server_status():
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "BLACKDARK MCP Server for AI Agents",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "tools": [t["name"] for t in MCP_TOOLS],
        "read_only": True,
        "execution_allowed": False,
        "auth": "X-API-Key / BLACKDARK_MCP_API_KEY",
        "endpoints": {
            "jsonrpc": "POST /mcp/jsonrpc",
            "tools_list": "GET /mcp/tools",
            "tool_call": "POST /mcp/tools/call",
        },
        "parent_feature": 162,
        "timestamp": _utcnow(),
    }


def run_stdio_server() -> None:
    """Stdio JSON-RPC loop for Claude/Cursor MCP integration."""
    api_key = os.getenv("BLACKDARK_MCP_API_KEY") or os.getenv("BLACKDARK_PUBLIC_API_KEY") or ""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue
        response = handle_jsonrpc_sync(request, api_key=api_key or None)
        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    run_stdio_server()
