"""Tests — Market Intelligence features #2–#4."""

from __future__ import annotations

import asyncio

import pytest

from bd_platform.alpha_factor_ranking import _composite, _momentum_score, _rank_coin
from bd_platform.mvrv_realignment import _realignment_signal, _regime_from_z
from bd_platform.squeeze_trigger_engine import _squeeze_coordinates


def test_regime_from_z():
    assert _regime_from_z(0) == "neutral"
    assert _regime_from_z(-1.5) == "undervalued"
    assert _regime_from_z(2.5) == "extreme_overheated"


def test_bullish_realignment_signal():
    assert _realignment_signal(-1.2, -0.8) == "bullish_realignment"
    assert _realignment_signal(1.2, 0.8) == "bearish_realignment"


def test_momentum_score_bounds():
    assert _momentum_score(0) == 50
    assert _momentum_score(10) == 90


def test_alpha_composite():
    factors = {"momentum": 80, "liquidity": 60, "trend": 70, "volatility_penalty": 50}
    assert 60 <= _composite(factors) <= 80


def test_rank_coin_structure():
    row = _rank_coin(
        {
            "symbol": "ETH",
            "name": "Ethereum",
            "rank": 2,
            "price_usd": 3000,
            "change_24h_pct": 5.0,
            "volume_24h_usd": 10e9,
            "market_cap_usd": 300e9,
            "sparkline_7d": [100, 102, 105, 108],
        },
        btc_change=2.0,
    )
    assert row["symbol"] == "ETH"
    assert 0 <= row["alpha_score"] <= 100
    assert "factors" in row


def test_squeeze_coordinates_structure():
    coords = _squeeze_coordinates(
        mark=100_000,
        funding_rate=0.0004,
        ls_ratio=1.9,
        change_24h=-1.0,
        oi_usd=2e9,
    )
    assert len(coords) >= 8
    types = {c["squeeze_type"] for c in coords}
    assert "long_liquidation_cascade" in types
    assert "short_squeeze_trigger" in types


@pytest.mark.asyncio
async def test_mvrv_realignment_live_mock(monkeypatch):
    async def fake_klines(asset, *, interval="1d", limit=365):
        import math

        return [30000 + math.sin(i / 10) * 2000 + i * 5 for i in range(365)]

    monkeypatch.setattr("bd_platform.mvrv_realignment._fetch_closes", fake_klines)
    from bd_platform.mvrv_realignment import compute_mvrv_realignment

    out = await compute_mvrv_realignment("BTC")
    assert out["ok"] is True
    assert out["data_state"] == "LIVE"
    assert "z_score" in out
    assert out["sla_met"] is True


@pytest.mark.asyncio
async def test_alpha_ranking_mock(monkeypatch):
    async def fake_market(**kwargs):
        return {
            "style": "test",
            "coins": [
                {
                    "rank": 1,
                    "symbol": "BTC",
                    "name": "Bitcoin",
                    "price_usd": 100000,
                    "change_24h_pct": 2,
                    "volume_24h_usd": 30e9,
                    "market_cap_usd": 2e12,
                    "sparkline_7d": [90, 92, 95, 98, 100],
                },
                {
                    "rank": 2,
                    "symbol": "ETH",
                    "name": "Ethereum",
                    "price_usd": 3000,
                    "change_24h_pct": 5,
                    "volume_24h_usd": 15e9,
                    "market_cap_usd": 360e9,
                    "sparkline_7d": [80, 85, 90, 95, 100],
                },
            ],
        }

    monkeypatch.setattr("bd_platform.alpha_factor_ranking.market_rankings", fake_market)
    from bd_platform.alpha_factor_ranking import rank_assets_by_alpha_factors

    out = await rank_assets_by_alpha_factors(limit=10)
    assert out["ok"] is True
    assert len(out["rankings"]) == 2
    assert out["rankings"][0]["alpha_rank"] == 1


@pytest.mark.asyncio
async def test_squeeze_triggers_mock(monkeypatch):
    async def fake_snap(asset="BTC"):
        return {
            "available": True,
            "mark_price": 100000,
            "funding_rate": 0.0005,
            "funding_rate_pct": 0.05,
            "open_interest_usd": 15e9,
            "change_24h_pct": 3,
            "long_short_ratio": 1.7,
        }

    async def fake_risk(asset="BTC"):
        return {"alerts": [{"type": "long_crowding", "detail": "test"}]}

    monkeypatch.setattr("bd_platform.squeeze_trigger_engine.binance_futures_snapshot", fake_snap)
    monkeypatch.setattr("bd_platform.squeeze_trigger_engine.binance_liquidation_risk", fake_risk)
    from bd_platform.squeeze_trigger_engine import squeeze_trigger_coordinates

    out = await squeeze_trigger_coordinates("BTC")
    assert out["ok"] is True
    assert len(out["coordinates"]) > 0
    assert out["sla_met"] is True


def _init_test_db(tmp_path, monkeypatch):
    import config
    import database

    db_path = tmp_path / "mi.db"
    monkeypatch.setattr(config, "DB_PATH", db_path)
    monkeypatch.setattr(database.config, "DB_PATH", db_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("ENV", "test")
    asyncio.run(database.init_db())


def test_market_intelligence_api(tmp_path, monkeypatch):
    _init_test_db(tmp_path, monkeypatch)

    async def fake_mvrv(asset="BTC"):
        return {"ok": True, "z_score": 0.5, "regime": "neutral", "data_state": "LIVE", "latency_ms": 100}

    async def fake_alpha(limit=25):
        return {"ok": True, "rankings": [], "count": 0, "data_state": "LIVE", "latency_ms": 100}

    async def fake_sq(symbol="BTC"):
        return {"ok": True, "coordinates": [], "headline": "test", "data_state": "LIVE", "latency_ms": 100}

    monkeypatch.setattr("bd_platform.mvrv_realignment.compute_mvrv_realignment", fake_mvrv)
    monkeypatch.setattr("bd_platform.alpha_factor_ranking.rank_assets_by_alpha_factors", fake_alpha)
    monkeypatch.setattr("bd_platform.squeeze_trigger_engine.squeeze_trigger_coordinates", fake_sq)

    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    assert c.get("/api/platform/onchain/mvrv-realignment").status_code == 200
    assert c.get("/api/platform/alpha/factor-ranking").status_code == 200
    assert c.get("/api/platform/squeeze/triggers").status_code == 200
    r = c.get("/market-intelligence")
    assert r.status_code == 200
    assert "Market Intelligence" in r.text
