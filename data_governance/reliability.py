"""Source reliability scoring from operational telemetry."""

from __future__ import annotations

import time
from typing import Any

from data_governance.registry import critical_sources


def _ws_stats() -> dict[str, Any]:
    try:
        from exchange_ws_hub import ws_hub_stats

        return ws_hub_stats()
    except Exception:
        return {}


def _live_book_stats() -> dict[str, Any]:
    try:
        from live_book_hub import hub_stats

        return hub_stats()
    except Exception:
        return {}


def score_source(source_id: str) -> dict[str, Any]:
    ws = _ws_stats()
    book = _live_book_stats()
    uptime = 0.95
    stale_incidents = 0
    if source_id in {"binance_ws", "binance_spot"}:
        uptime = 0.98 if ws.get("binance_connected") else 0.5
        stale_incidents = int(book.get("stale_count") or 0)
    score = max(0.0, min(100.0, uptime * 100 - stale_incidents * 2))
    return {
        "source_id": source_id,
        "reliability_score": round(score, 2),
        "uptime_estimate": uptime,
        "stale_incidents": stale_incidents,
        "measured_at": time.time(),
    }


def reliability_matrix() -> dict[str, Any]:
    scores = [score_source(s.source_id) for s in critical_sources()]
    avg = sum(s["reliability_score"] for s in scores) / max(len(scores), 1)
    return {"sources": scores, "aggregate_score": round(avg, 2), "critical_count": len(scores)}


def source_health_state(source_id: str) -> str:
    s = score_source(source_id)
    if s["reliability_score"] >= 80:
        return "healthy"
    if s["reliability_score"] >= 50:
        return "degraded"
    return "unhealthy"
