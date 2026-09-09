"""Async event processor — inbox → out-of-order guard → engine (BILL-007)."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from billing.event_inbox import (
    claim_inbox_for_processing,
    mark_inbox_failed,
    mark_inbox_succeeded,
    persist_inbox_event,
)
from billing.out_of_order_guard import should_apply_event
from billing.webhook_processor import process_stripe_event

logger = logging.getLogger("BLACKDARK.Billing.Processor")

_processor_task: asyncio.Task | None = None


async def enqueue_stripe_event(event: dict[str, Any]) -> dict[str, Any]:
    """Verify path: persist → ACK quickly → process async."""
    event_id = str(event.get("id") or "").strip()
    event_type = str(event.get("type") or "")
    data_object = (event.get("data") or {}).get("object") or {}
    object_id = str(data_object.get("id") or data_object.get("subscription") or "")
    created = event.get("created")
    inbox_id, is_new = await persist_inbox_event(
        provider="stripe",
        stripe_event_id=event_id,
        event_type=event_type,
        object_id=object_id or None,
        stripe_created_at=int(created) if created else None,
        payload=event,
    )
    if not is_new:
        return {"enqueued": False, "duplicate": True, "inbox_id": inbox_id}
    asyncio.create_task(_process_inbox_entry(inbox_id, event), name=f"billing-inbox-{inbox_id}")
    return {"enqueued": True, "inbox_id": inbox_id}


async def _process_inbox_entry(inbox_id: int, event: dict[str, Any]) -> None:
    if not await claim_inbox_for_processing(inbox_id):
        return
    event_id = str(event.get("id") or "")
    data_object = (event.get("data") or {}).get("object") or {}
    object_id = str(data_object.get("id") or data_object.get("subscription") or "")
    created = event.get("created")
    try:
        apply, reason = await should_apply_event(
            object_id=object_id or event_id,
            event_created_at=int(created) if created else None,
            event_id=event_id,
        )
        if not apply:
            await mark_inbox_succeeded(inbox_id)
            logger.info("inbox_skip_out_of_order | inbox_id=%s reason=%s", inbox_id, reason)
            return
        result = await process_stripe_event(event)
        if result.get("handled") is False and result.get("reason") not in {"duplicate_ignored"}:
            await mark_inbox_failed(inbox_id, json.dumps(result)[:500])
        else:
            await mark_inbox_succeeded(inbox_id)
    except Exception as exc:
        logger.exception("inbox_process_failed | inbox_id=%s", inbox_id)
        await mark_inbox_failed(inbox_id, str(exc))


async def process_pending_inbox(*, limit: int = 20) -> int:
    from billing.event_inbox import list_pending_inbox

    processed = 0
    for row in await list_pending_inbox(limit=limit):
        payload = json.loads(row.get("payload_json") or "{}")
        if payload:
            await _process_inbox_entry(int(row["id"]), payload)
            processed += 1
    return processed
