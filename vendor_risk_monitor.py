"""
BLACKDARK — Vendor risk monitoring atop ingestion_source_health.
"""

from __future__ import annotations

from typing import Any


def _risk_tier(success: int, errors: int, *, stale_hours: float | None) -> str:
    total = success + errors
    if total == 0:
        return "unknown"
    error_rate = errors / total
    if error_rate >= 0.25 or (stale_hours is not None and stale_hours > 24):
        return "high"
    if error_rate >= 0.08 or (stale_hours is not None and stale_hours > 6):
        return "medium"
    return "low"


def assess_vendor_row(row: dict[str, Any]) -> dict[str, Any]:
    success = int(row.get("success_count") or 0)
    errors = int(row.get("error_count") or 0)
    total = success + errors
    error_rate = (errors / total) if total else 0.0
    stale_hours = row.get("stale_hours")
    tier = _risk_tier(success, errors, stale_hours=stale_hours)
    factors: list[str] = []
    if error_rate >= 0.25:
        factors.append("high_error_rate")
    elif error_rate >= 0.08:
        factors.append("elevated_error_rate")
    if stale_hours is not None and stale_hours > 6:
        factors.append("stale_feed")
    if row.get("last_error"):
        factors.append("recent_error")
    score = max(0, min(100, int(100 - error_rate * 100 - min(40, (stale_hours or 0) * 2))))
    return {
        **row,
        "vendor_risk_tier": tier,
        "vendor_risk_score": score,
        "vendor_error_rate": round(error_rate, 4),
        "vendor_risk_factors": factors,
    }


async def vendor_risk_dashboard() -> dict[str, Any]:
    from datetime import UTC, datetime

    from database import fetch_ingestion_health_summary

    rows = await fetch_ingestion_health_summary()
    now = datetime.now(UTC)
    enriched: list[dict[str, Any]] = []
    for row in rows:
        stale_hours = None
        last_ok = row.get("last_ok_at")
        if last_ok:
            try:
                ts = datetime.fromisoformat(str(last_ok).replace("Z", "+00:00"))
                stale_hours = max(0.0, (now - ts).total_seconds() / 3600.0)
            except Exception:
                stale_hours = None
        enriched.append(assess_vendor_row({**row, "stale_hours": stale_hours}))
    by_tier: dict[str, int] = {"low": 0, "medium": 0, "high": 0, "unknown": 0}
    for row in enriched:
        by_tier[row["vendor_risk_tier"]] = by_tier.get(row["vendor_risk_tier"], 0) + 1
    return {
        "sources": enriched,
        "summary": by_tier,
        "high_risk_sources": [r["source_id"] for r in enriched if r["vendor_risk_tier"] == "high"],
    }
