"""
Lightweight financial headlines via U.S. agency RSS feeds.

Default feeds (Federal Reserve, SEC, CFTC) are U.S. government press releases —
public information suitable for commercial link-out aggregators (titles + URLs only).
We do not republish full article bodies.
"""

from __future__ import annotations

import logging
import time
import xml.etree.ElementTree as ET
from collections import deque
from typing import Any
from urllib.parse import urlparse

import aiohttp

from config import (
    FINANCIAL_NEWS_CACHE_TTL_SEC,
    FINANCIAL_NEWS_PER_FEED_LIMIT,
    FINANCIAL_NEWS_RPS_LIMIT,
    FINANCIAL_NEWS_RSS_FEEDS,
)

logger = logging.getLogger("BLACKDARK.FinancialNews")

_TIMEOUT = aiohttp.ClientTimeout(total=14)
_HEADERS = {
    "User-Agent": "BLACKDARK/1.0 (+https://blackdark.io)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*",
}

_CACHE: tuple[float, dict[str, Any]] | None = None
_RPS_TIMES: deque[float] = deque(maxlen=FINANCIAL_NEWS_RPS_LIMIT * 2)

_LICENSE_NOTE = (
    "Headlines from U.S. federal agency RSS feeds (public information). "
    "Titles and links only; full articles remain at the publisher. Not investment advice."
)


def _feed_label(feed_url: str) -> str:
    host = urlparse(feed_url).netloc.lower()
    if "federalreserve.gov" in host:
        return "Federal Reserve"
    if "sec.gov" in host:
        return "SEC"
    if "cftc.gov" in host:
        return "CFTC"
    return host or "RSS"


def _try_consume_rps() -> bool:
    now = time.time()
    while _RPS_TIMES and now - _RPS_TIMES[0] > 1.0:
        _RPS_TIMES.popleft()
    if len(_RPS_TIMES) >= FINANCIAL_NEWS_RPS_LIMIT:
        return False
    _RPS_TIMES.append(now)
    return True


def _parse_rss(payload: str, source: str, limit: int) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return items
    for entry in root.findall(".//item")[:limit]:
        title = (entry.findtext("title") or "").strip()
        if not title:
            continue
        link = (entry.findtext("link") or "").strip()
        items.append(
            {
                "title": title[:240],
                "url": link[:2048] if link else None,
                "source": source,
                "published_at": (entry.findtext("pubDate") or "").strip() or None,
            }
        )
    return items


async def _fetch_feed(session: aiohttp.ClientSession, feed_url: str) -> list[dict[str, Any]]:
    if not _try_consume_rps():
        return []
    label = _feed_label(feed_url)
    try:
        async with session.get(feed_url, headers=_HEADERS) as resp:
            if resp.status != 200:
                logger.debug("Financial news RSS HTTP %s %s", resp.status, feed_url)
                return []
            text = await resp.text()
        return _parse_rss(text, label, FINANCIAL_NEWS_PER_FEED_LIMIT)
    except (aiohttp.ClientError, TypeError, ValueError):
        logger.debug("Financial news RSS failed for %s", feed_url, exc_info=True)
        return []


async def fetch_financial_headlines(limit: int = 8) -> dict[str, Any]:
    global _CACHE
    lim = max(1, min(int(limit or 8), 20))
    now = time.time()
    if _CACHE is not None:
        ts, cached = _CACHE
        if now - ts <= FINANCIAL_NEWS_CACHE_TTL_SEC:
            return cached

    headlines: list[dict[str, Any]] = []
    feeds_ok = 0
    if not FINANCIAL_NEWS_RSS_FEEDS:
        return {
            "ok": False,
            "error": "no_feeds_configured",
            "headlines": [],
            "license_note": _LICENSE_NOTE,
        }

    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        for feed_url in FINANCIAL_NEWS_RSS_FEEDS:
            rows = await _fetch_feed(session, feed_url)
            if rows:
                feeds_ok += 1
                headlines.extend(rows)

    # De-dupe by title prefix
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for row in headlines:
        key = (row.get("title") or "")[:80].lower()
        if key in seen:
            continue
        seen.add(key)
        unique.append(row)

    result = {
        "ok": bool(unique),
        "fetched_ok": bool(unique),
        "source": "us_agency_rss",
        "attribution": "Headlines: U.S. Federal Reserve, SEC, CFTC (RSS)",
        "license_note": _LICENSE_NOTE,
        "commercial_use": "link_out_titles_only",
        "feeds_configured": len(FINANCIAL_NEWS_RSS_FEEDS),
        "feeds_with_data": feeds_ok,
        "headlines": unique[:lim],
    }
    _CACHE = (now, result)
    return result
