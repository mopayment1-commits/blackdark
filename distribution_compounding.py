"""Phase 6 — Product & Distribution Instrumentation."""

from __future__ import annotations

import logging
from typing import Any

from compounding_common import dumps_json, loads_json, utcnow

logger = logging.getLogger("BLACKDARK.DistributionCompounding")


async def track_event(
    *,
    event_type: str,
    payload: dict[str, Any] | None = None,
    user_id: int | None = None,
    session_id: str | None = None,
    source: str | None = None,
    attribution: dict[str, Any] | None = None,
) -> dict[str, Any]:
    from database import get_connection

    row = {
        "event_type": event_type,
        "user_id": user_id,
        "session_id": session_id,
        "source": source,
        "attribution_json": dumps_json(attribution or {}),
        "payload_json": dumps_json(payload or {}),
        "created_at": utcnow(),
    }
    async with get_connection() as db:
        cur = await db.execute(
            """
            INSERT INTO analytics_events (
                event_type, user_id, session_id, source, attribution_json, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["event_type"],
                row["user_id"],
                row["session_id"],
                row["source"],
                row["attribution_json"],
                row["payload_json"],
                row["created_at"],
            ),
        )
        row["id"] = getattr(cur, "lastrowid", None)

    try:
        from observability import increment_metric

        increment_metric("behavior_events_total")
        increment_metric(f"analytics_{event_type}_total")
    except Exception:
        pass
    return row


async def track_signup(*, email: str, source: str = "web", attribution: dict[str, Any] | None = None) -> dict[str, Any]:
    return await track_event(
        event_type="signup",
        payload={"email_domain": email.split("@")[-1] if "@" in email else "unknown"},
        source=source,
        attribution=attribution,
    )


async def track_api_usage(*, path: str, actor: str | None = None) -> dict[str, Any]:
    return await track_event(
        event_type="api_usage",
        payload={"path": path},
        source=actor or "anonymous",
    )


async def track_share(*, object_type: str, object_id: str, channel: str, source: str | None = None) -> dict[str, Any]:
    return await track_event(
        event_type="viral_share",
        payload={"object_type": object_type, "object_id": object_id, "channel": channel},
        source=source,
        attribution={"channel": channel, "object_type": object_type},
    )


async def track_embed(*, embed_id: str, referrer: str | None = None) -> dict[str, Any]:
    return await track_event(
        event_type="viral_embed",
        payload={"embed_id": embed_id},
        source=referrer,
        attribution={"referrer": referrer},
    )


async def track_referral(*, referral_code: str, referred_session: str | None = None) -> dict[str, Any]:
    return await track_event(
        event_type="referral",
        payload={"referral_code": referral_code},
        session_id=referred_session,
        attribution={"referral_code": referral_code},
    )


async def track_subscription_event(
    *,
    event_type: str,
    user_id: int | None = None,
    payload: dict[str, Any] | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    """Subscription lifecycle + upgrade funnel events (Feature #9)."""
    row = await track_event(
        event_type=event_type,
        payload=payload,
        user_id=user_id,
        session_id=session_id,
        source="subscription_lifecycle",
    )
    try:
        from bd_platform.analytics_integrations import posthog_capture

        distinct = f"user:{user_id}" if user_id else (session_id or "anonymous")
        await posthog_capture(event=event_type, distinct_id=distinct, properties=payload or {})
    except Exception:
        pass
    return row


async def analytics_summary(*, limit: int = 100) -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (await db.execute(
            "SELECT event_type, COUNT(*) AS c FROM analytics_events GROUP BY event_type"
        )).fetchall()
        recent = await (await db.execute(
            "SELECT * FROM analytics_events ORDER BY created_at DESC LIMIT ?",
            (max(1, min(limit, 500)),),
        )).fetchall()

    counts = {str(dict(r)["event_type"]): int(dict(r)["c"]) for r in rows}
    return {
        "event_counts": counts,
        "total_events": sum(counts.values()),
        "recent": [_event_api(dict(r)) for r in recent],
        "generated_at": utcnow(),
    }


async def seo_performance() -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        pa = await (await db.execute("SELECT * FROM platform_analytics WHERE id = 1")).fetchone()
    pa_dict = dict(pa) if pa else {}
    viral = await analytics_summary(limit=50)
    shares = viral["event_counts"].get("viral_share", 0)
    embeds = viral["event_counts"].get("viral_embed", 0)
    referrals = viral["event_counts"].get("referral", 0)
    return {
        "page_views": pa_dict.get("page_views", 0),
        "landing_views": pa_dict.get("landing_views", 0),
        "dashboard_views": pa_dict.get("dashboard_views", 0),
        "viral_shares": shares,
        "viral_embeds": embeds,
        "referrals": referrals,
        "seo_surfaces": ["/sitemap.xml", "/robots.txt", "/oracle-accuracy", "/docs"],
        "generated_at": utcnow(),
    }


async def institutional_dashboard_data() -> dict[str, Any]:
    from knowledge_graph import graph_stats
    from learning_compounding import accuracy_track_record

    return {
        "analytics": await analytics_summary(limit=25),
        "seo": await seo_performance(),
        "accuracy": await accuracy_track_record(limit=25),
        "graph": await graph_stats(),
        "generated_at": utcnow(),
    }


def _event_api(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row.get("id"),
        "event_type": row.get("event_type"),
        "user_id": row.get("user_id"),
        "session_id": row.get("session_id"),
        "source": row.get("source"),
        "attribution": loads_json(row.get("attribution_json")),
        "payload": loads_json(row.get("payload_json")),
        "created_at": row.get("created_at"),
    }
