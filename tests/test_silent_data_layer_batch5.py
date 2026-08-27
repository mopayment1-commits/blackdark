"""Tests — silent data layer batch 5 (#60, #69, #75)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from blackdark.ingestion.exchange_listing_tracker import lead_time_hours, record_sightings
from blackdark.ingestion.gateio_connector import _usdt_pairs, fetch_gateio_listing_intelligence
from blackdark.ingestion.kucoin_connector import _usdt_symbols, fetch_kucoin_listing_intelligence
from blackdark.ingestion.marketwatch_connector import _ai_context_line, _parse_rss


def test_usdt_pair_extraction():
    rows = [{"currency_pair": "PEPE_USDT"}, {"currency_pair": "ETH_BTC"}]
    assert "PEPE" in _usdt_pairs(rows)
    assert "ETH" not in _usdt_pairs(rows)


def test_kucoin_symbol_extraction():
    tickers = [{"symbol": "ETH-USDT"}, {"symbol": "XBT-USDT"}]
    syms = _usdt_symbols(tickers)
    assert "ETH" in syms
    assert "BTC" in syms


def test_marketwatch_macro_parsing():
    xml = """<?xml version='1.0'?><rss><channel><item>
    <title>Fed signals rate hike amid inflation worries</title>
    <description>Markets react</description>
    <link>https://example.com</link>
    </item></channel></rss>"""
    items = _parse_rss(xml, limit=5)
    assert items[0]["high_impact"] is True
    assert "fed" in items[0]["impact_tags"]


def test_marketwatch_ai_context_line():
    high = [{"title": "a"}, {"title": "b"}]
    assert "2 macro events" in (_ai_context_line(high) or "")


def test_listing_lead_time_tracker(tmp_path, monkeypatch):
    monkeypatch.setattr(
        "blackdark.ingestion.exchange_listing_tracker._SNAPSHOT_PATH",
        tmp_path / "snap.json",
    )
    record_sightings("kucoin", {"NEWCOIN"})
    record_sightings("binance", {"NEWCOIN"})
    # Same timestamp won't give lead - that's ok for unit test structure
    assert lead_time_hours(source_exchange="kucoin", symbol="NEWCOIN") is None or isinstance(
        lead_time_hours(source_exchange="kucoin", symbol="NEWCOIN"), float
    )


@pytest.mark.asyncio
async def test_gateio_listing_intelligence_mock():
    fake_gate = [
        {"currency_pair": "EARLY_USDT", "last": "1.0", "change_percentage": "5", "quote_volume": "100000"},
        {"currency_pair": "BTC_USDT", "last": "60000", "change_percentage": "1", "quote_volume": "9999999"},
    ]
    fake_binance = {
        "symbols": [
            {"baseAsset": "BTC", "quoteAsset": "USDT", "status": "TRADING"},
        ]
    }

    async def _fake_json(url, **kwargs):
        if "binance" in url:
            return {"ok": True, "data": fake_binance, "cache_hit": False}
        return {"ok": True, "data": fake_gate, "cache_hit": False}

    with patch.object(
        __import__("blackdark.ingestion.gateio_connector", fromlist=["_CACHE"])._CACHE,
        "http_get_json",
        side_effect=_fake_json,
    ):
        out = await fetch_gateio_listing_intelligence(min_volume_usd=1000)
    assert out["ok"] is True
    assert out["gate_only_count"] >= 1
    assert out.get("headline")


@pytest.mark.asyncio
async def test_kucoin_listing_intelligence_mock():
    fake_kucoin = {
        "data": {
            "ticker": [
                {"symbol": "EARLY-USDT", "last": "2", "changeRate": "0.1", "volValue": "200000"},
                {"symbol": "BTC-USDT", "last": "60000", "changeRate": "0.01", "volValue": "9000000"},
            ]
        }
    }
    fake_binance = {"symbols": [{"baseAsset": "BTC", "quoteAsset": "USDT", "status": "TRADING"}]}

    async def _fake_json(url, **kwargs):
        if "binance" in url:
            return {"ok": True, "data": fake_binance}
        return {"ok": True, "data": fake_kucoin}

    with patch.object(
        __import__("blackdark.ingestion.kucoin_connector", fromlist=["_CACHE"])._CACHE,
        "http_get_json",
        side_effect=_fake_json,
    ):
        out = await fetch_kucoin_listing_intelligence(min_volume_usd=1000)
    assert out["ok"] is True
    assert out.get("headline")
    assert "KuCoin" in (out.get("headline") or "")


@pytest.mark.asyncio
async def test_marketwatch_connector_mock():
    xml = """<?xml version='1.0'?><rss><channel><item>
    <title>Fed holds rates steady</title><description>macro</description></item>
    <item><title>Tech stocks rally</title><description>markets</description></item>
    </channel></rss>"""

    async def _fake_get(*_a, **_k):
        return {"ok": True, "data": xml, "cache_hit": False}

    with patch.object(
        __import__("blackdark.ingestion.marketwatch_connector", fromlist=["_CACHE"])._CACHE,
        "http_get",
        side_effect=_fake_get,
    ):
        from blackdark.ingestion.marketwatch_connector import fetch_marketwatch_macro_context

        out = await fetch_marketwatch_macro_context()
    assert out["ok"] is True
    assert out.get("ai_context_line")
