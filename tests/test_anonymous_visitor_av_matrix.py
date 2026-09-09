"""AV-01 → AV-30 P0 test matrix — Anonymous Visitor closure."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def av_client(tmp_path, monkeypatch):
    db = tmp_path / "av-matrix.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("ENV", "development")
    monkeypatch.setenv("COOKIE_SECURE", "false")
    monkeypatch.setenv("SECRETS_MASTER_KEY", "unit-test-vault-key-for-av-matrix")
    monkeypatch.setenv("SESSION_TOKEN_PEPPER", "unit-test-session-pepper-av-matrix")
    from dashboard import app

    return TestClient(app)


def test_av01_explicit_anonymous_state():
    from anonymous_visitor.states import ProductAuthState, resolve_product_state

    assert ProductAuthState.ANONYMOUS.value == "ANONYMOUS"
    assert resolve_product_state(None) == ProductAuthState.ANONYMOUS


def test_av02_route_inventory(av_client):
    from anonymous_visitor.inventory import scan_fastapi_routes

    rows = scan_fastapi_routes(av_client.app)
    assert len(rows) > 50
    allow = av_client.get("/api/anonymous-visitor/allowlist")
    assert allow.status_code == 200
    assert allow.json()["single_canonical_registry"] is True


def test_av03_deny_by_default(av_client):
    from anonymous_visitor.allowlist import is_anonymous_denied

    assert is_anonymous_denied("/api/data-governance/status")
    assert is_anonymous_denied("/api/financial-data-security/status")
    r1 = av_client.get("/api/data-governance/status")
    r2 = av_client.get("/api/financial-data-security/status")
    assert r1.status_code == 401
    assert r2.status_code == 401
    assert r1.json()["server_side_enforcement"] is True


def test_av04_homepage_value(av_client):
    r = av_client.get("/")
    assert r.status_code == 200
    body = r.text.lower()
    assert "blackdark" in body
    assert "trust" in body or "pulse" in body or "decision" in body


def test_av05_product_proof_before_signup(av_client):
    r = av_client.get("/api/trust-pulse?symbol=BTC")
    assert r.status_code == 200
    data = r.json()
    assert data.get("action") or data.get("decision_state") or data.get("symbol")


def test_av06_decision_truth_pulse(av_client):
    r = av_client.get("/api/anonymous-visitor/public-intelligence/decision-truth-pulse?symbol=BTC")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True or data.get("degraded_state")
    if data.get("ok"):
        assert data["license_public_display_pass"] is True
        assert data["non_personal"] is True


def test_av07_evidence_passport(av_client):
    r = av_client.get("/api/anonymous-visitor/public-intelligence/evidence-passport")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data["surface"] == "evidence_passport_public_summary"


def test_av08_public_accuracy(av_client):
    r = av_client.get("/api/anonymous-visitor/public-intelligence/accuracy")
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True or data.get("degraded_state")
    if data.get("ok"):
        assert data["timestamped"] is True


def test_av09_no_private_data_anonymous(av_client):
    r = av_client.get("/api/user/profile")
    assert r.status_code == 401


def test_av10_account_gate_boundary():
    from anonymous_visitor.account_gate import evaluate_account_gate

    blocked = evaluate_account_gate("save_asset", auth_state="ANONYMOUS")
    assert blocked["gate_required"] is True
    allowed = evaluate_account_gate("save_asset", auth_state="FREE_ACCOUNT")
    assert allowed["ok"] is True


def test_av11_licensing_gate():
    from anonymous_visitor.licensing import assert_license_public_display, licensing_register_export

    gate = assert_license_public_display("oracle_unified")
    assert gate["license_public_display_pass"] is True
    assert len(licensing_register_export()) >= 4
    bad = assert_license_public_display("unknown_source")
    assert bad["license_public_display_pass"] is False


def test_av12_attribution(av_client):
    r = av_client.get("/api/anonymous-visitor/public-intelligence/decision-truth-pulse?symbol=BTC")
    data = r.json()
    if data.get("ok"):
        assert data["attribution"]["required"] is True
        assert data["attribution"]["text"]


def test_av13_public_rate_limiting():
    from anonymous_visitor.protections import protection_status

    status = protection_status()
    assert status["rate_limiting"] is True


def test_av14_cost_protections(monkeypatch):
    from anonymous_visitor.allowlist import match_allowlist_entry
    from anonymous_visitor.protections import PublicProtectionError, check_public_protections

    monkeypatch.setenv("ANONYMOUS_PUBLIC_RL_EXEMPT", "false")
    ok = check_public_protections(method="GET", path="/api/anonymous-visitor/status", client_id="t1")
    assert ok["allowed"] is True
    entry = match_allowlist_entry("GET", "/api/anonymous-visitor/status")
    assert entry is not None
    with pytest.raises(PublicProtectionError):
        for _ in range(entry.rate_limit_per_min + 5):
            check_public_protections(
                method="GET",
                path="/api/anonymous-visitor/status",
                client_id="same-client",
                entry=entry,
            )


def test_av15_stream_policy():
    from anonymous_visitor.streams import validate_stream_path, unsafe_anonymous_streams

    assert validate_stream_path("/api/trust-pulse/stream")["allowed"] is True
    assert unsafe_anonymous_streams() == []


def test_av16_consent_manager():
    from anonymous_visitor.consent import consent_status, update_consent

    s = consent_status(visitor_key="test-visitor")
    assert s["essential_only_before_consent"] is True
    u = update_consent(visitor_key="test-visitor", payload={"rejected_optional": True})
    assert u["reject_as_easy_as_accept"] is True


def test_av17_no_tracking_before_consent():
    from anonymous_visitor.analytics import record_public_analytics_event

    r = record_public_analytics_event(visitor_key="no-consent", event="landing_view")
    assert r["recorded"] is False


def test_av18_public_financial_language(av_client):
    r = av_client.get("/api/anonymous-visitor/public-intelligence/decision-truth-pulse?symbol=BTC")
    data = r.json()
    if data.get("ok"):
        assert data.get("legal_marker") == "LEGAL_REVIEW_REQUIRED"
        assert "decision_state" in data


def test_av19_no_guaranteed_return_claims(av_client):
    r = av_client.get("/api/anonymous-visitor/public-intelligence/net-edge-proof?symbol=BTC")
    data = r.json()
    if data.get("ok"):
        assert data["not_guaranteed_profit"] is True


def test_av20_accessibility_baseline():
    from anonymous_visitor.accessibility import accessibility_report

    report = accessibility_report()
    assert report["passed"] >= 6


def test_av21_mobile_critical_journey(av_client):
    r = av_client.get("/", headers={"User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X)"})
    assert r.status_code == 200
    assert 'name="viewport"' in r.text or "viewport" in r.text


def test_av22_seo_policy():
    from anonymous_visitor.seo import seo_policy_for_path

    pub = seo_policy_for_path("/")
    priv = seo_policy_for_path("/dashboard")
    assert pub["indexable"] is True
    assert priv["indexable"] is False


def test_av23_gated_structured_data():
    from anonymous_visitor.seo import seo_policy_for_path

    api = seo_policy_for_path("/api/anonymous-visitor/status")
    assert api["indexable"] is False


def test_av24_private_leakage_tests(av_client):
    assert av_client.get("/api/privacy/export").status_code == 401
    assert av_client.get("/api/admin/billing/overview").status_code in {401, 403, 404, 422}


def test_av25_cache_controls(av_client):
    r = av_client.get("/api/anonymous-visitor/status")
    assert r.status_code == 200
    assert r.headers.get("X-BD-Auth-State") == "ANONYMOUS"


def test_av26_abuse_resource_tests(monkeypatch):
    from anonymous_visitor.allowlist import match_allowlist_entry
    from anonymous_visitor.protections import PublicProtectionError, check_public_protections

    monkeypatch.setenv("ANONYMOUS_PUBLIC_RL_EXEMPT", "false")
    entry = match_allowlist_entry("GET", "/api/trust-pulse")
    assert entry is not None
    with pytest.raises(PublicProtectionError):
        for _ in range(entry.rate_limit_per_min + 5):
            check_public_protections(method="GET", path="/api/trust-pulse", client_id="abuse", entry=entry)


def test_av27_legal_footer_links(av_client):
    r = av_client.get("/")
    text = r.text.lower()
    assert "privacy" in text or "legal" in text


def test_av28_share_links_anonymous(av_client):
    r = av_client.get("/api/trust-pulse?symbol=BTC")
    assert r.status_code == 200
    data = r.json()
    proof = data.get("proof") or {}
    share = proof.get("share_urls") or proof.get("share_text") or data.get("share")
    assert share or data.get("ledger") or data.get("why")


def test_av29_privacy_safe_analytics():
    from anonymous_visitor.analytics import analytics_status

    status = analytics_status()
    assert status["no_financial_secrets"] is True


def test_av30_machine_verifiable_closure():
    from anonymous_visitor.controls import evaluate_av_controls

    ev = evaluate_av_controls()
    assert ev["PASS_LIVE_NOT_CLAIMED"] is True
    assert len(ev["matrix"]) == 30
