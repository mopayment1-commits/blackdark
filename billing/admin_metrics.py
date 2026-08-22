"""Admin billing metrics and anomaly detection."""

from __future__ import annotations

from typing import Any


async def billing_metrics() -> dict[str, Any]:
    from database import get_connection

    async with get_connection() as db:
        total = await (await db.execute("SELECT COUNT(*) AS c FROM subscription_accounts")).fetchone()
        active = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM subscription_accounts
                WHERE subscription_status IN ('active', 'trialing', 'canceled')
                  AND plan != 'free'
                """
            )
        ).fetchone()
        expired = await (
            await db.execute(
                "SELECT COUNT(*) AS c FROM subscription_accounts WHERE subscription_status = 'expired'"
            )
        ).fetchone()
        past_due = await (
            await db.execute(
                "SELECT COUNT(*) AS c FROM subscription_accounts WHERE subscription_status = 'past_due'"
            )
        ).fetchone()
        by_plan_rows = await (
            await db.execute(
                """
                SELECT plan, COUNT(*) AS c FROM subscription_accounts
                WHERE plan != 'free' AND subscription_status != 'expired'
                GROUP BY plan
                """
            )
        ).fetchall()
        failed_payments = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM billing_payment_events
                WHERE status = 'failed'
                """
            )
        ).fetchone()
        renewals = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM billing_payment_events
                WHERE event_type = 'renewal' AND status = 'succeeded'
                """
            )
        ).fetchone()
        refunds = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM billing_payment_events
                WHERE status IN ('refunded', 'disputed', 'chargeback')
                """
            )
        ).fetchone()
        cancel_scheduled = await (
            await db.execute(
                "SELECT COUNT(*) AS c FROM subscription_accounts WHERE cancel_at_period_end = 1"
            )
        ).fetchone()
    by_plan = {str(r["plan"]): int(r["c"]) for r in by_plan_rows}
    return {
        "total_accounts": int(total["c"] if total else 0),
        "active_paid": int(active["c"] if active else 0),
        "expired": int(expired["c"] if expired else 0),
        "past_due": int(past_due["c"] if past_due else 0),
        "by_plan": by_plan,
        "failed_payments": int(failed_payments["c"] if failed_payments else 0),
        "renewals": int(renewals["c"] if renewals else 0),
        "refunds_disputes": int(refunds["c"] if refunds else 0),
        "cancel_at_period_end": int(cancel_scheduled["c"] if cancel_scheduled else 0),
    }


async def list_anomalies(*, limit: int = 50) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT user_id, email, plan, subscription_status, payment_status,
                       current_period_end, grace_period_end, cancel_at_period_end
                FROM subscription_accounts
                WHERE subscription_status = 'past_due'
                   OR (payment_status IN ('failed', 'refunded', 'disputed'))
                   OR (cancel_at_period_end = 1)
                ORDER BY updated_at DESC
                LIMIT ?
                """,
                (int(limit),),
            )
        ).fetchall()
    return [dict(r) for r in rows]
