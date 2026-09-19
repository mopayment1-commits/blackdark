"""Launch-57 Support Plane Phase 1 — default journey isolation."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"
LANDING = ROOT / "templates" / "landing.html"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_dashboard_boot_uses_launch57_command_home():
    dash = _read(DASHBOARD)
    assert "LAUNCH57_COMMAND_HOME = '/api/launch57/command-home'" in dash
    assert "loadCommandHome" in dash
    boot = dash.split("function boot()", 1)[1].split("function ", 1)[0]
    assert "loadCommandHome(true)" in boot
    assert "fetch('/api/intent/router')" not in dash
    assert re.search(r"fetch\(['\"]\/api\/trust-pulse", dash) is None
    assert re.search(r"fetch\(['\"]\/oracle\/", dash) is None
    assert re.search(r"fetch\(['\"]\/api\/oracle\/", dash) is None
    assert "commandHomeToHalfLifeHeat" in dash
    assert "loadCommandHome" in dash.split("function loadHalfLifeClock", 1)[1]


def test_dashboard_legacy_loaders_delegate_to_command_home():
    dash = _read(DASHBOARD)
    assert "async function loadTrustPulse(force)" in dash
    assert "return loadCommandHome(force)" in dash
    assert "async function askOracle()" in dash
    assert "loadCommandHome(true)" in dash


def test_landing_default_journey_uses_launch57():
    land = _read(LANDING)
    assert "/api/launch57/guest-trust" in land
    assert "fetchLaunch57GuestTrust" in land
    assert re.search(r"fetch\(['\"]\/api\/trust-pulse", land) is None
    assert "EventSource('/api/trust-pulse/stream" not in land
    assert re.search(r"fetch\([^)]*\/oracle\/", land) is None


def test_launch57_api_mounts_still_present():
    dash_py = _read(ROOT / "dashboard.py")
    assert "launch57_edge_ui_router" in dash_py
    assert "/api/launch57/command-home" in dash_py or "launch57_edge_ui" in dash_py


def test_command_home_api_reachable(monkeypatch):
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
    client.cookies.set("bd_token", "support-plane-phase1-test")
    res = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 1
    home = body.get("six_heroes_command_home") or {}
    assert home.get("launch57_scope_only") is True
    assert home.get("excludes_parked") is True


def test_command_home_eligible_ids_within_launch57():
    from dashboard import app

    client = TestClient(app)
    client.cookies.set("bd_token", "support-plane-phase1-test")
    body = client.get("/api/launch57/command-home", params={"symbol": "BTC"}).json()
    home = body.get("six_heroes_command_home") or {}
    eligible = home.get("eligible_launch57_ids") or []
    assert all(1 <= i <= 57 for i in eligible)
