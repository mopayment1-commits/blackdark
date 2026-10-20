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


def _row_get(row: Any, idx: int, key: str) -> Any:
    if row is None:
        return None
    if isinstance(row, dict):
        return row.get(key)
    try:
        return row[idx]
    except (TypeError, IndexError):
        return None


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

        from oracle_integrity import live_source_sql, resolved_true_sql

        live_clause = live_source_sql()
        oracle_today_row = await (
            await db.execute(
                f"SELECT COUNT(*) AS c FROM oracle_predictions WHERE timestamp >= ? AND {live_clause}",  # nosec B608
                (day_start,),
            )
        ).fetchone()
        oracle_decisions_today = _row_count(oracle_today_row)

        plan_dist_rows = await (
            await db.execute(
                """
                SELECT plan, COUNT(*) AS c FROM subscription_accounts
                WHERE subscription_status IN ('active', 'trialing', 'past_due')
                GROUP BY plan
                """
            )
        ).fetchall()
        user_levels: dict[str, int] = {}
        subscriptions_public: dict[str, int] = {"free": 0, "pro_decide": 0, "other_paid": 0}
        for prow in plan_dist_rows:
            rd = dict(prow)
            raw_plan = str(rd.get("plan") or "free")
            count = int(rd.get("c") or 0)
            canon = normalize_plan(raw_plan)
            user_levels[canon] = user_levels.get(canon, 0) + count
            if canon == "free":
                subscriptions_public["free"] += count
            elif canon == "pro":
                subscriptions_public["pro_decide"] += count
            else:
                subscriptions_public["other_paid"] += count

        sealed_open_markets = 0
        active_sealed_bets = 0
        try:
            sealed_open_markets = _row_count(
                await (
                    await db.execute(
                        "SELECT COUNT(*) AS c FROM oracle_sealed_markets WHERE status = 'open'"
                    )
                ).fetchone()
            )
            active_sealed_bets = _row_count(
                await (
                    await db.execute(
                        "SELECT COUNT(*) AS c FROM oracle_sealed_market_bets WHERE status = 'open'"
                    )
                ).fetchone()
            )
        except Exception:
            sealed_open_markets = 0
            active_sealed_bets = 0

        miss_bounty_pending = 0
        try:
            miss_bounty_pending = _row_count(
                await (
                    await db.execute(
                        "SELECT COUNT(*) AS c FROM miss_bounty_claims WHERE status = 'pending_review'"
                    )
                ).fetchone()
            )
        except Exception:
            miss_bounty_pending = 0

        resolved_clause = resolved_true_sql()
        ledger_logged = _row_count(
            await (
                await db.execute(f"SELECT COUNT(*) AS c FROM oracle_predictions WHERE {live_clause}")  # nosec B608
            ).fetchone()
        )
        ledger_resolved = _row_count(
            await (
                await db.execute(
                    f"SELECT COUNT(*) AS c FROM oracle_predictions WHERE {resolved_clause} AND {live_clause}"  # nosec B608
                )
            ).fetchone()
        )
        ledger_avg_row = await (
            await db.execute(
                f"""
                SELECT AVG(accuracy_score) AS avg
                FROM oracle_predictions
                WHERE {resolved_clause} AND accuracy_score IS NOT NULL AND {live_clause}
                """  # nosec B608
            )
        ).fetchone()
        ledger_accuracy = 0.0
        if ledger_avg_row is not None:
            try:
                ledger_accuracy = round(float(_row_get(ledger_avg_row, 0, "avg") or 0.0), 2)
            except (TypeError, ValueError):
                ledger_accuracy = 0.0

        recent_oracle_rows = await (
            await db.execute(
                f"""
                SELECT id, asset, verdict, resolved, label, timestamp, accuracy_score
                FROM oracle_predictions
                WHERE {live_clause}
                ORDER BY timestamp DESC, id DESC
                LIMIT 10
                """  # nosec B608
            )
        ).fetchall()

        error_log_rows = await (
            await db.execute(
                """
                SELECT timestamp, actor, action, outcome, request_path, metadata_json
                FROM audit_logs
                WHERE outcome IS NOT NULL AND outcome != 'ok'
                ORDER BY timestamp DESC, id DESC
                LIMIT 10
                """
            )
        ).fetchall()

    recent_decisions: list[dict[str, Any]] = []
    for row in recent_oracle_rows:
        rd = dict(row)
        resolved_flag = rd.get("resolved")
        recent_decisions.append(
            {
                "id": rd.get("id"),
                "asset": rd.get("asset"),
                "verdict": rd.get("verdict"),
                "label": rd.get("label"),
                "resolved": bool(resolved_flag) if resolved_flag is not None else False,
                "timestamp": rd.get("timestamp"),
                "accuracy_score": rd.get("accuracy_score"),
            }
        )

    recent_errors: list[dict[str, Any]] = []
    for row in error_log_rows:
        rd = dict(row)
        meta_raw = rd.pop("metadata_json", None)
        detail = ""
        if meta_raw:
            try:
                meta = json.loads(meta_raw) if isinstance(meta_raw, str) else meta_raw
                if isinstance(meta, dict):
                    detail = str(meta.get("error") or meta.get("detail") or "")[:200]
            except json.JSONDecodeError:
                detail = ""
        recent_errors.append(
            {
                "timestamp": rd.get("timestamp"),
                "actor": rd.get("actor"),
                "action": rd.get("action"),
                "outcome": rd.get("outcome"),
                "path": rd.get("request_path"),
                "detail": detail,
            }
        )

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
            "oracle_predictions",
            "oracle_sealed_markets",
            "oracle_sealed_market_bets",
            "miss_bounty_claims",
            "audit_logs",
            "billing.plan_registry (price_cents for MRR from DB plan ids only)",
        ],
        "subscriptions_by_tier": subscriptions_public,
        "user_levels": user_levels,
        "operations": {
            "oracle_decisions_today": oracle_decisions_today,
            "sealed_markets_open": sealed_open_markets,
            "sealed_bets_active": active_sealed_bets,
            "miss_bounty_pending": miss_bounty_pending,
            "ledger": {
                "logged": ledger_logged,
                "resolved": ledger_resolved,
                "pending": max(0, ledger_logged - ledger_resolved),
                "accuracy_percent": ledger_accuracy,
            },
            "recent_oracle_decisions": recent_decisions,
            "recent_errors": recent_errors,
        },
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
