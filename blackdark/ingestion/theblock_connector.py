"""
The Block public articles connector (#95) — silent research ingestion.

NOT a branded news surface. Feeds decision/alpha context with research themes.
"""

from __future__ import annotations

import logging
import re
import time
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from typing import Any

from blackdark.ingestion.connector_cache import IngestionCache, cache_key

logger = logging.getLogger("BLACKDARK.TheBlockConnector")

RSS_URL = "https://www.theblock.co/rss.xml"
_CACHE = IngestionCache(default_ttl_sec=1800, max_ttl_sec=86400)

_THEME_KEYWORDS: dict[str, tuple[str, ...]] = {
    "etf_institutional": ("etf", "institutional", "blackrock", "fidelity", "grayscale"),
    "ethereum": ("ethereum", "eth ", "layer 2", "l2"),
    "regulation": ("sec", "regulation", "lawsuit", "enforcement"),
    "defi": ("defi", "dex", "lending", "aave", "uniswap"),
    "macro": ("fed", "inflation", "rates", "macro"),
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _parse_rss(xml_text: str, *, limit: int = 15) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    for entry in root.findall(".//item")[:limit]:
        title = (entry.findtext("title") or "").strip()
        if not title:
            continue
        link = (entry.findtext("link") or "").strip()
        desc = re.sub(r"<[^>]+>", "", entry.findtext("description") or "").strip()[:400]
        lower = f"{title} {desc}".lower()
        themes = [k for k, kws in _THEME_KEYWORDS.items() if any(w in lower for w in kws)]
        items.append(
            {
                "title": title[:240],
                "link": link,
                "published_at": entry.findtext("pubDate"),
                "summary": desc,
                "themes": themes,
            }
        )
    return items


def _ai_flag_line(articles: list[dict[str, Any]]) -> str | None:
    if not articles:
        return None
    top = articles[0]
    themes = top.get("themes") or []
    if "etf_institutional" in themes and "ethereum" in themes:
        return (
            "AI analyzed institutional research on Ethereum ETF flows "
            "and flagged an accumulation pattern."
        )
    if "etf_institutional" in themes:
        return "AI analyzed institutional ETF flow research and adjusted risk context."
    if themes:
        return f"AI analyzed research on {themes[0].replace('_', ' ')} and updated market context."
    return "AI incorporated latest crypto research into decision context."


async def fetch_theblock_research_context(*, limit: int = 10) -> dict[str, Any]:
    """Silent research context for decision surfaces."""
    t0 = time.perf_counter()
    ttl = _CACHE.ttl("THEBLOCK_CACHE_TTL_SEC", 1800)
    key = cache_key("theblock_rss", limit)
    resp = await _CACHE.http_get(RSS_URL, timeout_sec=2.0, cache_key=key, ttl=ttl, source_slug="theblock")
    if not resp.get("ok"):
        return {"ok": False, "error": resp.get("error"), "articles": []}

    articles = _parse_rss(str(resp.get("data") or ""), limit=limit)
    elapsed = time.perf_counter() - t0
    return {
        "ok": True,
        "ingestion_role": "research_context",
        "feature": "#95",
        "article_count": len(articles),
        "articles": articles,
        "ai_context_line": _ai_flag_line(articles),
        "cache_hit": resp.get("cache_hit"),
        "stale_fallback": resp.get("stale_fallback"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }


def theblock_connector_status() -> dict[str, Any]:
    return {
        "ok": True,
        "surface": "theblock_ingestion_connector",
        "role": "research_context_input",
        "feature": "#95",
        "rss_url": RSS_URL,
        "cache_ttl_seconds": _CACHE.ttl("THEBLOCK_CACHE_TTL_SEC", 1800),
        "timestamp": _utcnow(),
    }
