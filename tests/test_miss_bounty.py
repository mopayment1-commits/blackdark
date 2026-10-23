"""Verified Miss Bounty rules."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

import pytest

os.environ.setdefault("SOFT_LAUNCH", "1")
os.environ.setdefault("SESSION_TOKEN_PEPPER", "test-miss-bounty")


@pytest.fixture()
def client(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "miss_bounty.db"))
    from starlette.testclient import TestClient

    from dashboard import app

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


@pytest.mark.asyncio
async def test_auto_reject_when_prices_differ(tmp_path, monkeypatch):
    import database

    monkeypatch.setattr(database.config, "DB_PATH", str(tmp_path / "mb2.db"))
    from miss_bounty_service import submit_miss_bounty_claim
    from miss_bounty_store import ensure_miss_bounty_schema

    await ensure_miss_bounty_schema()

    async def fake_elig(*, user_id, prediction_id):
        return {"eligible": True, "reasons": []}

    monkeypatch.setattr("miss_bounty_service.build_claim_eligibility", fake_elig)

    out = await submit_miss_bounty_claim(
        user_id=1,
        decision_link="https://blackdark.io/oracle-accuracy#pred-99",
        source_a_url="https://a.example.com/x",
        source_b_url="https://b.example.com/y",
        source_a_close=100.0,
        source_b_close=200.0,
    )
    assert out["status"] == "auto_rejected"


def test_public_log_endpoint(client):
    res = client.get("/api/oracle/miss-bounty/public-log")
    assert res.status_code == 200
    assert "claims" in res.json()


def test_miss_bounty_log_page(client):
    res = client.get("/miss-bounty-log")
    assert res.status_code == 200
    assert "Miss Bounty Log" in res.text


def test_oracle_accuracy_has_bounty_button_markup(client):
    res = client.get("/oracle-accuracy")
    assert res.status_code == 200
    assert "Claim Miss Bounty" in res.text
    assert "/miss-bounty-log" in res.text
