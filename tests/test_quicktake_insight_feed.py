"""Tests — QuickTake Insight Feed (#184)."""

from __future__ import annotations

import pytest

from bd_platform.quicktake_insight_feed import (
    create_insight,
    list_published_insights,
    moderate_insight,
    quicktake_status,
    submit_for_moderation,
)


@pytest.fixture
def isolated_store(tmp_path, monkeypatch):
    store = tmp_path / "quicktake.json"
    monkeypatch.setattr("bd_platform.quicktake_insight_feed._STORE_PATH", store)
    return store


def test_reject_ungrounded_quantitative_claim(isolated_store):
    out = create_insight(
        author="analyst",
        title="Bad claim",
        summary="test",
        claims=[{"claim": "Liquidity dropped 40%", "evidence": [], "source": None}],
    )
    assert out["ok"] is False
    assert out["error"] == "ungrounded_claim"


def test_create_and_publish_with_moderation(isolated_store):
    created = create_insight(
        author="research",
        title="BTC Brief",
        summary="Market update",
        claims=[
            {
                "claim": "BTC market health is supportive",
                "evidence": [{"type": "chart", "url": "/market-health/BTC"}],
                "source": "2026-01-01T00:00:00+00:00",
                "confidence": 72,
            }
        ],
        confidence=72,
    )
    assert created["ok"] is True
    iid = created["insight"]["id"]
    submitted = submit_for_moderation(insight_id=iid, author="research")
    assert submitted["moderation_state"] == "pending_moderation"
    approved = moderate_insight(insight_id=iid, action="approve", moderator="admin")
    assert approved["moderation_state"] == "published"
    feed = list_published_insights()
    assert feed["count"] == 1
    assert feed["insights"][0]["claims"][0]["evidence"]


def test_quicktake_status(isolated_store):
    status = quicktake_status()
    assert status["feature_id"] == 184
    assert status["no_ungrounded_claims"] is True
