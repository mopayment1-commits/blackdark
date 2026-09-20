"""Launch-57 Batch B — visible trust consumer paths (#3–#6) from dashboard / proof page."""

from __future__ import annotations

import re
import uuid

import pytest
from fastapi.testclient import TestClient

ROOT = __import__("pathlib").Path(__file__).resolve().parents[2]
DASHBOARD = ROOT / "templates" / "dashboard.html"
ORACLE_ACCURACY = ROOT / "templates" / "oracle_accuracy.html"


def _dash() -> str:
    return DASHBOARD.read_text(encoding="utf-8")


def _visible_trust_block() -> str:
    dash = _dash()
    start = dash.index("const LAUNCH57_DECISION_CERTIFICATE")
    end = dash.index("function setTrustPulseLoading(active)")
    return dash[start:end]


@pytest.fixture
def authed_client():
    from dashboard import app

    client = TestClient(app, base_url="http://127.0.0.1")
    client.cookies.set("bd_token", f"trust-visible-batch-b-{uuid.uuid4().hex[:8]}")
    return client


def test_dashboard_wires_launch57_visible_trust_routes():
    dash = _dash()
    block = _visible_trust_block()
    assert "LAUNCH57_DECISION_CERTIFICATE = '/api/launch57/decision-certificate'" in block
    assert "LAUNCH57_PUBLIC_ACCURACY = '/api/launch57/public-accuracy'" in block
    assert "LAUNCH57_COST_AUTOPSY = '/api/launch57/cost-autopsy'" in block
    assert "function prefetchVisibleTrust(pulse, commandHome)" in block
    assert "function openDecisionCertificate()" in dash
    assert "data-bd-call=\"openDecisionCertificate\"" in dash
    assert "Evidence:" in dash


def test_net_edge_chip_hidden_without_autopsy():
    block = _visible_trust_block()
    chips = _dash().split("function buildPulseChips(p)", 1)[1].split("function renderPulseFlip", 1)[0]
    assert "lastVisibleTrust.netEdge" in chips
    assert "Net-Edge:" in chips
    assert re.search(r"netEdge\s*\|\|\s*['\"]—['\"]", chips) is None


def test_oracle_accuracy_loads_launch57_public_accuracy_sample():
    page = ORACLE_ACCURACY.read_text(encoding="utf-8")
    assert "/api/launch57/public-accuracy" in page
    assert "launch57-ledger-sample" in page
    assert "shadow_ledger_not_production" in page or "synthetic excluded" in page


def test_decision_certificate_route_launch_3(authed_client):
    res = authed_client.get(
        "/api/launch57/decision-certificate",
        params={
            "symbol": "BTC",
            "decision_action": "WAIT",
            "decision_sentence": "BTC: WAIT",
            "decision_time": "2026-09-17T12:00:00.000Z",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 3
    assert body.get("certificate_hash")


def test_broken_decision_certificate_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("decision_certificate_handler_removed")

    monkeypatch.setattr("launch57.trust_batch1.decision_certificate_export", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", f"trust-visible-batch-b-cert-broken-{uuid.uuid4().hex[:8]}")
    res = client.get(
        "/api/launch57/decision-certificate",
        params={
            "symbol": "BTC",
            "decision_action": "WAIT",
            "decision_sentence": "BTC: WAIT",
            "decision_time": "2026-09-17T12:00:00.000Z",
        },
    )
    assert res.status_code == 500


def test_public_accuracy_route_launch_4_live_sample():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/public-accuracy", params={"symbol": "BTC"})
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 4
    assert body.get("live_only_primary") is True
    assert body.get("synthetic_excluded_from_primary") is True


def test_broken_public_accuracy_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("public_accuracy_handler_removed")

    monkeypatch.setattr("launch57.trust_batch1.public_accuracy_ledger", broken)
    client = TestClient(app, raise_server_exceptions=False)
    res = client.get("/api/launch57/public-accuracy", params={"symbol": "BTC"})
    assert res.status_code == 500


def _csrf_headers() -> dict[str, str]:
    return {"Origin": "http://127.0.0.1"}


def test_cost_autopsy_route_launch_5_real_opportunity(authed_client):
    res = authed_client.post(
        "/api/launch57/cost-autopsy",
        headers=_csrf_headers(),
        json={
            "symbol": "BTC",
            "opportunity": {
                "net_profit_usdt": 5.0,
                "quote_amount": 1000.0,
                "total_slippage_bps": 2,
                "withdrawal_fee_usdt": 0.1,
                "trading_fees_usdt": 0.2,
                "quote_age_ms": 100,
                "estimated_recipients": 1,
            },
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 5
    assert body.get("success") is True
    assert body.get("cost_claim_allowed") is not False
    assert body.get("net_edge_truth_score", {}).get("truth_score") is not None


def test_cost_autopsy_without_opportunity_hides_claim(authed_client):
    res = authed_client.post(
        "/api/launch57/cost-autopsy",
        headers=_csrf_headers(),
        json={"symbol": "BTC"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("launch_item_id") == 5
    assert body.get("success") is False
    assert body.get("cost_claim_allowed") is False


def test_broken_cost_autopsy_handler_fails(monkeypatch):
    from dashboard import app

    async def broken(**kwargs):
        raise RuntimeError("net_edge_handler_removed")

    monkeypatch.setattr("launch57.trust_batch1.net_edge_truth_score", broken)
    client = TestClient(app, base_url="http://127.0.0.1", raise_server_exceptions=False)
    client.cookies.set("bd_token", "trust-visible-batch-b-broken-net-edge")
    res = client.post(
        "/api/launch57/cost-autopsy",
        headers=_csrf_headers(),
        json={
            "symbol": "BTC",
            "opportunity": {
                "net_profit_usdt": 5.0,
                "quote_amount": 1000.0,
                "total_slippage_bps": 2,
                "withdrawal_fee_usdt": 0.1,
                "trading_fees_usdt": 0.2,
                "quote_age_ms": 100,
                "estimated_recipients": 1,
            },
        },
    )
    assert res.status_code == 500


def test_evidence_class_visible_on_pulse_unchanged():
    block = _visible_trust_block()
    pulse_chips = _dash().split("function buildPulseChips(p)", 1)[1].split("function renderPulseFlip", 1)[0]
    assert "Evidence:" in pulse_chips
    assert "proof.evidence_class" in pulse_chips
    to_pulse = _dash().split("function commandHomeToPulse(data, standaloneOracle, evidenceClass)", 1)[1].split("function setShareProofButton", 1)[0]
    assert "mapCanonicalEvidenceLabel" in to_pulse
    assert "resolveLaunch57EvidenceLabel" in to_pulse
    assert "data-launch-item-id=\"6\"" in pulse_chips
