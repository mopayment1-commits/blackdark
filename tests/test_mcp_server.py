"""Tests — MCP Server (#179) tool schemas and handlers."""

from __future__ import annotations

import os

import pytest
from fastapi import HTTPException

from blackdark.mcp.schemas import MCP_TOOLS
from blackdark.mcp.server import _verify_mcp_auth, handle_jsonrpc_async
from blackdark.mcp.tools import call_tool, list_tools


def test_tool_schemas_present():
    names = {t["name"] for t in MCP_TOOLS}
    assert "get_price" in names
    assert "get_market_health" in names
    assert "get_risk_score" in names
    assert len(MCP_TOOLS) >= 5


def test_list_tools_matches_schemas():
    tools = list_tools()
    assert len(tools) == len(MCP_TOOLS)
    for tool in tools:
        assert "inputSchema" in tool
        assert "description" in tool


def test_mcp_auth_required():
    with pytest.raises(HTTPException) as exc:
        _verify_mcp_auth(None)
    assert exc.value.status_code == 401


def test_mcp_auth_with_key(monkeypatch):
    monkeypatch.setenv("BLACKDARK_MCP_API_KEY", "mcp-test-key-12345678")
    _verify_mcp_auth("mcp-test-key-12345678")  # no raise


@pytest.mark.asyncio
async def test_tools_list_jsonrpc(monkeypatch):
    monkeypatch.setenv("BLACKDARK_MCP_API_KEY", "mcp-test-key-12345678")
    resp = await handle_jsonrpc_async(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}},
        api_key="mcp-test-key-12345678",
    )
    assert resp["result"]["tools"]
    assert len(resp["result"]["tools"]) >= 5


@pytest.mark.asyncio
async def test_get_price_tool_mocked(monkeypatch):
    async def fake_price(asset="BTC"):
        return {
            "ok": True,
            "asset": "BTC",
            "price_usd": 50000,
            "freshness": {"source": "test", "as_of": "2026-01-01"},
        }

    monkeypatch.setattr("blackdark.mcp.tools.get_price_intelligence", fake_price)
    out = await call_tool("get_price", {"asset": "BTC"})
    assert out["ok"] is True
    assert out["read_only"] is True
    assert out["execution_allowed"] is False
    assert out["result"]["price_usd"] == 50000


@pytest.mark.asyncio
async def test_unknown_tool():
    out = await call_tool("execute_trade", {})
    assert out["ok"] is False
    assert out["error"] == "unknown_tool"
