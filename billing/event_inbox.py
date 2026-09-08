"""Durable billing event inbox (BILL-005, BILL-007, BILL-055, BILL-056)."""

from __future__ import annotations

import hashlib
import json
import logging
from datetime import UTC, datetime
from typing import Any

logger = logging.getLogger("BLACKDARK.Billing.Inbox")

PROCESSING_PENDING = "pending"
PROCESSING_PROCESSING = "processing"
PROCESSING_SUCCEEDED = "succeeded"
PROCESSING_FAILED = "failed"
PROCESSING_DLQ = "dlq"

MAX_ATTEMPTS = 5


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def payload_hash(payload: dict[str, Any] | str) -> str:
    raw = payload if isinstance(payload, str) else json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode()).hexdigest()


async def persist_inbox_event(
    *,
    provider: str,
    stripe_event_id: str,
    event_type: str,
    object_id: str | None = None,
    stripe_created_at: int | None = None,
    payload: dict[str, Any] | None = None,
) -> tuple[int, bool]:
    """Persist before process. Returns (inbox_id, is_new)."""
    from database import get_connection

    provider = provider.strip().lower()
    event_id = stripe_event_id.strip()
    if not provider or not event_id:
        raise ValueError("provider and event_id required")
    ph = payload_hash(payload or {"id": event_id, "type": event_type})
    now = _utcnow_iso()
    async with get_connection() as db:
        existing = await (
            await db.execute(
                "SELECT id FROM billing_event_inbox WHERE provider = ? AND stripe_event_id = ?",
                (provider, event_id),
            )
        ).fetchone()
        if existing:
            return int(existing["id"]), False
        cursor = await db.execute(
            """
            INSERT INTO billing_event_inbox (
                provider, stripe_event_id, event_type, object_id,
                stripe_created_at, received_at, payload_hash,
                processing_status, attempt_count, payload_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
            """,
            (
                provider,
                event_id,
                event_type[:120],
                object_id,
                stripe_created_at,
                now,
                ph,
                PROCESSING_PENDING,
                json.dumps(payload or {}, separators=(",", ":"), default=str)[:65536],
            ),
        )
        return int(cursor.lastrowid or 0), True


async def claim_inbox_for_processing(inbox_id: int) -> bool:
    from database import get_connection

    now = _utcnow_iso()
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT processing_status, attempt_count FROM billing_event_inbox WHERE id = ?",
                (int(inbox_id),),
            )
        ).fetchone()
        if not row:
            return False
        if row["processing_status"] in {PROCESSING_SUCCEEDED, PROCESSING_DLQ}:
            return False
        await db.execute(
            """
            UPDATE billing_event_inbox
            SET processing_status = ?, attempt_count = attempt_count + 1,
                last_attempt_at = ?
            WHERE id = ? AND processing_status IN (?, ?)
            """,
            (PROCESSING_PROCESSING, now, int(inbox_id), PROCESSING_PENDING, PROCESSING_FAILED),
        )
        return True


async def mark_inbox_succeeded(inbox_id: int) -> None:
    from database import get_connection

    await _update_inbox(inbox_id, status=PROCESSING_SUCCEEDED, processed_at=_utcnow_iso())


async def mark_inbox_failed(inbox_id: int, error: str) -> None:
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT attempt_count FROM billing_event_inbox WHERE id = ?",
                (int(inbox_id),),
            )
        ).fetchone()
        attempts = int(row["attempt_count"]) if row else 0
        status = PROCESSING_DLQ if attempts >= MAX_ATTEMPTS else PROCESSING_FAILED
        await db.execute(
            """
            UPDATE billing_event_inbox
            SET processing_status = ?, last_error = ?, last_attempt_at = ?
            WHERE id = ?
            """,
            (status, error[:2000], _utcnow_iso(), int(inbox_id)),
        )
        if status == PROCESSING_DLQ:
            await db.execute(
                """
                INSERT INTO billing_dlq (
                    inbox_id, stripe_event_id, reason, attempts, moved_at, replay_status
                ) SELECT id, stripe_event_id, ?, attempt_count, ?, 'pending'
                FROM billing_event_inbox WHERE id = ?
                """,
                (error[:2000], _utcnow_iso(), int(inbox_id)),
            )


async def _update_inbox(inbox_id: int, *, status: str, processed_at: str | None = None) -> None:
    from database import get_connection

    async with get_connection() as db:
        await db.execute(
            """
            UPDATE billing_event_inbox
            SET processing_status = ?, processed_at = COALESCE(?, processed_at)
            WHERE id = ?
            """,
            (status, processed_at, int(inbox_id)),
        )


async def list_pending_inbox(*, limit: int = 50) -> list[dict[str, Any]]:
    from database import get_connection

    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT * FROM billing_event_inbox
                WHERE processing_status IN (?, ?)
                ORDER BY received_at ASC
                LIMIT ?
                """,
                (PROCESSING_PENDING, PROCESSING_FAILED, int(limit)),
            )
        ).fetchall()
    return [dict(r) for r in rows]


async def replay_dlq_entry(dlq_id: int, *, actor: str) -> dict[str, Any]:
    """Permission-controlled idempotent replay (BILL-056)."""
    from billing.audit_ledger import record_audit
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute("SELECT * FROM billing_dlq WHERE id = ?", (int(dlq_id),))
        ).fetchone()
        if not row:
            return {"ok": False, "reason": "not_found"}
        if row["replay_status"] == "succeeded":
            return {"ok": True, "duplicate": True}
        inbox = await (
            await db.execute(
                "SELECT * FROM billing_event_inbox WHERE id = ?",
                (int(row["inbox_id"]),),
            )
        ).fetchone()
        if not inbox:
            return {"ok": False, "reason": "inbox_missing"}
        await db.execute(
            """
            UPDATE billing_event_inbox
            SET processing_status = ?, last_error = NULL
            WHERE id = ?
            """,
            (PROCESSING_PENDING, int(inbox["id"])),
        )
        await db.execute(
            "UPDATE billing_dlq SET replay_status = 'requeued', replayed_at = ? WHERE id = ?",
            (_utcnow_iso(), int(dlq_id)),
        )
    await record_audit(action="INBOX_REPLAY", actor=actor, reason=f"dlq_id={dlq_id}")
    return {"ok": True, "inbox_id": int(inbox["id"])}


async def inbox_metrics() -> dict[str, int]:
    from database import get_connection

    async with get_connection() as db:
        pending = await (
            await db.execute(
                "SELECT COUNT(*) AS c FROM billing_event_inbox WHERE processing_status = ?",
                (PROCESSING_PENDING,),
            )
        ).fetchone()
        failed = await (
            await db.execute(
                "SELECT COUNT(*) AS c FROM billing_event_inbox WHERE processing_status = ?",
                (PROCESSING_FAILED,),
            )
        ).fetchone()
        dlq = await (
            await db.execute("SELECT COUNT(*) AS c FROM billing_dlq WHERE replay_status != 'succeeded'")
        ).fetchone()
    return {
        "inbox_pending": int(pending["c"] if pending else 0),
        "inbox_failed": int(failed["c"] if failed else 0),
        "dlq_size": int(dlq["c"] if dlq else 0),
    }
