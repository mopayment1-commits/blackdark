"""Launch-57 Phase 7 Edge+UI Batch 2 — Six Heroes Command Home."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.edge_ui_batch2 import six_heroes_command_home
from launch57.edge_ui_common import LAUNCH57_SCOPE_IDS, launch57_home_eligible_ids


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
async def test_command_home_blocks_stale(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _stale_spine(symbol)

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    out = await six_heroes_command_home(symbol="BTC", params={})
    assert out["launch_item_id"] == 1
    assert out["success"] is False
    assert out["presented_as_live"] is False


@pytest.mark.asyncio
async def test_command_home_eligible_ids_within_launch57_scope(monkeypatch):
    async def fake_spine(symbol, params=None):
        return _live_spine(symbol)

    async def fake_oracle(**kwargs):
        return {
            "decision_action": "WAIT",
            "single_sentence_oracle": {"action": "WAIT", "sentence": "BTC: WAIT"},
            "evidence_class": "SHADOW_LIVE_FORWARD",
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)
    out = await six_heroes_command_home(symbol="BTC", params={})
    home = out["six_heroes_command_home"]
    eligible = home["eligible_launch57_ids"]
    assert all(i in LAUNCH57_SCOPE_IDS for i in eligible)
    assert home["excludes_parked"] is True
    assert home["launch57_scope_only"] is True
    assert home["no_duplicate_capability_directory"] is True
    assert out.get("evidence_class_visible") == "SHADOW_LIVE_FORWARD"
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "COMMAND_HOME_GROUNDED"
    assert "heroes" in home


def test_home_eligible_excludes_parked_statuses():
    eligible = launch57_home_eligible_ids()
    assert all(i in LAUNCH57_SCOPE_IDS for i in eligible)
    assert 58 not in eligible
    assert 0 not in eligible


@pytest.mark.asyncio
async def test_kill_switch_batch2(monkeypatch):
    async def broken(*a, **k):
        raise RuntimeError("kill_switch_edge_ui_batch2")

    import launch57.edge_ui_batch2 as mod

    monkeypatch.setattr(mod, "six_heroes_command_home", broken)
    with pytest.raises(RuntimeError, match="kill_switch_edge_ui_batch2"):
        await mod.execute_launch57_edge_ui_batch2(params={"symbol": "BTC"})
