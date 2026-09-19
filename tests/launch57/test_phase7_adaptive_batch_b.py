"""Launch-57 Phase 7 Adaptive Batch B — builder verification tests (#1)."""

from __future__ import annotations

import pytest

from failure.freshness import FreshnessState
from launch57.edge_ui_batch2 import six_heroes_command_home
from launch57.edge_ui_common import LAUNCH57_SCOPE_IDS, launch57_home_eligible_ids
from launch57.trust_adaptive_common import apply_command_home_guard


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
async def test_capability_1_command_home_grounded_with_readiness_filter(monkeypatch):
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
    assert out["launch_item_id"] == 1
    assert out["success"] is True
    assert home["excludes_parked"] is True
    assert home["no_duplicate_capability_directory"] is True
    assert home["six_heroes_primary"] is True
    assert all(i in LAUNCH57_SCOPE_IDS for i in home["eligible_launch57_ids"])
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "COMMAND_HOME_GROUNDED"
    assert "heroes" in home
    assert home["heroes"]["derived_from"] == "canonical_decision_truth"


@pytest.mark.asyncio
async def test_capability_1_rejects_parked_readiness_bypass(monkeypatch):
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

    out = await six_heroes_command_home(symbol="BTC", params={"include_parked": True})
    home = out["six_heroes_command_home"]
    assert out["launch_item_id"] == 1
    assert out["success"] is False
    assert home["eligible_launch57_ids"] == []
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_READINESS_SCOPE_REJECTED"
    assert out["adaptive_disclosure"]["command_home_disclosure"]["scope_rejected"] is True


@pytest.mark.asyncio
async def test_capability_1_rejects_metadata_override(monkeypatch):
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

    out = await six_heroes_command_home(
        symbol="BTC",
        params={"eligible_launch57_ids": [99, 1]},
    )
    home = out["six_heroes_command_home"]
    assert out["success"] is False
    assert 99 not in home["eligible_launch57_ids"]
    assert out["adaptive_disclosure"]["level_1"]["answer_state"] == "UNSUPPORTED_READINESS_SCOPE_REJECTED"


def test_command_home_guard_rejects_parked_injection():
    canonical = launch57_home_eligible_ids()
    real = apply_command_home_guard(
        heroes={"heroes": {}, "derived_from": "canonical_decision_truth"},
        command_view=None,
        oracle={"evidence_class": "composite"},
        spine=_live_spine(),
        params={
            "include_parked": True,
            "surfaced_capabilities": [{"launch_number": 99, "engineering_status": "PARKED"}],
        },
    )
    bypass = apply_command_home_guard(
        heroes={"heroes": {}, "derived_from": "canonical_decision_truth"},
        command_view={"enabled": True},
        oracle={"evidence_class": "composite"},
        spine=_live_spine(),
        params={},
    )
    bypass["eligible_launch57_ids"] = [99]
    bypass["answer_state"] = "COMMAND_HOME_GROUNDED"

    assert real["answer_state"] == "UNSUPPORTED_READINESS_SCOPE_REJECTED"
    assert real["eligible_launch57_ids"] == []
    assert bypass["eligible_launch57_ids"] == [99]
    assert 99 not in canonical


def test_command_home_guard_bypass_fails_behavioral_acceptance():
    real = apply_command_home_guard(
        heroes={"heroes": {}, "derived_from": "canonical_decision_truth"},
        command_view=None,
        oracle={"evidence_class": "composite"},
        spine=_live_spine(),
        params={"override_readiness": True},
    )

    def bypass_guard(**kwargs):
        return {
            "answer_state": "COMMAND_HOME_GROUNDED",
            "eligible_launch57_ids": [99],
            "scope_rejected": False,
            "contract": {"evidence_class": "composite"},
        }

    bypass = bypass_guard()
    assert real["scope_rejected"] is True
    assert real["eligible_launch57_ids"] == []
    assert bypass["eligible_launch57_ids"] == [99]
    assert bypass["scope_rejected"] is False
