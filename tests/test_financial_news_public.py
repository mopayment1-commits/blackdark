"""U.S. agency RSS financial headlines (public API)."""

import pytest

from financial_news_public import _parse_rss, fetch_financial_headlines


SAMPLE_RSS = """<?xml version="1.0"?>
<rss><channel>
<item><title>Fed holds rates steady</title><link>https://example.gov/a</link><pubDate>Wed, 22 Oct 2026</pubDate></item>
<item><title>SEC filing update</title><link>https://example.gov/b</link></item>
</channel></rss>"""


def test_parse_rss():
    rows = _parse_rss(SAMPLE_RSS, "Federal Reserve", 5)
    assert len(rows) == 2
    assert rows[0]["title"] == "Fed holds rates steady"
    assert rows[0]["url"] == "https://example.gov/a"


@pytest.mark.asyncio
async def test_fetch_financial_headlines(monkeypatch):
    async def fake_fetch(session, feed_url):
        return _parse_rss(SAMPLE_RSS, "Test", 5)

    monkeypatch.setattr("financial_news_public.FINANCIAL_NEWS_RSS_FEEDS", ["https://test.local/rss"])
    monkeypatch.setattr("financial_news_public._fetch_feed", fake_fetch)
    monkeypatch.setattr("financial_news_public._CACHE", None)
    out = await fetch_financial_headlines(limit=5)
    assert out["ok"] is True
    assert out["commercial_use"] == "link_out_titles_only"
    assert len(out["headlines"]) >= 1


def test_public_news_route(monkeypatch):
    from dashboard import app
    from fastapi.testclient import TestClient

    async def fake_headlines(limit=8):
        return {"ok": True, "headlines": [{"title": "x", "source": "SEC"}]}

    monkeypatch.setattr("financial_news_public.fetch_financial_headlines", fake_headlines)
    client = TestClient(app)
    res = client.get("/api/public/news/headlines")
    assert res.status_code == 200
    assert res.json().get("headlines")
