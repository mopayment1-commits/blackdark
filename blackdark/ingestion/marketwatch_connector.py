"""
MarketWatch RSS connector (#75) — silent macro/news ingestion.

NOT a branded surface. Feeds decision context with portfolio-relevant macro flags.
"""

from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.MarketWatchConnector")

RSS_URL = "https://feeds.marketwatch.com/marketwatch/topstories/"
_FALLBACK_RSS = "https://feeds.content.dowjones.io/public/rss/mw_topstories"
_CACHE = IngestionCache(default_ttl_sec=1800, max_ttl_sec=86400)

_MACRO_KEYWORDS = (
    "fed",
    "federal reserve",
    "inflation",
    "cpi",
    "jobs report",
    "recession",
    "gdp",
    "treasury",
    "yield",
    "rate hike",
    "rate cut",
    "tariff",
    "trade war",
    "oil",
    "crude",
    "dollar",
    "stocks fall",
    "stocks rise",
    "s&p",
    "nasdaq",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_rss(xml_text: str, *, limit: int = 40) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for entry in root.findall(".//item")[:limit]:
        title = (entry.findtext("title") or "").strip()
        if not title:
            continue
        desc = re.sub(r"<[^>]+>", "", entry.findtext("description") or "").strip()[:400]
        lower = f"{title} {desc}".lower()
        tags = [k for k in _MACRO_KEYWORDS if k in lower]
        items.append(
            {
                "title": title[:240],
                "link": (entry.findtext("link") or "").strip(),
                "published_at": entry.findtext("pubDate"),
                "summary": desc,
                "high_impact": bool(tags),
                "impact_tags": tags,
                "macro_relevant": bool(tags),
            }
        )
    return items


def _ai_context_line(high_impact: list[dict[str, Any]]) -> str | None:
    n = len(high_impact)
    if n == 0:
        return None
    if n == 1:
        return "AI flagged 1 macro event from MarketWatch as high-impact on your portfolio"
    return f"AI flagged {n} macro events from MarketWatch as high-impact on your portfolio"


async def fetch_marketwatch_macro_context(*, limit: int = 40) -> dict[str, Any]:
    """Silent MarketWatch RSS macro context (#75)."""
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("MARKETWATCH_CACHE_TTL_SEC", 1800)
    key = cache_key("marketwatch_rss", limit)
    resp = await _CACHE.http_get(RSS_URL, timeout_sec=3.0, cache_key=key, ttl=ttl, source_slug="marketwatch")
    if not resp.get("ok"):
        resp = await _CACHE.http_get(_FALLBACK_RSS, timeout_sec=3.0, cache_key=key + ":fb", ttl=ttl, source_slug="marketwatch")
    if not resp.get("ok"):
        stale = _CACHE.get_stale(key)
        if stale:
            articles = _parse_rss(str(stale.get("data") or ""), limit=limit)
            high = [a for a in articles if a.get("high_impact")]
            return {
                "ok": True,
                "feature": "#75",
                "articles": articles,
                "high_impact_count": len(high),
                "ai_context_line": _ai_context_line(high),
                "stale_fallback": True,
                "data_state": "DEGRADED",
            }
        return {"ok": False, "error": resp.get("error"), "articles": [], "data_state": "MISSING"}

    articles = _parse_rss(str(resp.get("data") or ""), limit=limit)
    high_impact = [a for a in articles if a.get("high_impact")]
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "ingestion_role": "macro_news_context",
        "feature": "#75",
        "article_count": len(articles),
        "high_impact_count": len(high_impact),
        "high_impact_articles": high_impact[:5],
        "articles": articles[:15],
        "headline": _ai_context_line(high_impact),
        "ai_context_line": _ai_context_line(high_impact),
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


def marketwatch_connector_status() -> dict[str, Any]:
    from blackdark.data.circuit_breaker import is_open

    return {
        "ok": True,
        "surface": "marketwatch_ingestion_connector",
        "role": "macro_news_input",
        "feature": "#75",
        "rss_url": RSS_URL,
        "cache_ttl_seconds": _CACHE.ttl("MARKETWATCH_CACHE_TTL_SEC", 1800),
        "circuit_open": is_open("marketwatch"),
        "fallback_chain": ["marketwatch_rss", "dowjones_fallback", "stale_cache"],
        "timestamp": _utcnow(),
    }
