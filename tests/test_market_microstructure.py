"""Tests — #74 Market Microstructure Intelligence."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from bd_platform.market_microstructure import (
    LIQUID_ASSETS,
    effective_spread_bps,
    liquidity_health_score,
    order_book_imbalance,
    spoofing_detection_score,
    toxicity_regime,
    vpin_proxy,
    analyze_market_microstructure,
    microstructure_for_decision_engine,
)


def _sample_book() -> dict:
    bids = [[100.0, 10.0], [99.9, 50.0], [99.5, 200.0]]
    asks = [[100.1, 8.0], [100.2, 40.0], [100.6, 500.0]]
    return {"bids": bids, "asks": asks}


def test_order_book_imbalance():
    book = _sample_book()
    obi = order_book_imbalance(book["bids"], book["asks"])
    assert obi is not None
    assert -1 <= obi <= 1


def test_effective_spread():
    spread = effective_spread_bps(_sample_book()["bids"], _sample_book()["asks"])
    assert spread is not None
    assert spread > 0


def test_vpin_proxy_from_trades():
    trades = [{"p": "100", "q": "1", "m": False}] * 50 + [{"p": "100", "q": "1", "m": True}] * 50
    out = vpin_proxy(trades, buckets=5)
    assert out["vpin"] is not None
    assert 0 <= out["vpin"] <= 1


def test_spoofing_wall_detection():
    bids = [[100.0, 1.0], [99.0, 500.0]]
    asks = [[100.1, 1.0], [101.0, 1.0]]
    out = spoofing_detection_score(bids, asks)
    assert out["score"] > 0
    assert out["alerts"]


def test_toxicity_regime_manipulation():
    assert toxicity_regime(vpin=0.3, spoofing_score=75, obi=0.1, health=60) == "manipulation_detected"


def test_liquidity_health():
    health = liquidity_health_score(_sample_book()["bids"], _sample_book()["asks"], spread_bps=10)
    assert 0 <= health["score"] <= 100


@pytest.mark.asyncio
async def test_analyze_microstructure_mocked():
    book = _sample_book()
    trades = [{"p": "100", "q": "2", "m": False}] * 100

    async def fake_depth(sym, **kw):
        return book

    async def fake_trades(sym, **kw):
        return trades

    with patch("bd_platform.market_microstructure._fetch_depth", side_effect=fake_depth), patch(
        "bd_platform.market_microstructure._fetch_agg_trades",
        side_effect=fake_trades,
    ), patch("bd_platform.market_microstructure.asyncio.sleep", new=AsyncMock()):
        out = await analyze_market_microstructure("ETH", amount_usd=10_000)

    assert out["ok"] is True
    assert out["feature"] == "#74"
    assert out["liquidity_health_score"] >= 0
    assert out["toxicity_regime"] in {"normal", "caution", "high_toxicity", "manipulation_detected"}
    assert len(out["market_impact_curve"]) == 4
    assert len(LIQUID_ASSETS) >= 50


@pytest.mark.asyncio
async def test_decision_engine_payload():
    with patch(
        "bd_platform.market_microstructure.analyze_market_microstructure",
        new=AsyncMock(
            return_value={
                "ok": True,
                "asset": "ETH",
                "toxicity_regime": "high_toxicity",
                "liquidity_health_score": 45,
                "spoofing": {"score": 10},
                "headline": "test",
                "latency_ms": 100,
            }
        ),
    ):
        out = await microstructure_for_decision_engine("ETH")
    assert out["ok"] is True
    assert out["risk_score_delta"] > 0
