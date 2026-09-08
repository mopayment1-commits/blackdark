"""Fraud / abuse controls (BILL-040)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

logger = logging.getLogger("BLACKDARK.Billing.Fraud")

DEFAULT_VELOCITY_WINDOW_SEC = 3600
DEFAULT_MAX_DECLINES = 5
DEFAULT_MAX_CHECKOUT_ATTEMPTS = 10


async def record_decline(email: str, *, decline_code: str) -> dict[str, Any]:
    from database import get_connection

    now = datetime.now(UTC).isoformat()
    email = email.strip().lower()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO billing_fraud_events (email, event_type, detail, created_at)
            VALUES (?, 'decline', ?, ?)
            """,
            (email, decline_code[:80], now),
        )
    return await check_decline_velocity(email)


async def check_decline_velocity(email: str) -> dict[str, Any]:
    from database import get_connection

    email = email.strip().lower()
    since = (datetime.now(UTC) - timedelta(seconds=DEFAULT_VELOCITY_WINDOW_SEC)).isoformat()
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM billing_fraud_events
                WHERE email = ? AND event_type = 'decline' AND created_at >= ?
                """,
                (email, since),
            )
        ).fetchone()
    count = int(row["c"] if row else 0)
    throttled = count >= DEFAULT_MAX_DECLINES
    if throttled:
        logger.warning("decline_velocity_limit | email=%s count=%s", email, count)
    return {"email": email, "decline_count": count, "throttled": throttled}


async def record_checkout_attempt(email: str) -> dict[str, Any]:
    from database import get_connection

    now = datetime.now(UTC).isoformat()
    email = email.strip().lower()
    since = (datetime.now(UTC) - timedelta(seconds=DEFAULT_VELOCITY_WINDOW_SEC)).isoformat()
    async with get_connection() as db:
        await db.execute(
            """
            INSERT INTO billing_fraud_events (email, event_type, detail, created_at)
            VALUES (?, 'checkout_attempt', 'checkout', ?)
            """,
            (email, now),
        )
        row = await (
            await db.execute(
                """
                SELECT COUNT(*) AS c FROM billing_fraud_events
                WHERE email = ? AND event_type = 'checkout_attempt' AND created_at >= ?
                """,
                (email, since),
            )
        ).fetchone()
    count = int(row["c"] if row else 0)
    blocked = count >= DEFAULT_MAX_CHECKOUT_ATTEMPTS
    return {"email": email, "checkout_attempts": count, "blocked": blocked}
