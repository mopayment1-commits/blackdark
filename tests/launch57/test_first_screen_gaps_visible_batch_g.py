"""Launch-57 Batch G — visible first-screen gap consumer paths (#21, #36, #45, #49, #51)."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"
ORACLE_ACCURACY = ROOT / "templates" / "oracle_accuracy.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _first_screen_block() -> str:
    dash = _dash()
    start = dash.index("const LAUNCH57_SPOT_METRICS")
    end = dash.index("let lastVisibleTrust")
    return dash[start:end]


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app, base_url="http://127.0.0.1")
    client.cookies.set("bd_token", f"first-screen-gaps-batch-g-{uuid.uuid4().hex[:8]}")
    return client


def test_dashboard_wires_launch57_first_screen_gap_routes():
    block = _first_screen_block()
    assert "LAUNCH57_SPOT_METRICS = '/api/launch57/spot-metrics'" in block
    assert "LAUNCH57_SHAREABLE_ACCURACY = '/api/launch57/shareable-accuracy'" in block
    assert "LAUNCH57_DECISION_HISTORY = '/api/launch57/decision-history'" in block
    assert "LAUNCH57_AI_COPILOT = '/api/launch57/ai-copilot'" in block
    assert "LAUNCH57_RESEARCH_PORTAL = '/api/launch57/research-portal'" in block
    assert "function loadLaunch57FirstScreenGaps" in _dash()
    assert 'id="launch57-first-screen-gaps"' in _dash()


def test_send_chat_uses_launch57_ai_copilot_not_legacy_chat_api():
    chat = _dash().split("async function sendChat()", 1)[1].split("let nextUpgrade", 1)[0]
    assert "LAUNCH57_AI_COPILOT" in chat
    assert "/api/chat" not in chat
    assert "platform_data_only" in _dash().split("function renderLaunch57FirstScreenGaps", 1)[1].split("async function prefetchShareProof", 1)[0]


def test_load_daily_report_uses_launch57_research_portal_not_legacy_reports_api():
    report = _dash().split("async function loadDailyReport()", 1)[1].split("async function loadSubscriberValue", 1)[0]
    assert "LAUNCH57_RESEARCH_PORTAL" in report
    assert "/api/reports/daily" not in report


def test_prefetch_visible_trust_fetches_shareable_accuracy_for_pulse():
    trust = _dash().split("async function prefetchVisibleTrust", 1)[1].split("function renderAbstainReasonsBlock", 1)[0]
    assert "LAUNCH57_SHAREABLE_ACCURACY" in trust
    assert "launch_item_id) === 45" in trust


def test_oracle_accuracy_page_wires_shareable_accuracy_route():
    html = ORACLE_ACCURACY.read_text(encoding="utf-8")
    assert 'id="launch57-shareable-accuracy"' in html
    assert "/api/launch57/shareable-accuracy" in html


def test_spot_metrics_route_launch_21():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/spot-metrics", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 21


def test_broken_spot_metrics_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("spot_metrics_handler_removed")

    monkeypatch.setattr("launch57.data_batch1.spot_market_metrics_suite", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/spot-metrics", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_shareable_accuracy_route_launch_45():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/shareable-accuracy", params={"symbol": "BTC"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 45


def test_broken_shareable_accuracy_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("shareable_accuracy_handler_removed")

    monkeypatch.setattr("launch57.trust_batch2.shareable_accuracy_page", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/shareable-accuracy", params={"symbol": "BTC"})
    assert res.status_code == 500


def test_decision_history_route_launch_49(authed_client, monkeypatch):
    monkeypatch.setattr(
        "launch57.tier_distribution.enforce_launch57_tier_access",
        lambda **kwargs: {"allowed": True, "effective_tier": "pro", "minimum_tier": "pro"},
    )
    res = authed_client.get("/api/launch57/decision-history", params={"symbol": "BTC", "tier": "pro", "limit": 5})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 49


def test_broken_decision_history_handler_fails(monkeypatch):
    from dashboard import app

    monkeypatch.setattr(
        "launch57.tier_distribution.enforce_launch57_tier_access",
        lambda **kwargs: {"allowed": True, "effective_tier": "pro", "minimum_tier": "pro"},
    )

    async def broken(**kwargs):
        raise RuntimeError("decision_history_handler_removed")

    monkeypatch.setattr("launch57.edge_ui_batch1.personal_decision_history", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"first-screen-gaps-broken-49-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/decision-history", params={"symbol": "BTC", "tier": "pro"})
    assert res.status_code == 500


def test_ai_copilot_route_launch_36(authed_client, monkeypatch):
    monkeypatch.setattr(
        "launch57.tier_distribution.enforce_launch57_tier_access",
        lambda **kwargs: {"allowed": True, "effective_tier": "elite", "minimum_tier": "elite"},
    )
    res = authed_client.get("/api/launch57/ai-copilot", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 36


def test_broken_ai_copilot_handler_fails(monkeypatch):
    from dashboard import app

    monkeypatch.setattr(
        "launch57.tier_distribution.enforce_launch57_tier_access",
        lambda **kwargs: {"allowed": True, "effective_tier": "elite", "minimum_tier": "elite"},
    )

    async def broken(**kwargs):
        raise RuntimeError("ai_copilot_handler_removed")

    monkeypatch.setattr("launch57.explanation_ai_batch1.ai_research_agent_grounded", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"first-screen-gaps-broken-36-{uuid.uuid4().hex[:8]}")
    res = client.get("/api/launch57/ai-copilot", params={"symbol": "BTC", "tier": "elite"})
    assert res.status_code == 500


def test_research_portal_route_launch_51():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/research-portal", params={"symbol": "BTC", "tier": "free"})
    assert res.status_code == 200
    assert res.json().get("launch_item_id") == 51


def test_broken_research_portal_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("research_portal_handler_removed")

    monkeypatch.setattr("launch57.explanation_ai_batch1.research_intelligence_portal", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/research-portal", params={"symbol": "BTC"})
    assert res.status_code == 500
