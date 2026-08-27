"""Tests — silent data layer batch 4 (#85, #86, #87)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from blackdark.ingestion.order_flow_intelligence import (
    _aggregate_trades,
    _cross_validate_kline,
    _reversal_probability_from_series,
    compute_order_flow_intelligence,
)
from blackdark.ingestion.polygon_io_connector import fetch_polygon_macro_context
from blackdark.ingestion.polygonscan_connector import fetch_polygon_onchain_health


def test_aggregate_trades_buckets_and_sides():
    trades = [
        {"p": "1000", "q": "0.01", "m": False},  # $10 aggressive buy — retail
        {"p": "1000", "q": "5", "m": True},  # $5000 aggressive sell — medium
        {"p": "1000", "q": "200", "m": False},  # $200k aggressive buy — whale
    ]
    out = _aggregate_trades(trades)
    assert out["aggressive_buy_usd"] > out["aggressive_sell_usd"]
    assert out["buckets"]["whale"]["aggressive_buy_usd"] == 200000.0
    assert out["qa_issues"] == []


def test_cross_validate_kline_qa():
    ok = _cross_validate_kline(agg_buy=90, kline_taker_buy_quote=100, tolerance=0.15)
    assert ok["match_valid"] is True
    bad = _cross_validate_kline(agg_buy=10, kline_taker_buy_quote=100, tolerance=0.15)
    assert bad["match_valid"] is False


def test_reversal_probability_requires_history():
    short = [{"taker_buy_ratio": 0.7}] * 8
    assert _reversal_probability_from_series(short) is None


@pytest.mark.asyncio
async def test_order_flow_intelligence_mock():
    fake_klines = [
        [1, "0", "0", "0", "0", "100", 0, "1000", 10, "70", "0", "0"],
        [2, "0", "0", "0", "0", "100", 0, "1000", 10, "68", "0", "0"],
        [3, "0", "0", "0", "0", "100", 0, "1000", 10, "66", "0", "0"],
        [4, "0", "0", "0", "0", "100", 0, "1000", 10, "48", "0", "0"],
    ]
    fake_trades = [{"p": "1000", "q": "0.95", "m": False}]

    async def _fake_klines(*_a, **_k):
        return fake_klines

    async def _fake_agg(*_a, **_k):
        return {"ok": True, "data": fake_trades, "cache_hit": False}

    with patch(
        "blackdark.ingestion.order_flow_intelligence._fetch_klines",
        side_effect=_fake_klines,
    ), patch.object(
        __import__("blackdark.ingestion.order_flow_intelligence", fromlist=["_CACHE"])._CACHE,
        "http_get_json",
        side_effect=_fake_agg,
    ):
        from blackdark.ingestion import order_flow_intelligence as ofi

        ofi._CACHE._store.clear()
        out = await compute_order_flow_intelligence("ETH", limit=4, agg_limit=10)

    assert out["ok"] is True
    assert out["trade_side_qa"]["passed_bars"] == 4
    assert out["aggressive_flow"]["trade_count"] == 1


@pytest.mark.asyncio
async def test_polygon_io_fallback_without_key():
    with patch(
        "blackdark.ingestion.investing_com_connector.fetch_investing_news_context",
        new=AsyncMock(
            return_value={
                "ok": True,
                "ai_context_line": "AI analyzed macro news",
                "articles": [{"high_impact": True, "impact_tags": ["fed"]}],
            }
        ),
    ):
        out = await fetch_polygon_macro_context()
    assert out["feature"] == "#86"
    assert out["data_state"] == "DEGRADED"
    assert out["fallback"]["ok"] is True


@pytest.mark.asyncio
async def test_polygonscan_rpc_fallback():
    with patch(
        "blackdark.ingestion.polygonscan_connector._rpc_block_number",
        new=AsyncMock(return_value={"ok": True, "block_number": 12345678, "source": "polygon_rpc"}),
    ):
        from blackdark.ingestion import polygonscan_connector as pc

        pc._CACHE._store.clear()
        out = await fetch_polygon_onchain_health()
    assert out["ok"] is True
    assert out["block_number"] == 12345678
    assert "Polygon on-chain data included" in out["user_facing_note"]
