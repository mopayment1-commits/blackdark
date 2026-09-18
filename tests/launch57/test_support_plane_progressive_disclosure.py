"""Launch-57 Support Plane — §28 L2–L5 on Command Home composite path."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from launch57.trust_adaptive_common import build_progressive_disclosure_stack


def test_progressive_disclosure_stack_has_levels_1_through_5():
    payload = {
        "freshness_state": "LIVE",
        "six_heroes_command_home": {
            "oracle": {"decision_action": "WAIT", "single_sentence_oracle": {"sentence": "BTC: WAIT"}},
            "router_selection_contract": {"explain": {"selection_summary": "data_spine+trust_surface"}},
            "heroes": [{"title": "Truth", "state": "grounded"}],
        },
    }
    stack = build_progressive_disclosure_stack(
        payload,
        launch_item_id=1,
        surface="six_heroes_command_home",
        answer_state="COMMAND_HOME_GROUNDED",
    )
    for layer in ("level_1", "level_2", "level_3", "level_4", "level_5"):
        assert layer in stack
        assert stack[layer]["layer"].startswith("level_")
        assert stack[layer]["safety_floor_visible"] is True


def test_command_home_api_includes_progressive_disclosure_layers(monkeypatch):
    from failure.freshness import FreshnessState
    from dashboard import app

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "price": 50000.0,
            "change_24h": 1.0,
            "data_spine": {},
        }

    async def fake_oracle(**kwargs):
        return {
            "decision_action": "WAIT",
            "single_sentence_oracle": {"action": "WAIT", "sentence": "BTC: WAIT"},
            "evidence_class": "SHADOW_LIVE_FORWARD",
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)

    client = TestClient(app)
    body = client.get("/api/launch57/command-home", params={"symbol": "BTC"}).json()
    disclosure = body.get("adaptive_disclosure") or {}
    for layer in ("level_1", "level_2", "level_3", "level_4", "level_5"):
        assert layer in disclosure, f"missing {layer} on command home"
