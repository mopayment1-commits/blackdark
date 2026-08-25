"""
News Context Panel — Feature #216 (Sprint 1).

News linked to charts with mandatory source links, deduplication,
asset relevance scoring, and honest news display (not trading signals).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.NewsContext")

_FEATURE_ID = 216
_SEED_PATH = Path("data/news_context_seed.json")
_STORE_PATH = Path("data/news_context.json")
_DISCLAIMER = "News aggregation does not imply endorsement or recommendation."
_DISCLAIMER_AR = "تجميع الأخبار لا يعني تأييداً أو توصية."

Relevance = Literal["high", "medium", "low"]

_RELEVANCE_KEYWORDS: dict[str, list[str]] = {
    "high": ["etf", "sec", "fed", "hack", "approval", "ban", "rate cut", "whale"],
    "medium": ["upgrade", "tvl", "regulation", "outage", "defi", "mica"],
    "low": ["partnership", "conference", "announcement"],
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> list[dict[str, Any]]:
    if not _SEED_PATH.is_file():
        return []
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("news context seed load failed: %s", exc)
        return []


def _load_store() -> dict[str, Any]:
    if _STORE_PATH.is_file():
        try:
            return json.loads(_STORE_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            pass
    store = {"articles": _load_seed(), "updated_at": _utcnow()}
    _STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    _STORE_PATH.write_text(json.dumps(store, indent=2, ensure_ascii=False), encoding="utf-8")
    return store


def _dedupe_key(headline: str, dedupe_group: str | None = None) -> str:
    if dedupe_group:
        return dedupe_group
    normalized = re.sub(r"[^a-z0-9]+", "", headline.lower())
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


def _minutes_ago(published_at_utc: str) -> str:
    try:
        pub = datetime.fromisoformat(published_at_utc.replace("Z", "+00:00"))
        delta = datetime.now(UTC) - pub
        minutes = max(0, int(delta.total_seconds() / 60))
        if minutes < 60:
            return f"Published: {minutes} minutes ago"
        hours = minutes // 60
        return f"Published: {hours} hours ago"
    except ValueError:
        return "Published: unknown"


def _entity_relevance(headline: str, summary: str, assets: list[str]) -> Relevance:
    text = f"{headline} {summary}".lower()
    for kw in _RELEVANCE_KEYWORDS["high"]:
        if kw in text:
            return "high"
    for kw in _RELEVANCE_KEYWORDS["medium"]:
        if kw in text:
            return "medium"
    if len(assets) >= 2:
        return "medium"
    return "low"


def _news_display(headline: str, topic: str) -> str:
    topic_label = topic.replace("_", " ").title() if topic else "General"
    return f"News: {topic_label}"


def _dedupe_articles(articles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Dedupe — same story from N sources = 1 card with N sources."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for article in articles:
        key = _dedupe_key(
            str(article.get("headline") or ""),
            article.get("dedupe_group"),
        )
        groups.setdefault(key, []).append(article)

    cards: list[dict[str, Any]] = []
    for key, group in groups.items():
        group.sort(key=lambda a: a.get("published_at_utc") or "", reverse=True)
        primary = group[0]
        sources = [
            {"source": a.get("source"), "source_url": a.get("source_url")}
            for a in group
            if a.get("source_url")
        ]
        if not sources:
            continue

        relevance = _entity_relevance(
            str(primary.get("headline") or ""),
            str(primary.get("summary") or ""),
            primary.get("assets") or [],
        )
        source_count = len(sources)
        cards.append({
            "card_id": key,
            "headline": primary.get("headline"),
            "summary": primary.get("summary"),
            "topic": primary.get("topic"),
            "assets": primary.get("assets") or [],
            "published_at_utc": primary.get("published_at_utc"),
            "time_display": _minutes_ago(str(primary.get("published_at_utc") or "")),
            "sources": sources,
            "source_count": source_count,
            "source_count_display": f"{source_count} source{'s' if source_count != 1 else ''}",
            "primary_source_url": sources[0]["source_url"],
            "source_line": f"Source: {sources[0]['source']} | {sources[0]['source_url']}",
            "relevance": relevance,
            "relevance_display": f"Relevance: {relevance.title()}",
            "news_display": _news_display(str(primary.get("headline") or ""), str(primary.get("topic") or "")),
            "not_a_signal": True,
            "deduped": source_count > 1,
            "dedupe_group": primary.get("dedupe_group"),
        })
    cards.sort(key=lambda c: c.get("published_at_utc") or "", reverse=True)
    return cards


def list_news_context(
    *,
    asset: str | None = None,
    relevance: Relevance | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    store = _load_store()
    articles = list(store.get("articles") or [])

    if asset:
        sym = asset.upper()
        articles = [
            a for a in articles
            if sym in [x.upper() for x in (a.get("assets") or [])]
        ]

    cards = _dedupe_articles(articles)

    if relevance:
        cards = [c for c in cards if c.get("relevance") == relevance]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "mode": "news_context_panel",
        "count": len(cards[:limit]),
        "cards": cards[:limit],
        "source_links_required": True,
        "dedupe_enabled": True,
        "not_a_signal": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_ar": _DISCLAIMER_AR,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }


def get_news_card(card_id: str) -> dict[str, Any]:
    feed = list_news_context(limit=200)
    for card in feed.get("cards") or []:
        if card.get("card_id") == card_id:
            return {
                "ok": True,
                "feature_id": _FEATURE_ID,
                "card": card,
                "disclaimer": _DISCLAIMER,
                "disclaimer_hideable": False,
                "timestamp": _utcnow(),
            }
    return {"ok": False, "error": "card_not_found"}


async def refresh_news_from_feeds(*, limit: int = 15) -> dict[str, Any]:
    """Import live headlines from CoinDesk RSS — source links mandatory."""
    from bd_platform.free_market_data import coindesk_rss

    imported: list[dict[str, Any]] = []
    rss = await coindesk_rss(limit=limit)
    for item in rss:
        link = str(item.get("link") or "").strip()
        if not link:
            continue
        headline = str(item.get("title") or "")
        imported.append({
            "id": _dedupe_key(headline),
            "headline": headline,
            "summary": str(item.get("summary") or "")[:300],
            "source": str(item.get("source") or "coindesk"),
            "source_url": link,
            "published_at_utc": _utcnow(),
            "assets": _extract_assets(headline),
            "dedupe_group": _dedupe_key(headline),
            "topic": _topic_from_headline(headline),
        })

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "imported_count": len(imported),
        "articles": imported,
        "source_links_required": True,
        "timestamp": _utcnow(),
    }


def _extract_assets(text: str) -> list[str]:
    assets = []
    upper = text.upper()
    for sym in ("BTC", "ETH", "SOL", "BNB", "XRP", "BITCOIN", "ETHEREUM"):
        if sym in upper:
            assets.append(sym.replace("BITCOIN", "BTC").replace("ETHEREUM", "ETH"))
    return list(dict.fromkeys(assets)) or ["BTC"]


def _topic_from_headline(headline: str) -> str:
    lower = headline.lower()
    if any(k in lower for k in ("sec", "etf", "regulation", "mica")):
        return "regulation"
    if any(k in lower for k in ("fed", "rate", "inflation")):
        return "macro"
    if any(k in lower for k in ("hack", "exploit")):
        return "security"
    return "general"


def news_context_status() -> dict[str, Any]:
    store = _load_store()
    articles = store.get("articles") or []
    cards = _dedupe_articles(articles)
    deduped_count = sum(1 for c in cards if c.get("deduped"))
    with_source = sum(1 for a in articles if a.get("source_url"))

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "module": "News Context Panel",
        "sprint": 1,
        "article_count": len(articles),
        "card_count": len(cards),
        "deduped_cards": deduped_count,
        "source_links_required": True,
        "articles_with_source": with_source,
        "dedupe_enabled": True,
        "relevance_scoring": True,
        "not_a_signal": True,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
