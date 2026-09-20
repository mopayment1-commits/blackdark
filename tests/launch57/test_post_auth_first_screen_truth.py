"""Launch-57 — first screen after session: truth-only display on /dashboard."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"
LOGIN = ROOT / "templates" / "login.html"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_post_auth_default_destination_is_dashboard():
    login = _read(LOGIN)
    assert "function resolvePostAuthUrl" in login
    assert "return '/dashboard';" in login


def test_dashboard_boot_calls_launch57_command_home():
    dash = _read(DASHBOARD)
    boot = dash.split("function boot()", 1)[1].split("if (document.readyState", 1)[0]
    assert "scheduleCommandHome()" in boot
    assert "startTrustPulseStream()" in boot
    assert "LAUNCH57_COMMAND_HOME = '/api/launch57/command-home'" in dash


def test_dashboard_truth_helpers_present():
    dash = _read(DASHBOARD)
    assert "function mapCanonicalEvidenceLabel" in dash
    assert "function freshnessUiLabel" in dash
    assert "presented_as_live" in dash
    assert "Evidence:" in dash
    assert re.search(r"knownFresh\s*\?\s*['\"]Live['\"]", dash) is None
    assert re.search(r"freshState\s*===\s*['\"]live['\"]", dash) is None


def test_command_home_to_pulse_blocks_stale_without_live_label():
    dash = _read(DASHBOARD)
    block = dash.split("function commandHomeToPulse(data)", 1)[1].split("function loadCommandHome", 1)[0]
    assert "freshnessState === 'STALE'" in block
    assert "freshnessState === 'UNKNOWN'" in block
    assert "presented_as_live: false" in block
    assert "Stale — not live" in block or "freshnessUiLabel(freshnessState, false" in block


def test_render_trust_pulse_fail_closed():
    dash = _read(DASHBOARD)
    render = dash.split("function renderTrustPulse(p", 1)[1].split("async function loadTrustPulse", 1)[0]
    assert "presented_as_live" in render
    assert "decision_live_blocked" in render
    assert "freshnessUiLabel" in render
    assert re.search(r"['\"]Live['\"]", render) is None


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app)
    client.cookies.set("bd_token", "post-auth-first-screen-truth")
    return client


def test_dashboard_page_200_with_session_cookie(authed_client, monkeypatch):
    from failure.freshness import FreshnessState

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

    reg = authed_client.post(
        "/api/auth/register",
        json={
            "email": f"post-auth-dash-{uuid.uuid4().hex[:10]}@example.com",
            "password": "SecurePass1234!",
            "accepted_terms": True,
            "accepted_privacy": True,
        },
        headers={"Origin": "https://testserver"},
    )
    assert reg.status_code == 200, reg.text
    res = authed_client.get("/dashboard", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "trust-pulse" in res.text
    assert "loadCommandHome" in res.text


def test_command_home_200_with_session_cookie(authed_client, monkeypatch):
    from failure.freshness import FreshnessState

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

    res = authed_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 1
    assert body.get("presented_as_live") is True
    assert body.get("freshness_state") == FreshnessState.LIVE.value
    assert body.get("evidence_class_visible") == "SHADOW_LIVE_FORWARD"


def test_stale_command_home_not_presented_as_live(authed_client, monkeypatch):
    from failure.freshness import FreshnessState

    async def fake_spine(symbol, params=None):
        return {
            "symbol": symbol,
            "freshness_state": FreshnessState.STALE.value,
            "live_eligible": False,
            "presented_as_live": False,
            "data_spine": {},
        }

    monkeypatch.setattr("launch57.edge_ui_batch2.load_decision_spine", fake_spine)

    res = authed_client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("success") is False
    assert body.get("presented_as_live") is False
    assert body.get("freshness_state") == FreshnessState.STALE.value


def test_dockerfile_includes_launch57_post_auth_runtime_packages():
    dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
    required = [
        "COPY launch57/ launch57/",
        "COPY decision_truth/ decision_truth/",
        "COPY failure/ failure/",
        "COPY data_governance/ data_governance/",
        "COPY governance/ governance/",
    ]
    for line in required:
        assert line in dockerfile, f"missing Dockerfile packaging: {line}"


def test_register_then_command_home_path_not_500(monkeypatch):
    from dashboard import app

    async def fake_spine(symbol, params=None):
        from failure.freshness import FreshnessState

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
    email = f"post-auth-truth-{uuid.uuid4().hex[:12]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePass1234!",
            "accepted_terms": True,
            "accepted_privacy": True,
        },
    )
    assert reg.status_code == 200, reg.text
    dash = client.get("/dashboard")
    assert dash.status_code == 200
    home = client.get("/api/launch57/command-home", params={"symbol": "BTC"})
    assert home.status_code == 200, home.text
