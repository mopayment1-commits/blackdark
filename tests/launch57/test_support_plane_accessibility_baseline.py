"""Launch-57 Support Plane — §31 accessibility engineering baseline."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from launch57.accessibility_common import WCAG_TARGET, build_launch57_accessibility_envelope

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"


def test_launch57_accessibility_envelope_wcag_target():
    env = build_launch57_accessibility_envelope(
        {"six_heroes_command_home": {}, "decision_truth_state": "AVAILABLE"},
        surface="six_heroes_command_home",
    )
    assert env["standard"] == WCAG_TARGET
    assert env["engineering_baseline_only"] is True
    assert env["controls"]["non_color_only_status"] is True


def test_command_home_api_includes_launch57_accessibility(monkeypatch):
    from failure.freshness import FreshnessState
    from dashboard import app

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.LIVE.value,
            "live_eligible": True,
            "presented_as_live": True,
            "price": 1.0,
            "change_24h": 0.0,
            "data_spine": {},
        }

    async def fake_oracle(**kwargs):
        return {
            "decision_action": "WAIT",
            "single_sentence_oracle": {"action": "WAIT", "sentence": "WAIT"},
            "evidence_class": "SHADOW_LIVE_FORWARD",
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)
    monkeypatch.setattr("launch57.edge_ui_batch2.single_sentence_oracle", fake_oracle)

    client = TestClient(app)
    body = client.get("/api/launch57/command-home", params={"symbol": "BTC"}).json()
    a11y = body.get("launch57_accessibility") or {}
    assert a11y.get("standard") == WCAG_TARGET
    assert a11y.get("surface") == "six_heroes_command_home"


def test_dashboard_trust_pulse_has_accessible_heading():
    dash = DASHBOARD.read_text(encoding="utf-8")
    assert 'id="trust-pulse"' in dash or "trust-pulse" in dash
    assert re.search(r"<h[12][^>]*>", dash) is not None
