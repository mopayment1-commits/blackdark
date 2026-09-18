"""Launch-57 Phase 7 Edge+UI Batch 1 — Net-Edge, MVRV blocker, product surfaces, kill-switch."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.edge_ui_batch1 import (
    LAUNCH57_EDGE_UI_BATCH1_CAP_IDS,
    capability_library_search,
    discipline_mirror_light,
    execute_launch57_edge_ui_batch1,
    mvrv_mvrv_z_score_suite,
    personal_decision_history,
    spot_perp_arbitrage_scanner,
)


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


def _stale_spine(symbol: str = "BTC"):
    return {
        "symbol": symbol,
        "freshness_state": FreshnessState.STALE.value,
        "live_eligible": False,
        "presented_as_live": False,
        "data_spine": {},
    }


@pytest.mark.asyncio
async def test_spot_perp_blocks_stale(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _stale_spine(symbol)

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    out = await spot_perp_arbitrage_scanner(symbol="BTC", params={})
    assert out["launch_item_id"] == 43
    assert out["success"] is False
    assert out["presented_as_live"] is False


@pytest.mark.asyncio
async def test_spot_perp_blocks_cost_claim_without_opportunity(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    out = await spot_perp_arbitrage_scanner(symbol="BTC", params={"cost_claim": True})
    assert out["launch_item_id"] == 43
    assert out["success"] is False
    assert out["cost_claim_blocked"] is True
    assert "net_edge" in out["net_edge_path"]


@pytest.mark.asyncio
async def test_spot_perp_scan_without_cost_claim(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_scan(**kwargs):
        return {
            "opportunities": [{"kind": "spot_futures", "net_profit_usdt": 1.0}],
            "counts": {"spot_futures": 1},
            "data_source": "test",
            "data_age_sec": 1.0,
            "executable_count": 1,
        }

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("arbitrage_service.scan_arbitrage_opportunities", fake_scan)
    out = await spot_perp_arbitrage_scanner(symbol="BTC", params={})
    assert out["spot_perp_arbitrage"]["opportunities"]
    assert out["spot_perp_arbitrage"]["opportunities"][0]["gross_spread_only"] is True
    assert out["spot_perp_arbitrage"]["opportunities"][0]["executable"] is False


@pytest.mark.asyncio
async def test_mvrv_source_blocker_visible(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_mvrv(symbol):
        return {"ok": True, "z_score": 1.2, "regime": "neutral"}

    async def fake_macro():
        return {"indicators": [{"id": "mvrv", "url": "https://example.com/mvrv"}]}

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("bd_platform.mvrv_realignment.compute_mvrv_realignment", fake_mvrv)
    monkeypatch.setattr("bd_platform.onchain_hub.lookintobitcoin_macro", fake_macro)
    out = await mvrv_mvrv_z_score_suite(symbol="BTC", params={})
    assert out["launch_item_id"] == 38
    status = out["mvrv_z_score_suite"]["source_status"]["BTC"]
    assert status["licensed_mvrv_feed"] is False
    assert status["local_proxy_compute"] is True
    assert status["blocker"] == "BLOCKED_EXTERNAL"
    assert status["presented_as_live"] is False
    assert out["mvrv_z_score_suite"]["licensed_source_configured"] is False


@pytest.mark.asyncio
async def test_personal_decision_history_free_limit(monkeypatch):
    monkeypatch.setattr(
        "launch57.edge_ui_common.read_decision_history_rows",
        lambda **kwargs: [{"decision_id": "d1"}],
    )
    out = await personal_decision_history(symbol="BTC", params={"tier": "free", "limit": 50})
    assert out["launch_item_id"] == 49
    assert out["personal_decision_history"]["limited_free"] is True
    assert out["personal_decision_history"]["free_limit"] == 10


@pytest.mark.asyncio
async def test_capability_library_secondary_layer(monkeypatch):
    monkeypatch.setattr(
        "launch57.edge_ui_common.launch57_library_entries",
        lambda **kwargs: [{"launch_number": 21, "secondary_layer": True}],
    )
    out = await capability_library_search(symbol="BTC", params={"query": "price"})
    assert out["launch_item_id"] == 52
    lib = out["capability_library"]
    assert lib["secondary_layer"] is True
    assert lib["not_primary_home"] is True
    assert lib["launch57_scope_only"] is True


@pytest.mark.asyncio
async def test_discipline_mirror_light(monkeypatch):
    monkeypatch.setattr(
        "discipline_mirror.personal_mirror",
        lambda user_key, limit=20: {"private": True, "total_answers": 0},
    )
    out = await discipline_mirror_light(symbol="BTC", params={"user_key": "u1"})
    assert out["launch_item_id"] == 50
    assert out["discipline_mirror"]["lightweight"] is True


@pytest.mark.asyncio
async def test_kill_switch_batch1(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_edge_ui_batch1")

    import launch57.edge_ui_batch1 as mod

    monkeypatch.setattr(mod, "spot_perp_arbitrage_scanner", broken)
    with pytest.raises(RuntimeError, match="kill_switch_edge_ui_batch1"):
        await execute_launch57_edge_ui_batch1(230, params={"symbol": "BTC"})


@pytest.mark.asyncio
async def test_dispatch_all_batch1_caps(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_scan(**kwargs):
        return {"opportunities": [], "counts": {}}

    async def fake_mvrv(symbol):
        return {"ok": True, "z_score": 0.5}

    async def fake_macro():
        return {"indicators": []}

    monkeypatch.setattr("launch57.edge_ui_common.load_decision_spine", fake_spine)
    monkeypatch.setattr("arbitrage_service.scan_arbitrage_opportunities", fake_scan)
    monkeypatch.setattr("bd_platform.mvrv_realignment.compute_mvrv_realignment", fake_mvrv)
    monkeypatch.setattr("bd_platform.onchain_hub.lookintobitcoin_macro", fake_macro)

    for cap_id in sorted(LAUNCH57_EDGE_UI_BATCH1_CAP_IDS):
        out = await execute_launch57_edge_ui_batch1(cap_id, params={"symbol": "BTC"})
        assert out["backend_module"] == "launch57.edge_ui_batch1"
