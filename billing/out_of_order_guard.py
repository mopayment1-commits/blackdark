"""Out-of-order protection (BILL-008)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any


async def should_apply_event(
    *,
    object_id: str,
    event_created_at: int | None,
    event_id: str,
) -> tuple[bool, str]:
    """Return (apply, reason). Older events must not rollback newer state."""
    from database import get_connection

    if not object_id:
        return True, "no_object_id"
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT last_applied_event_id, last_applied_event_created_at, billing_generation
                FROM billing_out_of_order_guard WHERE object_id = ?
                """,
                (object_id,),
            )
        ).fetchone()
        if not row:
            await db.execute(
                """
                INSERT INTO billing_out_of_order_guard (
                    object_id, last_applied_event_id, last_applied_event_created_at, billing_generation
                ) VALUES (?, ?, ?, 1)
                """,
                (object_id, event_id, event_created_at),
            )
            return True, "first_event"
        last_ts = row["last_applied_event_created_at"]
        if event_created_at is None:
            return True, "no_event_timestamp"
        if last_ts is not None and event_created_at < int(last_ts):
            return False, "out_of_order_stale"
        if row["last_applied_event_id"] == event_id:
            return False, "duplicate_event_id"
        await db.execute(
            """
            UPDATE billing_out_of_order_guard
            SET last_applied_event_id = ?,
                last_applied_event_created_at = ?,
                billing_generation = billing_generation + 1
            WHERE object_id = ?
            """,
            (event_id, event_created_at, object_id),
        )
        return True, "accepted"


async def guard_state(object_id: str) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT * FROM billing_out_of_order_guard WHERE object_id = ?",
                (object_id,),
            )
        ).fetchone()
    return dict(row) if row else None
