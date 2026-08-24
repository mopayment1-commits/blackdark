"""Tests — Arbitrage Scanner (#112), Net Profit (#113), New Listings (#114)."""

from __future__ import annotations

import pytest

from bd_platform.net_profit_engine import _headline, attach_net_profit


def test_net_profit_headline_complete():
    h = _headline(50.0, 12.5, [])
    assert "Gross gap" in h
    assert "Net $12.50" in h


def test_net_profit_headline_missing():
    h = _headline(50.0, None, ["gas"])
    assert "incomplete" in h
    assert "gas" in h


def test_attach_net_profit_layer():
    breakdown = {
        "ok": True,
        "waterfall": {"gross_gap_usd": 10.0, "net_profit_usd": 3.5},
    }
    out = attach_net_profit({"asset": "BTC"}, breakdown)
    assert out["net_profit_complete"] is True
    assert out["net_profit_usd"] == 3.5
    assert out["profitable"] is True


@pytest.mark.asyncio
async def test_net_profit_breakdown(monkeypatch):
    async def fake_gas(chain, quote_usd, *, hops=1):
        return 15.0

    monkeypatch.setattr("gas_oracle.gas_cost_bps", fake_gas)

    from bd_platform.net_profit_engine import compute_net_profit_breakdown

    out = await compute_net_profit_breakdown(
        gross_gap_usd=25.0,
        notional_usd=1000.0,
        buy_exchange="binance",
        sell_exchange="okx",
        symbol="BTC/USDT",
        slippage_bps=10.0,
        include_withdrawal=False,
    )
    assert out["ok"] is True
    wf = out["waterfall"]
    assert wf["gross_gap_usd"] == 25.0
    assert wf["net_profit_usd"] is not None
    assert wf["net_profit_usd"] < wf["gross_gap_usd"]
    assert out["sla_met"] is True


@pytest.mark.asyncio
async def test_arbitrage_scanner_mock(monkeypatch):
    async def fake_scan(*, quote_usd=1000):
        return {
            "opportunities": [
                {
                    "asset": "ETH",
                    "buy_venue": "binance",
                    "sell_venue": "uniswap",
                    "buy_price": 3000.0,
                    "sell_price": 3010.0,
                    "spread_bps": 33.0,
                    "dex_liquidity_usd": 5_000_000,
                }
            ]
        }

    async def fake_breakdown(**kwargs):
        return {
            "ok": True,
            "waterfall": {
                "gross_gap_usd": 3.33,
                "net_profit_usd": 1.0,
                "trading_fees_usd": 1.0,
                "slippage_usd": 0.5,
                "gas_usd": 0.83,
            },
            "headline": "Gross gap $3.33 → Net $1.00 after gas, slippage, and fees",
        }

    monkeypatch.setattr("bd_platform.cex_dex_arbitrage.scan_cex_dex_opportunities", fake_scan)
    monkeypatch.setattr("bd_platform.net_profit_engine.compute_net_profit_breakdown", fake_breakdown)

    from bd_platform.arbitrage_scanner import scan_arbitrage

    out = await scan_arbitrage(quote_usd=1000)
    assert out["ok"] is True
    assert out["feature_id"] == 112
    assert out["product_name"] == "Arbitrage Scanner"
    assert out["requires_net_profit"] is True
    assert out["opportunities"][0]["net_profit_complete"] is True
    assert "disclaimer" in out


@pytest.mark.asyncio
async def test_new_listings_dex_event(monkeypatch, tmp_path):
    monkeypatch.setattr("bd_platform.new_listings_alert._CACHE_PATH", tmp_path / "cache.json")
    monkeypatch.setattr("bd_platform.new_listings_alert._ALERTS_PATH", tmp_path / "alerts.jsonl")
    monkeypatch.setattr("bd_platform.new_listings_alert._REGISTRY_PATH", tmp_path / "reg.jsonl")
    monkeypatch.setattr("bd_platform.new_listings_alert._KNOWN_SYMBOLS_PATH", tmp_path / "known.json")

    import time as time_mod

    recent_ms = int(time_mod.time() * 1000)

    async def fake_binance(session):
        return []

    async def fake_dex(session, *, limit=15):
        return [
            {
                "event_type": "new_listing",
                "exchange": "pancakeswap",
                "symbol": "TEST",
                "liquidity_usd": 2_000_000,
                "contract_verified": True,
                "headline": "New pair on pancakeswap — TEST — initial liquidity $2,000,000 — Contract Verified",
                "source": "dexscreener",
                "mode": "event_only",
                "timestamp": "2026-08-24T00:00:00+00:00",
            }
        ]

    monkeypatch.setattr("bd_platform.new_listings_alert._detect_binance_new_listings", fake_binance)
    monkeypatch.setattr("bd_platform.new_listings_alert._fetch_dexscreener_recent", fake_dex)

    from bd_platform.new_listings_alert import scan_new_listings

    out = await scan_new_listings(limit=5)
    assert out["ok"] is True
    assert out["feature_id"] == 114
    assert out["mode"] == "event_only"
    assert out["alert_count"] >= 1
    assert "buy" not in out["disclaimer"].lower() or "not buy" in out["disclaimer"].lower()
    assert out["sla_met"] is True
    _ = recent_ms  # silence unused


@pytest.mark.asyncio
async def test_fee_database_status():
    from bd_platform.net_profit_engine import fee_database_status

    out = await fee_database_status()
    assert out["ok"] is True
    assert out["feature_id"] == 130
    assert out["exchanges_tracked"] >= 1
