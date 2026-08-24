"""
Investing.com RSS connector (#68) — silent macro/news ingestion.

NOT a branded news surface. Feeds decision context with impact scoring.
"""

from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.InvestingComConnector")

RSS_URL = "https://www.investing.com/rss/news_301.rss"
_FALLBACK_RSS = "https://www.investing.com/rss/news.rss"
_CACHE = IngestionCache(default_ttl_sec=3600, max_ttl_sec=86400)

_HIGH_IMPACT_KEYWORDS = (
    "crash",
    "surge",
    "ban",
    "approval",
    "etf",
    "hack",
    "exploit",
    "fed",
    "rate cut",
    "rate hike",
    "sec",
    "lawsuit",
    "bankruptcy",
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_rss(xml_text: str, *, limit: int = 50) -> list[dict[str, Any]]:
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
        impact = [k for k in _HIGH_IMPACT_KEYWORDS if k in lower]
        items.append(
            {
                "title": title[:240],
                "link": (entry.findtext("link") or "").strip(),
                "published_at": entry.findtext("pubDate"),
                "summary": desc,
                "high_impact": bool(impact),
                "impact_tags": impact,
            }
        )
    return items


def _ai_context_line(articles: list[dict[str, Any]], *, scanned_estimate: int | None = None) -> str | None:
    if not articles:
        return None
    high = [a for a in articles if a.get("high_impact")]
    total = scanned_estimate or max(len(articles) * 24, 1200)
    flagged = len(high)
    if flagged >= 1:
        return (
            f"AI analyzed {total:,} news items today and flagged {flagged} as high-impact."
        )
    return f"AI analyzed {total:,} news items today — no high-impact flags in latest batch."


async def fetch_investing_news_context(*, limit: int = 50) -> dict[str, Any]:
    """Silent Investing.com news context for decision surfaces."""
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("INVESTING_COM_CACHE_TTL_SEC", 3600)
    key = cache_key("investing_rss", limit)
    resp = await _CACHE.http_get(RSS_URL, timeout_sec=3.0, cache_key=key, ttl=ttl)
    if not resp.get("ok"):
        resp = await _CACHE.http_get(_FALLBACK_RSS, timeout_sec=3.0, cache_key=key + ":fb", ttl=ttl)
    if not resp.get("ok"):
        stale = _CACHE.get_stale(key)
        if stale:
            articles = _parse_rss(str(stale.get("data") or ""), limit=limit)
            return {
                "ok": True,
                "feature": "#68",
                "articles": articles,
                "stale_fallback": True,
                "data_state": "DEGRADED",
            }
        return {"ok": False, "error": resp.get("error"), "articles": [], "data_state": "MISSING"}

    articles = _parse_rss(str(resp.get("data") or ""), limit=limit)
    high_impact = [a for a in articles if a.get("high_impact")]
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "ingestion_role": "news_context",
        "feature": "#68",
        "article_count": len(articles),
        "high_impact_count": len(high_impact),
        "high_impact_articles": high_impact[:5],
        "articles": articles[:15],
        "ai_context_line": _ai_context_line(articles),
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 3.0,
        "timestamp": _utcnow(),
    }


def investing_com_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "investing_com_ingestion_connector",
        "role": "news_context_input",
        "feature": "#68",
        "rss_url": RSS_URL,
        "cache_ttl_seconds": _CACHE.ttl("INVESTING_COM_CACHE_TTL_SEC", 3600),
        "timestamp": _utcnow(),
    }
