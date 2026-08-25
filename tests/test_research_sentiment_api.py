"""Tests — #187 Research Portal, #188 Unified API, #195 Unique Social Volume."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from bd_platform import research_portal as rp
from bd_platform import unique_social_volume as usv
from bd_platform import unified_api_platform as uap


# ── #195 Unique Social Volume ─────────────────────────────────────────────────


def test_deduplication_reduces_volume():
    docs = [
        {"id": "1", "text": "BTC to the moon", "source_id": "a", "source_tier": "community"},
        {"id": "2", "text": "BTC to the moon", "source_id": "b", "source_tier": "unknown", "posts_per_day": 100, "is_bot": True},
        {"id": "3", "text": "Institutional BTC inflows rise", "source_id": "reuters", "source_tier": "verified_media"},
    ]
    result = usv.compute_unique_social_volume(docs)
    assert result["raw_volume"] == 3
    assert result["unique_volume"] == 2
    assert result["duplicate_count"] == 1
    assert "raw" in result["display"].lower()


def test_bot_spam_policy_documented():
    status = usv.unique_social_volume_status()
    assert status["bot_spam_policy_documented"] is True
    assert status["source_level_qa"] is True


def test_weighted_volume_less_than_unique():
    docs = [
        {"id": "1", "text": "alpha", "source_id": "x", "source_tier": "unknown", "posts_per_day": 200, "is_bot": True},
        {"id": "2", "text": "beta", "source_id": "y", "source_tier": "institutional"},
    ]
    result = usv.compute_unique_social_volume(docs)
    assert result["weighted_volume"] < result["unique_volume"]


# ── #187 Research Portal ──────────────────────────────────────────────────────


@pytest.fixture
def isolated_research_store(tmp_path, monkeypatch):
    store = tmp_path / "research_portal.json"
    seed = tmp_path / "research_portal_seed.json"
    seed.write_text(
        '[{"id":"t1","title":"BTC Liquidity Report","author":"Research","sector":"DeFi",'
        '"assets":["BTC"],"tags":["liquidity","BTC"],"summary":"Liquidity analysis",'
        '"body":"Bitcoin liquidity depth on CEX","source":"Internal","publication_date":"2026-01-01","language":"en"},'
        '{"id":"t2","title":"تحليل سيولة البيتكوين","author":"فريق","sector":"DeFi",'
        '"assets":["BTC"],"tags":["سيولة","بيتكوين"],"summary":"تقرير عربي",'
        '"body":"سيولة البيتكوين في البورصات","source":"Internal","publication_date":"2026-01-02","language":"ar"}]',
        encoding="utf-8",
    )
    monkeypatch.setattr(rp, "_STORE_PATH", store)
    monkeypatch.setattr(rp, "_SEED_PATH", seed)
    return store


def test_research_portal_seed_and_count(isolated_research_store):
    status = rp.research_portal_status()
    assert status["report_count"] >= 2


def test_fulltext_search_relevance(isolated_research_store):
    results = rp.search_reports("liquidity BTC", mode="fulltext")
    assert results["count"] >= 1
    assert results["results"][0]["relevance_score"] > 0


def test_semantic_search_arabic(isolated_research_store):
    results = rp.search_reports("تقارير عن سيولة البيتكوين", mode="semantic")
    assert results["count"] >= 1
    titles = [r["title"] for r in results["results"]]
    assert any("سيولة" in t or "Liquidity" in t for t in titles)


def test_version_archive_on_update(isolated_research_store):
    updated = rp.update_report("t1", editor_id="editor", summary="Updated summary v2")
    assert updated["ok"] is True
    assert updated["version"] == 2
    assert updated["previous_versions"] == 1

    archived = rp.get_report("t1", version=1)
    assert archived["ok"] is True
    assert archived["archived"] is True
    assert archived["report"]["summary"] != "Updated summary v2"


def test_saved_items(isolated_research_store):
    rp.save_report_for_user("user-1", "t1")
    saved = rp.list_saved_reports("user-1")
    assert saved["count"] == 1
    assert saved["saved"][0]["id"] == "t1"


def test_source_metadata_present(isolated_research_store):
    report = rp.get_report("t1")
    r = report["report"]
    assert r.get("source")
    assert r.get("publication_date")
    assert r.get("author")


# ── #188 Unified API (merged SanAPI-style) ───────────────────────────────────


def test_unified_api_status_includes_188():
    status = uap.unified_api_status()
    assert 188 in status["merged_feature_ids"]
    assert status["daily_quotas"]["pro"] == 1000
    assert status["daily_quotas"]["institutional"] == 10000
    assert status["principle"] == "What you see in UI = what you get in API"


def test_tier_quotas():
    pro = uap.get_tier_quota("pro")
    inst = uap.get_tier_quota("institutional")
    assert pro["daily_limit"] == 1000
    assert inst["daily_limit"] == 10000


def test_metric_contracts_defined():
    contracts = uap.unified_api_status()["metric_contracts"]
    assert "sentiment" in contracts
    assert "social_volume" in contracts
    assert "weighted_sentiment_score" in contracts["sentiment"]


@pytest.mark.asyncio
async def test_graphql_requires_pro():
    result = await uap.execute_graphql_query("{ price sentiment }", tier="free")
    assert result["ok"] is False
    assert result["error"] == "graphql_pro_required"


@pytest.mark.asyncio
async def test_graphql_pro_tier(monkeypatch):
    monkeypatch.setattr(uap, "fetch_price", AsyncMock(return_value={"data": {"price_usd": 100}}))
    monkeypatch.setattr(uap, "fetch_sentiment", AsyncMock(return_value={"data": {"weighted_sentiment_score": 0.5}}))
    result = await uap.execute_graphql_query("{ price sentiment }", variables={"asset": "BTC"}, tier="pro")
    assert result["ok"] is True
    assert "price" in result["data"]
    assert result["ui_parity"] is True


@pytest.mark.asyncio
async def test_fetch_social_volume_envelope(monkeypatch):
    monkeypatch.setattr(
        "bd_platform.unique_social_volume.analyze_unique_social_volume",
        AsyncMock(return_value={"ok": True, "raw_volume": 100, "unique_volume": 12, "weighted_volume": 8, "display": "test"}),
    )
    result = await uap.fetch_social_volume("BTC")
    assert result["ok"] is True
    assert result["data"]["raw_volume"] == 100
    assert result["metadata"]["source"] == "unique_social_volume"
