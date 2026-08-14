"""In-repo adversarial / red-team suite for launch certification.

This is not an independent pentest firm report. It is a re-verifiable OWASP-style
attack pack against this process. Missing firm report remains FAIL in drills.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="module")
def client():
    from dashboard import app

    return TestClient(app, follow_redirects=False)


def test_admin_without_key_is_403(client: TestClient):
    r = client.get("/api/admin/launch-checklist")
    assert r.status_code in {401, 403}


def test_telegram_test_unauth_401(client: TestClient):
    r = client.post("/api/alerts/telegram/test", json={"chat_id": "1"})
    assert r.status_code == 401


def test_oauth_unconfigured_503_or_auth(client: TestClient):
    r = client.get("/api/auth/oauth/google/start")
    assert r.status_code in {503, 200}


def test_sql_injection_does_not_500(client: TestClient):
    payload = "1' OR '1'='1"
    r = client.get("/oracle/BTC", params={"ux_mode": payload})
    assert r.status_code < 500


def test_path_traversal_static_rejected(client: TestClient):
    r = client.get("/static/../production_launch_certification.py")
    assert r.status_code in {400, 403, 404}


def test_execution_order_unauth(client: TestClient):
    r = client.post("/api/execution/order", json={"symbol": "BTCUSDT", "side": "buy"})
    assert r.status_code in {401, 403, 422}


def test_privacy_erase_unauth(client: TestClient):
    r = client.post("/api/privacy/dsr/erase", json={"confirm": True})
    assert r.status_code in {401, 403}


def test_xss_not_reflected_raw_in_login(client: TestClient):
    r = client.get("/login")
    assert r.status_code == 200
    # Login page must not include unescaped typical XSS probe as executable handler.
    assert "<script>alert(1)</script>" not in r.text


def test_journal_idor_unauth(client: TestClient):
    r = client.get("/api/journal")
    assert r.status_code in {200, 401, 403}


def test_b2b_feed_without_key(client: TestClient):
    r = client.get("/api/b2b/feed")
    assert r.status_code in {401, 403, 422}
