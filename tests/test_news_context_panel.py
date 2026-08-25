"""Tests — #216 News Context Panel."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from bd_platform import news_context_panel as ncp


@pytest.fixture
def isolated_news(tmp_path, monkeypatch):
    seed = tmp_path / "news_context_seed.json"
    store = tmp_path / "news_context.json"
    seed.write_text(
        json.dumps([
            {
                "id": "n1", "headline": "SEC approves Bitcoin ETF",
                "summary": "SEC approval for spot BTC ETF.",
                "source": "CoinDesk",
                "source_url": "https://coindesk.com/etf",
                "published_at_utc": "2026-08-25T12:00:00+00:00",
                "assets": ["BTC"], "dedupe_group": "etf-approval", "topic": "regulation",
            },
            {
                "id": "n2", "headline": "SEC approves Bitcoin ETF",
                "summary": "Regulators approve BTC ETF.",
                "source": "Reuters",
                "source_url": "https://reuters.com/etf",
                "published_at_utc": "2026-08-25T12:05:00+00:00",
                "assets": ["BTC"], "dedupe_group": "etf-approval", "topic": "regulation",
            },
            {
                "id": "n3", "headline": "ETH upgrade completes",
                "summary": "Ethereum upgrade done.",
                "source": "The Block",
                "source_url": "https://theblock.co/eth",
                "published_at_utc": "2026-08-25T11:00:00+00:00",
                "assets": ["ETH"], "dedupe_group": "eth-upgrade", "topic": "technology",
            },
        ]),
        encoding="utf-8",
    )
    monkeypatch.setattr(ncp, "_SEED_PATH", seed)
    monkeypatch.setattr(ncp, "_STORE_PATH", store)
    return store


def test_source_links_required(isolated_news):
    feed = ncp.list_news_context()
    for card in feed["cards"]:
        assert card.get("primary_source_url")
        assert "Source:" in card["source_line"]


def test_dedupe_multiple_sources(isolated_news):
    feed = ncp.list_news_context()
    etf_cards = [c for c in feed["cards"] if "ETF" in c.get("headline", "")]
    assert len(etf_cards) == 1
    assert etf_cards[0]["source_count"] == 2
    assert "2 sources" in etf_cards[0]["source_count_display"]


def test_relevance_scoring(isolated_news):
    feed = ncp.list_news_context()
    etf = next(c for c in feed["cards"] if "ETF" in c.get("headline", ""))
    assert etf["relevance"] in ("high", "medium", "low")
    assert "Relevance:" in etf["relevance_display"]


def test_not_a_signal(isolated_news):
    feed = ncp.list_news_context()
    for card in feed["cards"]:
        assert card["not_a_signal"] is True
        assert card["news_display"].startswith("News:")
        assert "Buy Signal" not in card["news_display"]
        assert "Sell" not in card["news_display"]


def test_timestamp_display(isolated_news):
    feed = ncp.list_news_context()
    for card in feed["cards"]:
        assert card["time_display"].startswith("Published:")


def test_disclaimer_not_hideable(isolated_news):
    feed = ncp.list_news_context()
    assert "does not imply endorsement" in feed["disclaimer"]
    assert feed["disclaimer_hideable"] is False


def test_asset_filter(isolated_news):
    feed = ncp.list_news_context(asset="ETH")
    assert all("ETH" in c["assets"] for c in feed["cards"])


def test_no_summary_without_source(isolated_news):
    store = ncp._load_store()
    articles = store["articles"]
    for a in articles:
        if a.get("summary"):
            assert a.get("source_url")


def test_full_seed_exists():
    rows = json.loads(Path("data/news_context_seed.json").read_text(encoding="utf-8"))
    assert len(rows) >= 10


def test_api_routes():
    from fastapi.testclient import TestClient
    from dashboard import app

    c = TestClient(app)
    status = c.get("/api/platform/news-context/status")
    assert status.status_code == 200
    assert status.json()["feature_id"] == 216

    feed = c.get("/api/platform/news-context?asset=BTC")
    assert feed.status_code == 200
    assert feed.json()["not_a_signal"] is True
