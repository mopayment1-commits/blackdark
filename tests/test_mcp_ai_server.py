"""Tests — #262 MCP for AI (AI Agent Server)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from bd_platform import mcp_ai_server as mcp


@pytest.fixture
def isolated_seed(tmp_path, monkeypatch):
    seed = tmp_path / "mcp_ai_server_seed.json"
    trace = tmp_path / "trace_log.jsonl"
    seed.write_text(
        json.dumps({
            "mcp_server_version": "1.0",
            "mcp_spec_compatible": "2025-03",
            "trace_retention_days": 90,
            "daily_quotas": {"free": 50, "pro": 5000, "enterprise": -1},
            "demo_api_keys": {
                "bd-demo-free-mcp-key-0001": {"tier": "free", "agent_id": "agent_test_free"},
                "bd-demo-pro-mcp-key-0001": {"tier": "pro", "agent_id": "agent_test_pro"},
                "bd-demo-enterprise-mcp-key": {"tier": "enterprise", "agent_id": "agent_test_ent"},
            },
        }),
        encoding="utf-8",
    )
    monkeypatch.setattr(mcp, "_SEED_PATH", seed)
    monkeypatch.setattr(mcp, "_TRACE_LOG", trace)
    from collections import defaultdict
    monkeypatch.setattr(mcp, "_rate_counters", defaultdict(lambda: defaultdict(int)))
    monkeypatch.setattr(mcp, "_rate_day", "")
    return seed


@pytest.fixture
def auth_headers():
    return {
        "api_key": "bd-demo-free-mcp-key-0001",
        "agent_fingerprint": "fp_test_agent_abc12345",
    }


@pytest.fixture
def mock_price_envelope():
    return {
        "ok": True,
        "data": {"price_usd": 98500.0, "change_24h_pct": 1.2, "exchange": "binance"},
        "metadata": {"fetched_at": "2026-08-25T13:20:00+00:00"},
        "timestamp": "2026-08-25T13:20:00+00:00",
    }


def test_tool_schemas_documented(isolated_seed):
    schemas = mcp.get_tool_schemas()
    names = [t["name"] for t in schemas["tools"]]
    assert "blackdark_get_price" in names
    assert "blackdark_get_onchain_metric" in names
    assert "blackdark_get_exchange_quality" in names
    for tool in schemas["tools"]:
        assert "inputSchema" in tool
        assert "outputSchema" in tool
        assert "examples" in tool
    assert schemas["mcp_server_version"] == "1.0"
    assert schemas["mcp_spec_compatible"] == "2025-03"


def test_no_anonymous_access(isolated_seed):
    result = mcp._resolve_agent("", None)
    assert result["ok"] is False
    result2 = mcp._resolve_agent("bd-demo-free-mcp-key-0001", None)
    assert result2["ok"] is False
    assert "fingerprint" in result2["error"]


def test_authentication_api_key_and_fingerprint(isolated_seed, auth_headers):
    result = mcp._resolve_agent(auth_headers["api_key"], auth_headers["agent_fingerprint"])
    assert result["ok"] is True
    assert result["agent_id"] == "agent_test_free"
    assert result["tier"] == "free"


def test_rate_limit_free_tier(isolated_seed, auth_headers):
    rate = mcp.check_mcp_rate_limit("agent_test_free", "free")
    assert rate["allowed"] is True
    assert rate["daily_limit"] == 50

    for _ in range(50):
        mcp._increment_rate("agent_test_free")
    rate2 = mcp.check_mcp_rate_limit("agent_test_free", "free")
    assert rate2["allowed"] is False
    assert rate2["rate_limited"] is True


def test_rate_limit_enterprise_unlimited(isolated_seed):
    rate = mcp.check_mcp_rate_limit("agent_test_ent", "enterprise")
    assert rate["allowed"] is True
    assert rate["daily_limit"] == "unlimited"
    assert rate.get("priority_queue") is True


@pytest.mark.asyncio
async def test_get_price_with_evidence(isolated_seed, auth_headers, mock_price_envelope, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_price",
        AsyncMock(return_value=mock_price_envelope),
    )
    import bd_platform.verifiable_ai_engine as vai
    monkeypatch.setattr(vai, "_freshness_for_asset", lambda asset, feed_id="price": {"latency_ms": 80, "stale": False})

    result = await mcp.call_mcp_tool(
        "blackdark_get_price",
        {"asset": "BTC"},
        api_key=auth_headers["api_key"],
        agent_fingerprint=auth_headers["agent_fingerprint"],
    )
    assert result["ok"] is True
    assert result["price_usd"] == 98500.0
    assert len(result["evidence"]) >= 1
    assert result["evidence"][0].get("freshness_ms") == 80
    assert result["disclaimer_hideable"] is False
    assert "BLACKDARK MCP Server" in result["disclaimer"]
    assert result["mcp"]["grounding_layer"] == "#230"


@pytest.mark.asyncio
async def test_fail_closed_no_data(isolated_seed, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_price",
        AsyncMock(return_value={"ok": False, "data": {}}),
    )

    result = await mcp.call_mcp_tool(
        "blackdark_get_price",
        {"asset": "BTC"},
        api_key=auth_headers["api_key"],
        agent_fingerprint=auth_headers["agent_fingerprint"],
    )
    assert result["ok"] is False
    assert result["error"] == "Data unavailable"
    assert result["fail_closed"] is True


@pytest.mark.asyncio
async def test_tool_traceability(isolated_seed, auth_headers, mock_price_envelope, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_price",
        AsyncMock(return_value=mock_price_envelope),
    )
    import bd_platform.verifiable_ai_engine as vai
    monkeypatch.setattr(vai, "_freshness_for_asset", lambda asset, feed_id="price": {"latency_ms": 50, "stale": False})

    await mcp.call_mcp_tool(
        "blackdark_get_price",
        {"asset": "BTC"},
        api_key=auth_headers["api_key"],
        agent_fingerprint=auth_headers["agent_fingerprint"],
    )
    trace = mcp.get_tool_trace(limit=10)
    assert trace["trace_retention_days"] == 90
    assert trace["count"] >= 1
    entry = trace["entries"][-1]
    assert entry["agent_id"] == "agent_test_free"
    assert entry["tool_called"] == "blackdark_get_price"
    assert entry["parameters"] == {"asset": "BTC"}
    assert "response_hash" in entry
    assert "timestamp" in entry


@pytest.mark.asyncio
async def test_onchain_metric_tool(isolated_seed, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unified_api_platform.fetch_onchain",
        AsyncMock(return_value={
            "ok": True,
            "data": {"mvrv_proxy": 1.8, "sopr_proxy": 1.02, "nvt": 45.0},
            "metadata": {"fetched_at": "2026-08-25T13:20:00+00:00"},
        }),
    )
    import bd_platform.verifiable_ai_engine as vai
    monkeypatch.setattr(vai, "_freshness_for_asset", lambda asset, feed_id="onchain": {"latency_ms": 100, "stale": False})

    result = await mcp.call_mcp_tool(
        "blackdark_get_onchain_metric",
        {"asset": "BTC", "metric": "mvrv_proxy"},
        api_key=auth_headers["api_key"],
        agent_fingerprint=auth_headers["agent_fingerprint"],
    )
    assert result["ok"] is True
    assert result["value"] == 1.8
    assert len(result["evidence"]) >= 1


@pytest.mark.asyncio
async def test_exchange_quality_tool(isolated_seed, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "bd_platform.connector_coverage_map.build_coverage_map",
        AsyncMock(return_value={
            "venues": [{
                "venue_id": "binance",
                "live": True,
                "latency_ms": 120.0,
                "pairs": 245,
                "probed_at": "2026-08-25T13:20:00+00:00",
                "status_display": "Binance: ✅ 245 pairs",
            }],
        }),
    )

    result = await mcp.call_mcp_tool(
        "blackdark_get_exchange_quality",
        {"exchange": "binance"},
        api_key=auth_headers["api_key"],
        agent_fingerprint=auth_headers["agent_fingerprint"],
    )
    assert result["ok"] is True
    assert result["live"] is True
    assert result["quality_score"] > 0
    assert len(result["evidence"]) >= 1


def test_not_standalone(isolated_seed):
    status = mcp.mcp_ai_server_status()
    assert status["standalone"] is False
    assert status["feature_id"] == 262
    assert 230 in status["integrated_with"]
    assert status["mcp_server_version"] == "1.0"
    assert status["disclaimer_hideable"] is False


def test_api_routes(isolated_seed):
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    headers = {
        "X-API-Key": "bd-demo-free-mcp-key-0001",
        "X-Agent-Fingerprint": "fp_test_agent_abc12345",
    }
    assert c.get("/api/platform/mcp/status").status_code == 200
    status = c.get("/api/platform/mcp/status").json()
    assert status["feature_id"] == 262
    assert c.get("/api/platform/mcp/tools/schema").status_code == 200
    assert c.get("/api/platform/mcp/trace", headers=headers).status_code == 200


def test_full_seed_exists():
    seed = json.loads(Path("data/mcp_ai_server_seed.json").read_text(encoding="utf-8"))
    assert seed["feature_id"] == 262
    assert seed["standalone"] is False
    assert seed["mcp_server_version"] == "1.0"
