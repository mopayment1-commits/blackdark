"""B2B pilot call booking page and API."""

from __future__ import annotations

import os

import pytest

os.environ.setdefault("ENV", "development")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-b2b-pilot")

from anonymous_route_foundation import is_anonymous_route_allowed
from dashboard import app


@pytest.fixture()
def client():
    from starlette.testclient import TestClient

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_pilot_routes_allowed_anonymous():
    assert is_anonymous_route_allowed("GET", "/b2b/pilot") is True
    assert is_anonymous_route_allowed("POST", "/api/b2b/pilot-request") is True


def test_b2b_page_pilot_link_not_mailto(client):
    html = client.get("/b2b").text
    assert 'href="/b2b/pilot"' in html
    assert "Book Pilot Call" in html
    assert "mailto:info@blackdark.io" not in html or html.count("mailto:info@blackdark.io") == 0


def test_b2b_elite_cta_anonymous_registers(client):
    html = client.get("/b2b").text
    assert 'href="/login?tab=register&amp;plan=elite">SEE THE EDGE / ELITE</a>' in html


def test_b2b_elite_cta_authenticated_checkout(client, monkeypatch):
    async def _fake_user(_request):
        return {"email": "elite@example.com", "name": "Elite", "tier": "free"}

    monkeypatch.setattr("dashboard._resolve_html_auth_user", _fake_user)
    html = client.get("/b2b").text
    assert 'href="/create-checkout-session?tier=elite">SEE THE EDGE / ELITE</a>' in html


def test_pilot_page_renders_form(client):
    res = client.get("/b2b/pilot")
    assert res.status_code == 200
    assert "Book a Pilot Call" in res.text
    assert 'id="pilotRequestForm"' in res.text


def test_pilot_request_post_stores(client, monkeypatch):
    stored = {}

    async def fake_insert(**kwargs):
        stored.update(kwargs)
        return 42

    monkeypatch.setattr("database.insert_b2b_pilot_request", fake_insert)

    res = client.post(
        "/api/b2b/pilot-request",
        json={
            "name": "Ada",
            "email": "ada@fund.example",
            "company": "Example Fund",
            "message": "Pilot for emerging terminal",
        },
    )
    assert res.status_code == 200
    body = res.json()
    assert body.get("ok") is True
    assert stored.get("email") == "ada@fund.example"
    assert stored.get("company") == "Example Fund"
