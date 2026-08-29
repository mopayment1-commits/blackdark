"""QuickTake / analyst insight feed (PDF #409)."""

from __future__ import annotations

from typing import Any


async def quicktake_feed_status_409(*, limit: int = 10) -> dict[str, Any]:
    from bd_platform.news_classifier import classify_headlines, coindesk_feed

    feed = await coindesk_feed(limit=limit)
    classified: dict[str, Any] = {"count": 0, "headlines": []}
    try:
        classified = await classify_headlines(limit=limit)
    except Exception as exc:
        classified = {"ok": False, "error": str(exc), "count": 0, "headlines": []}
    return {
        "ok": True,
        "success": True,
        "capability_id": 409,
        "feed": feed,
        "classified": classified,
        "surface": "quicktake_analyst_feed",
    }
