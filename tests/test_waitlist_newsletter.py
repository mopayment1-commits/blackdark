"""Admin waitlist newsletter broadcast."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("ENV", "development")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-waitlist-newsletter")

from dashboard import app


@pytest.fixture()
def client():
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.fixture()
def admin_headers(monkeypatch):
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key-please-rotate")
    monkeypatch.setenv("ADMIN_MFA_REQUIRED", "false")
    return {"X-Admin-Key": "test-admin-key-please-rotate"}


def test_waitlist_newsletter_routes_registered():
    paths = set(app.openapi().get("paths") or {})
    assert "/api/admin/waitlist/summary" in paths
    assert "/api/admin/waitlist/newsletter" in paths


def test_waitlist_newsletter_requires_admin(client):
    assert client.get("/api/admin/waitlist/summary").status_code in {401, 403}
    assert client.post("/api/admin/waitlist/newsletter", json={"subject": "a", "message": "b"}).status_code in {
        401,
        403,
    }


def test_waitlist_newsletter_send(client, admin_headers, monkeypatch):
    from database import insert_waitlist_signup

    async def _seed():
        await insert_waitlist_signup("newsletter-a@blackdark.test")
        await insert_waitlist_signup("newsletter-b@blackdark.test")

    import asyncio

    asyncio.get_event_loop().run_until_complete(_seed())

    sent_to: list[str] = []

    def _fake_send(to_email: str, subject: str, body: str) -> bool:
        sent_to.append(to_email)
        return True

    monkeypatch.setenv("SMTP_HOST", "smtp.test")
    monkeypatch.setattr("alert_service.send_email_alert", _fake_send)

    res = client.post(
        "/api/admin/waitlist/newsletter",
        headers=admin_headers,
        json={"subject": "Launch update", "message": "Hello waitlist"},
    )
    assert res.status_code == 200
    body = res.json()
    assert body["ok"] is True
    assert body["total"] >= 2
    assert body["sent"] >= 2
    assert "newsletter-a@blackdark.test" in sent_to
    assert "newsletter-b@blackdark.test" in sent_to


def test_admin_dashboard_has_newsletter_button(client, admin_headers):
    res = client.get("/admin", headers=admin_headers)
    assert res.status_code == 200
    assert "newsletterBtn" in res.text
    assert "Send Newsletter" in res.text
