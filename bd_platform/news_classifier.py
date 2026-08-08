"""News classifier — topic/sentiment + CoinDesk RSS."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


async def classify_headlines(limit: int = 20) -> dict[str, Any]:
    import config
    from sentiment_engine import analyze_sentiment_score_async, fetch_market_sentiment_news

    assets = list(config.WHITELIST_ASSETS)[:5]
    items = await fetch_market_sentiment_news(assets)
    classified: list[dict[str, Any]] = []
    for item in items[:limit]:
        text = str(item.raw_text or "")
        analysis = await analyze_sentiment_score_async(text)
        classified.append({
            "asset": item.asset,
            "source": item.source,
            "text": text[:200],
            "compound_score": analysis.compound_score,
            "topic": _topic_bucket(text),
        })
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "count": len(classified),
        "headlines": classified,
        "reference": "CryptoPanic-style classifier",
    }


async def coindesk_feed(limit: int = 10) -> dict[str, Any]:
    from bd_platform.free_market_data import coindesk_rss
    from sentiment_engine import analyze_sentiment_score_async

    rss_items = await coindesk_rss(limit=limit)
    headlines: list[dict[str, Any]] = []
    for item in rss_items:
        text = str(item.get("title") or "")
        analysis = await analyze_sentiment_score_async(text)
        headlines.append({
            **item,
            "text": text[:200],
            "compound_score": analysis.compound_score,
            "topic": _topic_bucket(text),
        })
    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "source": "coindesk_rss",
        "count": len(headlines),
        "coindesk_count": len(headlines),
        "coindesk_headlines": headlines,
        "headlines": headlines,
    }


def _topic_bucket(text: str) -> str:
    lower = text.lower()
    if any(k in lower for k in ("etf", "sec", "regulation", "ban")):
        return "regulation"
    if any(k in lower for k in ("hack", "exploit", "breach")):
        return "security"
    if any(k in lower for k in ("fed", "inflation", "rate", "macro")):
        return "macro"
    if any(k in lower for k in ("whale", "inflow", "outflow")):
        return "onchain_flow"
    return "general"
