"""Global site shell chrome — header session, nav, footer, login loading."""

from __future__ import annotations

import re
import uuid
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def client():
    from dashboard import app

    return TestClient(app)


def _header_nav(html: str) -> str:
    match = re.search(
        r'<nav class="bd-header-util"[^>]*>.*?</nav>',
        html,
        flags=re.S,
    )
    return match.group(0) if match else ""


def test_header_template_session_branches():
    util = (ROOT / "templates/partials/top_utility.html").read_text(encoding="utf-8")
    global_hdr = (ROOT / "templates/partials/global_header.html").read_text(encoding="utf-8")
    footer = (ROOT / "templates/partials/site_footer.html").read_text(encoding="utf-8")
    assert "header_authenticated" in util
    assert "bd-account-menu" in util
    assert 'id="bdUtilLogin"' in util
    assert 'id="bdUtilSignup"' in util
    assert 'id="bdUtilPricing"' in util
    assert "/profile" in util
    assert 'href="/dashboard"' not in util
    assert "bd-header-upgrade" not in util
    assert "bd-global-links" in global_hdr
    assert "bd-nav-toggle" in global_hdr
    assert "data-nav-key" in global_hdr
    assert "lang_switcher" not in footer
    assert "/terms" in footer and "/privacy" in footer


def test_anonymous_header_shows_login_not_account(client):
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    header = _header_nav(res.text)
    assert 'id="bdUtilLogin"' in header
    assert 'id="bdUtilSignup"' in header
    assert 'id="bdAccountTrigger"' not in header
    assert 'id="bdUtilPricing"' in header
    visible_lang = len(re.findall(r'class="bd-lang-visible"', header))
    assert visible_lang == 1


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
    header = _header_nav(res.text)
    assert 'id="bdUtilLogin"' not in header
    assert 'id="bdUtilSignup"' not in header
    assert 'id="bdUtilPricing"' not in header
    assert 'id="bdAccountTrigger"' in header
    assert 'id="bdAccountAvatar"' in header
    assert "/profile" in header
    assert 'id="bdHeaderLogout"' in header
    assert 'id="bdLangTrigger"' in header
    visible_lang = len(re.findall(r'class="bd-lang-visible"', header))
    assert visible_lang == 1
    assert "FREE" in header


def test_authenticated_dashboard_shows_lang_and_account(client):
    email = f"hdr-dash-{uuid.uuid4().hex[:10]}@example.com"
    reg = client.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass1234!", "accepted_terms": True},
        headers={"Origin": "https://testserver"},
    )
    assert reg.status_code == 200, reg.text
    for path in ("/", "/login", "/dashboard"):
        res = client.get(path, headers={"Accept": "text/html"})
        assert res.status_code == 200, path
        header = _header_nav(res.text)
        assert 'id="bdLangTrigger"' in header, path
        assert 'id="bdUtilLogin"' not in header, path
        assert 'id="bdAccountTrigger"' in header, path


def test_anonymous_login_shows_lang_login_signup(client):
    for path in ("/", "/login"):
        res = client.get(path, headers={"Accept": "text/html"})
        assert res.status_code == 200, path
        header = _header_nav(res.text)
        assert 'id="bdLangTrigger"' in header, path
        assert 'id="bdUtilLogin"' in header, path
        assert 'id="bdUtilSignup"' in header, path
        assert 'id="bdAccountTrigger"' not in header, path


def test_dashboard_auth_gate_has_login_link(client):
    res = client.get("/dashboard", headers={"Accept": "text/html"})
    assert res.status_code in (200, 401)
    assert 'id="gateLoginBtn"' in res.text or 'href="/login' in res.text


def test_nav_active_on_dashboard_lens(client):
    email = f"nav-{uuid.uuid4().hex[:10]}@example.com"
    c = TestClient(__import__("dashboard").app)
    reg = c.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass1234!", "accepted_terms": True},
        headers={"Origin": "https://testserver"},
    )
    assert reg.status_code == 200
    res = c.get("/dashboard?lens=operate", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert 'data-nav-key="operate"' in res.text
    assert 'data-nav-key="operate" class="active"' in res.text or 'data-nav-key="operate"' in res.text and 'aria-current="page"' in res.text
