"""Global header session chrome — SSR Login/Sign up vs account menu."""

from __future__ import annotations

import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    from dashboard import app

    return TestClient(app)


def test_header_template_session_branches():
    util = (ROOT / "templates/partials/top_utility.html").read_text(encoding="utf-8")
    assert "header_authenticated" in util
    assert "bd-account-menu" in util
    assert 'id="bdUtilLogin"' in util
    assert 'id="bdUtilSignup"' in util
    assert "bd-fixed-chrome" not in util
    assert "box-shadow" not in util or "bd-account-dropdown" in util


def test_anonymous_header_shows_login_not_account(client):
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert 'id="bdUtilLogin"' in res.text
    assert 'id="bdUtilSignup"' in res.text
    assert 'id="bdAccountTrigger"' not in res.text


def test_authenticated_header_hides_login_shows_account(client):
    email = f"header-{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass1234!", "accepted_terms": True},
        headers={"Origin": "https://testserver"},
    )
    assert reg.status_code == 200, reg.text
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert 'id="bdUtilLogin"' not in res.text
    assert 'id="bdUtilSignup"' not in res.text
    assert 'id="bdAccountTrigger"' in res.text
    assert "/dashboard" in res.text
    assert 'id="bdHeaderLogout"' in res.text
