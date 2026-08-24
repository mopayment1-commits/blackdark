"""Tests — silent data layer (#97, #95, #93)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.decision_engine_inputs import gather_decision_inputs
from blackdark.ingestion.exchange_flow_metric import compute_token_exchange_flows
from blackdark.ingestion.theblock_connector import _parse_rss, fetch_theblock_research_context


RSS_SAMPLE = """<?xml version="1.0"?>
<rss><channel>
<item><title>Ethereum ETF sees institutional inflows</title>
<link>https://example.com/1</link>
<pubDate>Mon, 24 Aug 2026 12:00:00 GMT</pubDate>
<description>BlackRock and Fidelity lead institutional accumulation.</description></item>
</channel></rss>"""


def test_parse_theblock_rss_themes():
    rows = _parse_rss(RSS_SAMPLE)
    assert len(rows) == 1
    assert "etf_institutional" in rows[0]["themes"]
    assert "ethereum" in rows[0]["themes"]


@pytest.mark.asyncio
async def test_exchange_flow_filters_internal():
    with patch(
        "blackdark.ingestion.exchange_flow_metric._whale_transfer_rows",
        new=AsyncMock(
            return_value=[
                {
                    "from": "0x28c6c06298d514db089934071355e5743bf21d60",
                    "to": "0x21a31ee1afc51d94c2e590cc82992f2f6f6b15c2",
                    "amount_usd": 1_000_000,
                    "exchange": "binance",
                    "flow_type": "internal",
                },
                {
                    "from": "0xexternal",
                    "to": "0x28c6c06298d514db089934071355e5743bf21d60",
                    "amount_usd": 2_000_000,
                    "exchange": "binance",
                    "flow_type": "deposit",
                },
            ]
        ),
    ):
        out = await compute_token_exchange_flows("SHIB")
    assert out["ok"] is True
    assert out["internal_transfers_filtered"] >= 1
    assert out["inflow_usd"] == 2_000_000
    assert "Binance" in (out.get("headline") or "")


@pytest.mark.asyncio
async def test_theblock_connector_mock():
    fake = {"ok": True, "data": RSS_SAMPLE, "latency_ms": 20}
    with patch(
        "blackdark.ingestion.theblock_connector._CACHE.http_get",
        new=AsyncMock(return_value=fake),
    ):
        out = await fetch_theblock_research_context(limit=5)
    assert out["ok"] is True
    assert out["article_count"] >= 1
    assert out["ai_context_line"] is not None


@pytest.mark.asyncio
async def test_solana_rpc_balance_mock():
    from blackdark.ingestion.solana_rpc_connector import fetch_solana_balance

    with patch(
        "blackdark.ingestion.solana_rpc_connector._rpc_call",
        new=AsyncMock(return_value={"ok": True, "result": {"value": 2_000_000_000}, "endpoint": "test"}),
    ):
        out = await fetch_solana_balance("So11111111111111111111111111111111111111112")
    assert out["ok"] is True
    assert out["balance_sol"] == 2.0
    assert out["rpc_tier"] in {"public", "dedicated"}


@pytest.mark.asyncio
async def test_decision_inputs_mock():
    with patch(
        "blackdark.ingestion.exchange_flow_metric.compute_token_exchange_flows",
        new=AsyncMock(
            return_value={
                "ok": True,
                "headline": "Large ETH inflow to Binance detected — AI adjusts risk score",
                "risk_score_delta": 5.0,
                "net_flow_usd": 1_000_000,
            }
        ),
    ), patch(
        "blackdark.ingestion.theblock_connector.fetch_theblock_research_context",
        new=AsyncMock(return_value={"ok": True, "ai_context_line": "AI analyzed ETF research."}),
    ), patch(
        "blackdark.ingestion.solana_rpc_connector.fetch_solana_chain_health",
        new=AsyncMock(return_value={"ok": True, "slot": 123}),
    ):
        out = await gather_decision_inputs("ETH")
    assert out["ok"] is True
    assert out["feature"] == "#48"
    assert out["risk_score_delta"] == 5.0
    assert len(out["headlines"]) >= 1


def test_data_layer_status_api(tmp_path, monkeypatch):
    import asyncio

    import config
    import database

    db_path = tmp_path / "dl.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    r = c.get("/api/platform/ingestion/data-layer/status")
    assert r.status_code == 200
    body = r.json()
    assert "theblock" in body
    assert "solana_rpc" in body
