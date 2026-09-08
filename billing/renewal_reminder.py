"""Renewal reminder — 5 days before renewal (BILL-020)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from billing.financial_arithmetic import from_minor_units
from billing.plan_registry import plan_def


async def find_renewals_due_reminder(*, days_before: int = 5) -> list[dict[str, Any]]:
    from database import get_connection

    now = datetime.now(UTC)
    window_start = (now + timedelta(days=days_before - 1)).isoformat()
    window_end = (now + timedelta(days=days_before + 1)).isoformat()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT sa.* FROM subscription_accounts sa
                LEFT JOIN billing_renewal_reminders rr
                  ON rr.user_id = sa.user_id AND rr.renewal_at = sa.renewal_date
                WHERE sa.plan != 'free'
                  AND sa.auto_renew_enabled = 1
                  AND sa.renewal_date IS NOT NULL
                  AND sa.renewal_date >= ? AND sa.renewal_date <= ?
                  AND rr.id IS NULL
                """,
                (window_start, window_end),
            )
        ).fetchall()
    notices: list[dict[str, Any]] = []
    for row in rows:
        sub = dict(row)
        tier = str(sub.get("plan") or "pro")
        pdef = plan_def(tier)
        amount_minor = int(pdef.get("price_cents") or 0)
        notice = {
            "user_id": sub["user_id"],
            "email": sub["email"],
            "renewal_at": sub.get("renewal_date"),
            "estimated_subtotal_minor": amount_minor,
            "estimated_subtotal": str(from_minor_units(amount_minor)),
            "estimated_tax_minor": 0,
            "estimated_total_minor": amount_minor,
            "estimated_total": str(from_minor_units(amount_minor)),
            "currency": "usd",
            "tier": tier,
        }
        notices.append(notice)
    return notices


async def record_reminder_sent(user_id: int, *, renewal_at: str, delivery_status: str = "queued") -> None:
    from database import get_connection

    now = datetime.now(UTC).isoformat()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO billing_renewal_reminders (
                user_id, renewal_at, notice_sent_at, delivery_status
            ) VALUES (?, ?, ?, ?)
            """,
            (int(user_id), renewal_at, now, delivery_status[:40]),
        )
