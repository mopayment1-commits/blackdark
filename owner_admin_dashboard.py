"""Owner admin dashboard metrics — database-backed only (no invented figures)."""

from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from typing import Any

from billing.plan_registry import normalize_plan, plan_def


def _iso_start(days: int = 0) -> str:
    now = datetime.now(UTC)
    if days == 0:
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        start = now - timedelta(days=days)
    return start.isoformat()


def _row_count(row: Any, key: str = "c") -> int:
    if row is None:
        return 0
    if isinstance(row, dict):
        return int(row.get(key, 0) or 0)
    try:
        return int(row[0])
    except (TypeError, IndexError, ValueError):
        return 0


async def fetch_owner_dashboard_metrics() -> dict[str, Any]:
    from database import get_connection

    day_start = _iso_start(0)
    week_start = _iso_start(7)
    month_start = _iso_start(30)
    active_login_cutoff = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    now_iso = datetime.now(UTC).isoformat()

    async with get_connection() as db:
        total_users = _row_count(
            await (await db.execute("SELECT COUNT(*) AS c FROM users")).fetchone()
        )
        active_users = _row_count(
            await (
                await db.execute(
                    """
                    SELECT COUNT(DISTINCT u.id) AS c FROM users u
                    LEFT JOIN user_sessions s ON s.user_id = u.id AND s.expires_at > ?
                    WHERE (u.last_login_at IS NOT NULL AND u.last_login_at >= ?)
                       OR s.id IS NOT NULL
                    """,
                    (now_iso, active_login_cutoff),
                )
            ).fetchone()
        )
        new_users_today = _row_count(
            await (
                await db.execute(
                    "SELECT COUNT(*) AS c FROM users WHERE created_at >= ?",
                    (day_start,),
                )
            ).fetchone()
        )
        new_users_week = _row_count(
            await (
                await db.execute(
                    "SELECT COUNT(*) AS c FROM users WHERE created_at >= ?",
                    (week_start,),
                )
            ).fetchone()
        )

        total_subscribers = _row_count(
            await (
                await db.execute("SELECT COUNT(*) AS c FROM subscription_accounts")
            ).fetchone()
        )
        paid_subscribers = _row_count(
            await (
                await db.execute(
                    """
                    SELECT COUNT(*) AS c FROM subscription_accounts
                    WHERE plan != 'free'
                      AND subscription_status IN ('active', 'trialing', 'past_due')
                    """
                )
            ).fetchone()
        )
        free_subscribers = _row_count(
            await (
                await db.execute(
                    """
                    SELECT COUNT(*) AS c FROM subscription_accounts
                    WHERE plan = 'free'
                       OR subscription_status IN ('none', 'incomplete')
                    """
                )
            ).fetchone()
        )
        canceled_subscribers = _row_count(
            await (
                await db.execute(
                    """
                    SELECT COUNT(*) AS c FROM subscription_accounts
                    WHERE subscription_status IN ('canceled', 'expired')
                    """
                )
            ).fetchone()
        )

        plan_rows = await (
            await db.execute(
                """
                SELECT plan, COUNT(*) AS c FROM subscription_accounts
                WHERE subscription_status IN ('active', 'trialing', 'past_due')
                  AND plan != 'free'
                GROUP BY plan
                """
            )
        ).fetchall()
        revenue_by_plan: dict[str, int] = {}
        mrr_cents = 0
        for row in plan_rows:
            rd = dict(row)
            plan = normalize_plan(str(rd.get("plan") or "free"))
            count = int(rd.get("c") or 0)
            revenue_by_plan[plan] = count
            mrr_cents += int(plan_def(plan).get("price_cents") or 0) * count

        revenue_total_row = await (
            await db.execute(
                """
                SELECT COALESCE(SUM(amount_cents), 0) AS c FROM billing_payment_events
                WHERE status = 'succeeded' AND amount_cents IS NOT NULL
                """
            )
        ).fetchone()
        revenue_month_row = await (
            await db.execute(
                """
                SELECT COALESCE(SUM(amount_cents), 0) AS c FROM billing_payment_events
                WHERE status = 'succeeded' AND amount_cents IS NOT NULL AND created_at >= ?
                """,
                (month_start,),
            )
        ).fetchone()
        revenue_total_cents = _row_count(revenue_total_row)
        revenue_month_cents = _row_count(revenue_month_row)

        visitor_types = ("page_view", "landing_view", "dashboard_view", "api_usage")

        async def _visitor_count(since: str) -> int:
            row = await (
                await db.execute(
                    """
                    SELECT COUNT(DISTINCT COALESCE(session_id, 'evt:' || CAST(id AS TEXT))) AS c
                    FROM analytics_events
                    WHERE created_at >= ? AND event_type IN (?, ?, ?, ?)
                    """,
                    (since, *visitor_types),
                )
            ).fetchone()
            primary = _row_count(row)
            if primary > 0:
                return primary
            brow = await (
                await db.execute(
                    """
                    SELECT COUNT(DISTINCT COALESCE(session_id, 'evt:' || CAST(id AS TEXT))) AS c
                    FROM behavior_events
                    WHERE created_at >= ?
                    """,
                    (since,),
                )
            ).fetchone()
            return _row_count(brow)

        visitors_today = await _visitor_count(day_start)
        visitors_week = await _visitor_count(week_start)
        visitors_month = await _visitor_count(month_start)

        emails_sent = _row_count(
            await (
                await db.execute("SELECT COUNT(*) AS c FROM alert_delivery_log")
            ).fetchone()
        )
        delivery_rows = await (
            await db.execute("SELECT results_json FROM alert_delivery_log")
        ).fetchall()
        emails_failed = 0
        for dr in delivery_rows:
            raw = dict(dr).get("results_json") or ""
            try:
                parsed = json.loads(raw) if isinstance(raw, str) else raw
            except json.JSONDecodeError:
                parsed = {}
            if isinstance(parsed, dict):
                email_part = parsed.get("email") or parsed
                if isinstance(email_part, dict) and email_part.get("ok") is False:
                    emails_failed += 1
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict) and item.get("channel") == "email" and item.get("ok") is False:
                        emails_failed += 1

        new_subscriptions_today = _row_count(
            await (
                await db.execute(
                    "SELECT COUNT(*) AS c FROM subscription_accounts WHERE created_at >= ?",
                    (day_start,),
                )
            ).fetchone()
        )
        new_subscriptions_week = _row_count(
            await (
                await db.execute(
                    "SELECT COUNT(*) AS c FROM subscription_accounts WHERE created_at >= ?",
                    (week_start,),
                )
            ).fetchone()
        )
        cancellations_week = _row_count(
            await (
                await db.execute(
                    """
                    SELECT COUNT(*) AS c FROM subscription_accounts
                    WHERE subscription_status IN ('canceled', 'expired')
                      AND updated_at >= ?
                    """,
                    (week_start,),
                )
            ).fetchone()
        )
        past_due = _row_count(
            await (
                await db.execute(
                    "SELECT COUNT(*) AS c FROM subscription_accounts WHERE subscription_status = 'past_due'"
                )
            ).fetchone()
        )
        upgrades_week = _row_count(
            await (
                await db.execute(
                    """
                    SELECT COUNT(*) AS c FROM billing_audit_ledger
                    WHERE action LIKE '%upgrade%' AND timestamp >= ?
                    """,
                    (week_start,),
                )
            ).fetchone()
        )
        signups_week = _row_count(
            await (
                await db.execute(
                    """
                    SELECT COUNT(*) AS c FROM analytics_events
                    WHERE event_type = 'signup' AND created_at >= ?
                    """,
                    (week_start,),
                )
            ).fetchone()
        )
        if signups_week == 0:
            signups_week = new_users_week

    paid_accounts = max(paid_subscribers, 0)
    arpu_cents = int(revenue_month_cents / paid_accounts) if paid_accounts else 0

    return {
        "generated_at": now_iso,
        "data_sources": [
            "users",
            "user_sessions",
            "subscription_accounts",
            "billing_payment_events",
            "billing_audit_ledger",
            "analytics_events",
            "behavior_events",
            "alert_delivery_log",
            "billing.plan_registry (price_cents for MRR from DB plan ids only)",
        ],
        "users": {
            "total": total_users,
            "active_30d": active_users,
            "new_today": new_users_today,
            "new_week": new_users_week,
        },
        "subscribers": {
            "total_accounts": total_subscribers,
            "paid": paid_subscribers,
            "free": free_subscribers,
            "canceled": canceled_subscribers,
        },
        "revenue": {
            "mrr_cents": mrr_cents,
            "arr_cents": mrr_cents * 12,
            "total_collected_cents": revenue_total_cents,
            "collected_last_30d_cents": revenue_month_cents,
            "arpu_cents_last_30d": arpu_cents,
            "active_paid_by_plan": revenue_by_plan,
            "nrr_pct": None,
            "grr_pct": None,
            "churn_pct": None,
            "cac": None,
            "ltv_cents": None,
            "notes": {
                "mrr": "Sum of plan_registry.price_cents × active paid accounts (plan from DB).",
                "nrr_grr_churn_cac": "Not stored in DB — shown as null.",
            },
        },
        "visitors": {
            "today": visitors_today,
            "week": visitors_week,
            "month": visitors_month,
        },
        "emails": {
            "sent": emails_sent,
            "opened": None,
            "failed": emails_failed,
            "notes": "Open tracking not persisted in database.",
        },
        "subscriptions": {
            "new_today": new_subscriptions_today,
            "new_week": new_subscriptions_week,
            "canceled_week": cancellations_week,
            "past_due": past_due,
            "upgrades_week": upgrades_week,
            "signups_week": signups_week,
        },
    }
