"""Launch-57 Phase 3 — institutional intercept for decision caps."""

from __future__ import annotations

import pytest

from cap646.institutional_official_production import execute
from failure.freshness import FreshnessState


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "prices": {"price": 50000.0, "change_24h": 1.0, "freshness_state": FreshnessState.LIVE.value, "presented_as_live": True},
        "freshness": {"freshness_state": FreshnessState.LIVE.value},
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.0,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_institutional_intercepts_cap35(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_ctx():
        return {}

    monkeypatch.setattr("launch57.decision_batch1.load_decision_spine", fake_spine)
    monkeypatch.setattr("onchain_tracker.build_onchain_context_safe", fake_ctx)
    out = await execute(35, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.decision_batch1"
    assert out.get("market_compass") or out.get("success") is False


@pytest.mark.asyncio
async def test_institutional_intercepts_cap29(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.decision_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr(
        "bd_platform.pro_trader_layer.build_multi_dim_analysis_73",
        lambda asset: {"ok": True, "composite_score": 60},
    )
    monkeypatch.setattr(
        "bd_platform.institutional_delivery_intelligence_layer.cross_market_decision_intelligence_567",
        lambda symbol: {},
    )
    out = await execute(29, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.decision_batch2"
