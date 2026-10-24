"""Waitlist signup, duplicate handling, and live count."""

import asyncio
import os
import uuid

import pytest

os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-pepper-waitlist-ops")


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from dashboard import app

    return TestClient(app)


def test_waitlist_duplicate_returns_409(client):
    email = f"dup-{uuid.uuid4().hex}@blackdark.test"
    first = client.post("/join-waitlist", json={"email": email, "name": "A"})
    assert first.status_code == 200
    second = client.post("/join-waitlist", json={"email": email, "name": "B"})
    assert second.status_code == 409
    body = second.json()
    assert "already" in str(body.get("detail", "")).lower()


def test_db_count_waitlist_matches_rows(client):
    from database import db_count_waitlist, insert_waitlist_signup

    email = f"cnt-{uuid.uuid4().hex}@blackdark.test"

    async def _run():
        before = await db_count_waitlist()
        await insert_waitlist_signup(email)
        after = await db_count_waitlist()
        assert after >= before + 1

    asyncio.run(_run())

    stats = client.get("/api/analytics/stats")
    assert stats.status_code == 200
    assert int(stats.json().get("waitlist_count") or 0) >= 1


def test_admin_waitlist_entries_requires_admin(client):
    assert client.get("/api/admin/waitlist/entries").status_code in {401, 403}
    assert client.get("/api/admin/waitlist/export.csv").status_code in {401, 403}
