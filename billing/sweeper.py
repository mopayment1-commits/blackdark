"""Background sweeper — expire subscriptions and apply pending downgrades."""

from __future__ import annotations

import asyncio
import logging

from billing.subscription_engine import expire_subscription_account
from billing.subscription_store import list_expired_candidates, list_pending_downgrades, update_subscription_account

logger = logging.getLogger("BLACKDARK.Billing.Sweeper")

_sweeper_task: asyncio.Task | None = None


async def run_billing_sweep() -> dict[str, int]:
    expired = 0
    downgraded = 0
    for sub in await list_expired_candidates():
        uid = int(sub["user_id"])
        if sub.get("cancel_at_period_end") or not sub.get("auto_renew_enabled"):
            await expire_subscription_account(uid, reason="period_ended_no_renewal")
            expired += 1
        elif sub.get("subscription_status") == "past_due":
            await expire_subscription_account(uid, reason="grace_expired")
            expired += 1
    for sub in await list_pending_downgrades():
        uid = int(sub["user_id"])
        target = str(sub.get("pending_plan") or "free")
        await update_subscription_account(
            uid,
            plan=target,
            pending_plan=None,
            bump_entitlements=True,
        )
        downgraded += 1
    return {"expired": expired, "downgraded": downgraded}


async def _sweeper_loop(interval_sec: int = 900) -> None:
    while True:
        try:
            stats = await run_billing_sweep()
            if stats["expired"] or stats["downgraded"]:
                logger.info("billing_sweep | %s", stats)
        except Exception:
            logger.exception("billing_sweep failed")
        await asyncio.sleep(interval_sec)


def start_billing_sweeper(interval_sec: int = 900) -> asyncio.Task | None:
    global _sweeper_task
    if _sweeper_task is not None and not _sweeper_task.done():
        return _sweeper_task
    _sweeper_task = asyncio.create_task(_sweeper_loop(interval_sec), name="billing-sweeper")
    logger.info("Billing sweeper started (interval=%ss)", interval_sec)
    return _sweeper_task
