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
    await _fanout_analytics(
        action=action,
        user_id=user_id,
        old_plan=old_plan,
        new_plan=new_plan,
        metadata=metadata,
    )
    return row_id


_AUDIT_EVENT_MAP: dict[str, str] = {
    "ACTIVATE": "subscription_activated",
    "RENEW": "subscription_renewed",
    "RENEWAL_FAILED": "subscription_past_due",
    "CANCEL": "subscription_canceled",
    "EXPIRE": "subscription_expired",
    "UPGRADE": "subscription_upgraded",
    "DOWNGRADE": "subscription_downgrade_scheduled",
    "REVOKE": "subscription_revoked",
    "PAYMENT_FAILED": "subscription_past_due",
}


async def _fanout_analytics(
    *,
    action: str,
    user_id: int | None,
    old_plan: str | None,
    new_plan: str | None,
    metadata: dict[str, Any] | None,
) -> None:
    event_type = _AUDIT_EVENT_MAP.get(action.upper())
    if not event_type:
        return
    try:
        from distribution_compounding import track_subscription_event

        await track_subscription_event(
            event_type=event_type,
            user_id=user_id,
            payload={
                "action": action,
                "old_plan": old_plan,
                "new_plan": new_plan,
                **(metadata or {}),
            },
        )
    except Exception:
        pass


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
