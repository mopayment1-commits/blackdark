"""Tests — P1 UI Visibility: Decision Card, Risk Score, 12 routes, Unified Alerts."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from dashboard import app

client = TestClient(app)

P0_ROUTES = (
    ("/exchanges", "exchanges"),
    ("/stablecoins", "stablecoins"),
    ("/arbitrage", "arbitrage"),
    ("/brief", "brief"),
    ("/whales", "whales"),
)

P1_ROUTES = (
    ("/liquidity", "liquidity"),
    ("/defi", "defi"),
    ("/unlocks", "unlocks"),
    ("/correlation", "correlation"),
    ("/stress-test", "stress-test"),
    ("/thesis", "thesis"),
    ("/sopr", "sopr"),
    ("/dormancy", "dormancy"),
    ("/clusters", "clusters"),
    ("/dex-screener", "dex-screener"),
    ("/treasuries", "treasuries"),
    ("/metrics-library", "metrics"),
)


@pytest.mark.parametrize("path,cap_id", P0_ROUTES + P1_ROUTES)
def test_capability_route_html(path: str, cap_id: str):
    res = client.get(path)
    assert res.status_code == 200
    assert f'data-capability="{cap_id}"' in res.text
    assert "decision_card_global.js" in res.text
    assert "riskScoreStrip" in res.text


def test_thesis_asset_route():
    res = client.get("/thesis/ETH")
    assert res.status_code == 200
    assert 'data-thesis-asset="ETH"' in res.text


def test_wallet_profiler_route():
    res = client.get("/wallet/0x1234567890abcdef1234567890abcdef12345678")
    assert res.status_code == 200
    assert "walletRoot" in res.text
    assert "decision_card_global.js" in res.text


def test_simulator_redirect():
    res = client.get("/simulator", follow_redirects=False)
    assert res.status_code == 302
    assert "strategy-simulator" in res.headers.get("location", "")


def test_decision_card_api():
    res = client.post(
        "/api/platform/intelligence-ledger/ui/decision-card",
        json={
            "ux_mode": "beginner",
            "payload": {
                "verdict": "WAIT",
                "decision_sentence": "Test sentence",
                "confidence": 0.65,
            },
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    card = data["decision_card"]
    assert card["verdict"] == "WAIT"
    assert card["risk_warning_always_visible"] is True


def test_risk_score_surface_api():
    res = client.get("/api/platform/intelligence-ledger/portfolio-ai/risk-score")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert data.get("portfolio_risk_score") is not None or data.get("asset_risk_scores")
    assert len(data.get("asset_risk_scores") or []) >= 1


def test_risk_score_per_asset():
    res = client.get("/api/platform/intelligence-ledger/portfolio-ai/risk-score/BTC")
    assert res.status_code == 200
    data = res.json()
    assert data["asset"] == "BTC"
    assert data.get("risk_score") is not None


def test_unified_alert_feed():
    res = client.get("/api/alerts/unified-feed?limit=10")
    assert res.status_code == 200
    data = res.json()
    assert data["ok"] is True
    assert "alerts" in data
    assert "counts_by_type" in data
    assert set(data.get("available_types") or []) >= {
        "arbitrage", "risk", "whale", "events", "exchange", "stablecoin"
    }


def test_unified_alert_feed_filter():
    res = client.get("/api/alerts/unified-feed?alert_type=risk&limit=5")
    assert res.status_code == 200
    data = res.json()
    assert data.get("filter") == "risk"


def test_intelligence_hub_has_decision_card():
    res = client.get("/intelligence-ledger")
    assert res.status_code == 200
    assert "decisionCardSticky" in res.text
    assert "Intelligence Hub" in res.text
