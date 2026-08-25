"""Tests — #197 Weighted Social Sentiment, #200 Connector Coverage Map."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bd_platform import connector_coverage_map as ccm
from bd_platform import weighted_social_sentiment as wss


# ── #197 Weighted Social Sentiment ───────────────────────────────────────────


def test_weights_version_explicit():
    status = wss.weighted_social_sentiment_status()
    assert status["weights_explicit"] is True
    assert status["weights_version"] == "1.0.0"


def test_source_weight_clamped():
    meta = wss.resolve_source_weight("unknown", account_age_days=1, posts_per_day=200, is_bot=True)
    assert 0.1 <= meta["final_weight"] <= 2.0
    assert meta["age_multiplier"] == 0.2


def test_new_account_low_weight():
    new_acct = wss.resolve_source_weight("coindesk", account_age_days=3)
    old_acct = wss.resolve_source_weight("coindesk", account_age_days=365)
    assert new_acct["final_weight"] < old_acct["final_weight"]


def test_weighted_vs_raw_sentiment():
    contributors = [
        {"source_id": "coindesk", "score": 0.8, "channel_type": "news"},
        {"source_id": "bot_1", "score": 1.0, "channel_type": "twitter", "account_age_days": 1, "is_bot": True},
    ]
    result = wss.compute_weighted_sentiment(contributors)
    assert result["weights_version"] == "1.0.0"
    assert result["weighted_sentiment_score"] != result["raw_sentiment_score"]


def test_explain_contributors():
    contributors = [
        {"source_id": "coindesk", "score": 0.7, "channel_type": "news"},
        {"source_id": "analyst_a", "score": 0.6, "channel_type": "twitter"},
        {"source_id": "whale_alert", "score": 0.5, "channel_type": "twitter"},
    ]
    result = wss.compute_weighted_sentiment(contributors)
    explain = wss.explain_contributors(result)
    assert "coindesk" in explain["explanation"].lower() or "Coindesk" in explain["top_contributors"]
    assert explain["channel_mix_pct"]


def test_manipulation_resistance_100_bots():
    contributors = [
        {"source_id": "coindesk", "score": 0.3, "channel_type": "news"},
        {"source_id": "bloomberg", "score": 0.2, "channel_type": "news"},
        {"source_id": "analyst_a", "score": 0.1, "channel_type": "twitter"},
    ]
    test = wss.run_manipulation_resistance_test(contributors, bot_count=100, bot_score=1.0)
    assert test["passed"] is True
    assert test["delta"] <= test["max_allowed_delta"]


@pytest.mark.asyncio
async def test_analyze_weighted_integrates_195(monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unique_social_volume.analyze_unique_social_volume",
        AsyncMock(return_value={"raw_volume": 100, "unique_volume": 10, "display": "test"}),
    )
    result = await wss.analyze_weighted_social_sentiment("BTC", nlp_compound=0.2)
    assert result["ok"] is True
    assert result["social_volume"]["unique_volume"] == 10
    assert result["manipulation_resistance"]["passed"] is True


# ── #200 Connector Coverage Map ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_coverage_map_structure(monkeypatch):
    async def fake_probe(vid, url):
        return {"venue_id": vid, "live": vid != "mexc", "latency_ms": 50, "error": None, "probed_at": "t"}

    monkeypatch.setattr(ccm, "_probe_venue", fake_probe)
    result = await ccm.build_coverage_map(probe_live=True)
    assert result["ok"] is True
    assert result["live_parity"] is True
    assert result["live_venue_count"] >= 1
    assert any("Binance" in line for line in result["display_lines"])


@pytest.mark.asyncio
async def test_coverage_shows_warning_when_down(monkeypatch):
    async def fake_probe(vid, url):
        return {"venue_id": vid, "live": False, "latency_ms": 0, "error": "timeout", "probed_at": "t"}

    monkeypatch.setattr(ccm, "_probe_venue", fake_probe)
    result = await ccm.build_coverage_map(probe_live=True)
    binance = next(v for v in result["venues"] if v["venue_id"] == "binance")
    assert binance["status_icon"] == "⚠️"
    assert binance["pairs_or_pools"] == 0


def test_coverage_status():
    status = ccm.connector_coverage_status()
    assert status["endpoint"] == "/api/v1/coverage"
    assert 200 in status["feature_ids"]
    assert any("194" in str(x) for x in status["integrated_with"])
