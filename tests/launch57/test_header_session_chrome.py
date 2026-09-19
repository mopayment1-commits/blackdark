"""Global header session chrome — SSR Login/Sign up vs account menu."""

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
    assert "header_authenticated" in util
    assert "bd-account-menu" in util
    assert 'id="bdUtilLogin"' in util
    assert 'id="bdUtilSignup"' in util
    assert 'id="bdUtilPricing"' in util
    assert "bd-global-links" in global_hdr
    assert "Prove" in global_hdr or "nav.prove" in global_hdr
    assert "bd-fixed-chrome" not in util


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
    assert 'class="bd-lang-visible"' not in header
