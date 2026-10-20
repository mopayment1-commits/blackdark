"""Profile page — header link and API actions used by profile buttons."""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient


def test_authenticated_profile_page_has_scripts_and_handlers():
    from dashboard import app

    c = TestClient(app)
    email = f"prof-act-{uuid.uuid4().hex[:10]}@example.com"
    reg = c.post(
        "/api/auth/register",
        json={"email": email, "password": "SecurePass1234!", "accepted_terms": True},
        headers={"Origin": "https://testserver"},
    )
    assert reg.status_code == 200, reg.text
    html = c.get("/profile", headers={"Accept": "text/html"}).text
    assert "profile_page.js" in html
    assert 'id="bdAccountProfileLink"' in html
    assert 'href="/profile"' in html
    assert 'data-bd-call="saveProfile"' in html

    me = c.get("/api/auth/me").json()
    assert me.get("authenticated") is True

    patch = c.patch(
        "/api/auth/profile",
        json={"name": "Test Display", "timezone": "UTC"},
        headers={"Origin": "https://testserver"},
    )
    assert patch.status_code == 200, patch.text

    del_avatar = c.delete("/api/auth/avatar", headers={"Origin": "https://testserver"})
    assert del_avatar.status_code == 200, del_avatar.text
