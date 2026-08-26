"""Tests — News Integration #575 (merged into AI Content Engine)."""

from __future__ import annotations

import json

import pytest

from bd_platform import ai_content_engine as ace


@pytest.fixture
def news_seed(tmp_path, monkeypatch):
    p = tmp_path / "ai_content_engine_seed.json"
    p.write_text(json.dumps({
        "legal_review": {"complete": True},
        "evidence_items": [],
        "digests": {},
        "screener": {"default_weights": {}, "assets": []},
        "news_items": [
            {
                "asset": "BTC",
                "headline": "BTC headline A",
                "summary": "Summary A",
                "source": "Source A",
                "source_url": "https://example.com/a",
                "published_at": "2026-08-26T10:00:00Z",
                "tags": ["btc"],
                "dedupe_key": "dup_key",
            },
            {
                "asset": "BTC",
                "headline": "BTC headline A duplicate",
                "summary": "Duplicate",
                "source": "Source A",
                "source_url": "https://example.com/a",
                "published_at": "2026-08-26T09:00:00Z",
                "tags": ["btc"],
                "dedupe_key": "dup_key",
            },
            {
                "asset": "BTC",
                "headline": "BTC headline B",
                "summary": "Summary B",
                "source": "Source B",
                "source_url": "https://example.com/b",
                "published_at": "2026-08-26T11:00:00Z",
                "tags": ["on-chain"],
                "dedupe_key": "unique_b",
            },
        ],
    }), encoding="utf-8")
    monkeypatch.setattr(ace, "_SEED_PATH", p)
    return p


def test_news_panel_dedupes(news_seed):
    panel = ace.build_news_panel(asset="BTC")
    assert panel["ok"] is True
    assert panel["article_count"] == 2
    assert panel["deduplicated"] == 1
    assert panel["no_duplicate_spam"] is True


def test_source_links_preserved(news_seed):
    panel = ace.build_news_panel(asset="BTC")
    assert panel["source_links_preserved"] is True
    for article in panel["articles"]:
        assert article["source_link_preserved"] is True
        assert article["source_url"].startswith("https://")


def test_news_ranked_by_date(news_seed):
    panel = ace.build_news_panel(asset="BTC")
    dates = [a["published_at"] for a in panel["articles"]]
    assert dates == sorted(dates, reverse=True)


def test_news_merged_not_standalone(news_seed):
    panel = ace.build_news_panel(asset="BTC")
    assert panel["standalone_rejected"] is True
    assert panel["merged_into"] == "AI Content Engine"
    assert panel["sub_module"]["task_id"] == "575"
