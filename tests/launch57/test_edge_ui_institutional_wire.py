"""Launch-57 Phase 7 — institutional intercept for edge+UI caps."""

from __future__ import annotations

import pytest

from cap646.institutional_official_production import execute
from failure.freshness import FreshnessState


def _live_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.LIVE.value,
        "live_eligible": True,
        "presented_as_live": True,
        "price": 50000.0,
        "change_24h": 1.0,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_institutional_intercepts_cap230(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_scan(**kwargs):
        return {"opportunities": [{"kind": "funding"}], "counts": {}}

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("arbitrage_service.scan_arbitrage_opportunities", fake_scan)
    out = await execute(230, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.edge_ui_batch1"
    assert out["launch_item_id"] == 43


@pytest.mark.asyncio
async def test_institutional_intercepts_cap40_mvrv(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_mvrv(symbol):
        return {"ok": True, "z_score": 0.1}

    async def fake_macro():
        return {"indicators": []}

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.mvrv_realignment.compute_mvrv_realignment", fake_mvrv)
    monkeypatch.setattr("bd_platform.onchain_hub.lookintobitcoin_macro", fake_macro)
    out = await execute(40, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.edge_ui_batch1"
    assert out["launch_item_id"] == 38


@pytest.mark.asyncio
async def test_institutional_intercepts_cap635(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_scan(**kwargs):
        return {"opportunities": [], "counts": {}}

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("arbitrage_service.scan_arbitrage_opportunities", fake_scan)
    out = await execute(635, params={"symbol": "BTC"})
    assert out["handler_module"] == "launch57.edge_ui_batch1"
    assert out["launch_item_id"] == 43
