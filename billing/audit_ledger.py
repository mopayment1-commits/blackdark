"""Immutable billing audit ledger — who / what / when / why."""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.Billing.Audit")


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


async def record_audit(
    *,
    action: str,
    actor: str,
    user_id: int | None = None,
    email: str | None = None,
    old_plan: str | None = None,
    new_plan: str | None = None,
    old_status: str | None = None,
    new_status: str | None = None,
    amount_cents: int | None = None,
    currency: str = "usd",
    payment_event_id: int | None = None,
    provider_subscription_id: str | None = None,
    reason: str | None = None,
    entitlements_version: int | None = None,
    metadata: dict[str, Any] | None = None,
) -> int:
    from database import get_connection

    async with get_connection() as db:
        cursor = await db.execute(
            """
            INSERT INTO billing_audit_ledger (
                timestamp, actor, action, user_id, email,
                old_plan, new_plan, old_status, new_status,
                amount_cents, currency, payment_event_id,
                provider_subscription_id, reason, entitlements_version, metadata_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _utcnow_iso(),
                actor,
                action,
                user_id,
                (email or "").strip().lower() or None,
                old_plan,
                new_plan,
                old_status,
                new_status,
                amount_cents,
                currency,
                payment_event_id,
                provider_subscription_id,
                reason,
                entitlements_version,
                json.dumps(metadata or {}, separators=(",", ":"), default=str),
            ),
        )
        row_id = int(cursor.lastrowid or 0)
    logger.info(
        "billing_audit | action=%s user_id=%s email=%s %s→%s",
        action,
        user_id,
        email,
        old_plan,
        new_plan,
    )
    return row_id


async def fetch_audit_for_user(user_id: int, *, limit: int = 50) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT * FROM billing_audit_ledger
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (int(user_id), int(limit)),
            )
        ).fetchall()
    return [dict(r) for r in rows]
