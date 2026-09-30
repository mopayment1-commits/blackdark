"""Wave 6 — guest surfaces: /, /login, guest-trust sample."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[2]


def test_homepage_loads_without_500():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "bd_token" not in res.text.lower() or "localStorage" not in res.text


def test_login_page_no_session_secrets_in_html():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/login", headers={"Accept": "text/html"})
    assert res.status_code == 200
    assert "SECRETS_MASTER_KEY" not in res.text
    assert "AUDIT_SIGNING_KEY" not in res.text


def test_guest_trust_api_not_500():
    from dashboard import app

    client = TestClient(app)
    res = client.get("/api/launch57/guest-trust", params={"symbol": "BTC"})
    assert res.status_code == 200, res.text


def test_landing_no_false_live_label_pattern():
    landing = (ROOT / "templates" / "landing.html").read_text(encoding="utf-8")
    badge = landing.split("function _lpFreshnessBadge", 1)[1].split("function fetchLaunch57GuestTrust", 1)[0]
    assert "presentedAsLive === true" in badge or "presentedAsLive" in badge
    assert re.search(r"knownFresh\s*\?\s*['\"]Live['\"]", landing) is None
