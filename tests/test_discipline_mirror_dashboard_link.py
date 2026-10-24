"""Discipline Mirror — Open Dashboard respects session."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from dashboard import app


def test_discipline_template_uses_dashboard_href_variable():
    html = Path("templates/discipline.html").read_text(encoding="utf-8")
    assert "dashboard_href" in html
    assert 'id="openDashboardBtn"' in html


def test_discipline_mirror_anonymous_gets_login_next_for_dashboard(tmp_path, monkeypatch):
    import database
    from auth_service import hash_password

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "dm.db"))

    async def _setup():
        await database.init_db()
        await database.create_user(
            "mirror@example.com",
            hash_password("strong-pass-12345"),
            "Mirror User",
        )

    asyncio.run(_setup())
    client = TestClient(app, base_url="https://testserver")
    anon = client.get("/discipline-mirror")
    assert anon.status_code == 200
    assert 'href="/login?next=%2Fdashboard"' in anon.text or 'href="/login?next=/dashboard"' in anon.text

    login = client.post(
        "/api/auth/login",
        headers={"Origin": "https://testserver"},
        json={
            "email": "mirror@example.com",
            "password": "strong-pass-12345",
            "remember_me": True,
        },
    )
    assert login.status_code == 200
    authed = client.get("/discipline-mirror")
    assert authed.status_code == 200
    assert 'href="/dashboard"' in authed.text
    dash = client.get("/dashboard")
    assert dash.status_code == 200
    assert "auth_required" not in dash.text.lower() or "account required" not in dash.text.lower()
