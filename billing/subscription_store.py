"""Subscription account persistence (SSOT)."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

from billing.plan_registry import normalize_plan

logger = logging.getLogger("BLACKDARK.Billing.Store")


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _row_to_dict(row: Any) -> dict[str, Any]:
    data = dict(row)
    data["cancel_at_period_end"] = bool(int(data.get("cancel_at_period_end") or 0))
    data["auto_renew_enabled"] = bool(int(data.get("auto_renew_enabled") or 0))
    return data


async def ensure_subscription_account(
    user_id: int,
    email: str,
    *,
    plan: str = "free",
) -> dict[str, Any]:
    from database import get_connection

    email = email.strip().lower()
    plan = normalize_plan(plan)
    now = _utcnow_iso()
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT * FROM subscription_accounts WHERE user_id = ?",
                (int(user_id),),
            )
        ).fetchone()
        if row:
            return _row_to_dict(row)
        period_end = (_utcnow() + timedelta(days=3650)).isoformat()
        await db.execute(
            """
            INSERT INTO subscription_accounts (
                user_id, email, plan, subscription_status, payment_status,
                start_date, current_period_start, current_period_end, renewal_date,
                cancel_at_period_end, auto_renew_enabled, entitlements_version,
                created_at, updated_at
            ) VALUES (?, ?, ?, 'active', 'none', ?, ?, ?, ?, 0, 0, 1, ?, ?)
            """,
            (
                int(user_id),
                email,
                plan,
                now,
                now,
                period_end,
                period_end,
                now,
                now,
            ),
        )
        row = await (
            await db.execute(
                "SELECT * FROM subscription_accounts WHERE user_id = ?",
                (int(user_id),),
            )
        ).fetchone()
    return _row_to_dict(row)


async def get_by_user_id(user_id: int) -> dict[str, Any] | None:
    from database import get_connection

    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT * FROM subscription_accounts WHERE user_id = ?",
                (int(user_id),),
            )
        ).fetchone()
    return _row_to_dict(row) if row else None


async def get_by_email(email: str) -> dict[str, Any] | None:
    from database import fetch_user_by_email, get_connection

    email = email.strip().lower()
    user = await fetch_user_by_email(email)
    if user:
        sub = await get_by_user_id(int(user["id"]))
        if sub:
            return sub
    async with get_connection() as db:
        row = await (
            await db.execute(
                "SELECT * FROM subscription_accounts WHERE email = ? ORDER BY id DESC LIMIT 1",
                (email,),
            )
        ).fetchone()
    return _row_to_dict(row) if row else None


async def get_by_provider_subscription_id(provider_sub_id: str) -> dict[str, Any] | None:
    from database import get_connection

    if not provider_sub_id:
        return None
    async with get_connection() as db:
        row = await (
            await db.execute(
                """
                SELECT * FROM subscription_accounts
                WHERE provider_subscription_id = ?
                ORDER BY id DESC LIMIT 1
                """,
                (provider_sub_id,),
            )
        ).fetchone()
    return _row_to_dict(row) if row else None


async def update_subscription_account(
    user_id: int,
    *,
    plan: str | None = None,
    subscription_status: str | None = None,
    payment_status: str | None = None,
    current_period_start: str | None = None,
    current_period_end: str | None = None,
    renewal_date: str | None = None,
    cancel_at_period_end: bool | None = None,
    auto_renew_enabled: bool | None = None,
    auto_renew_consent_at: str | None = None,
    provider: str | None = None,
    provider_subscription_id: str | None = None,
    provider_customer_id: str | None = None,
    pending_plan: str | None = None,
    entitlements_version: int | None = None,
    grace_period_end: str | None = None,
    trial_ends_at: str | None = None,
    start_date: str | None = None,
    bump_entitlements: bool = False,
) -> dict[str, Any]:
    from database import get_connection

    updates: list[str] = ["updated_at = ?"]
    params: list[Any] = [_utcnow_iso()]
    if plan is not None:
        updates.append("plan = ?")
        params.append(normalize_plan(plan))
    if subscription_status is not None:
        updates.append("subscription_status = ?")
        params.append(subscription_status)
    if payment_status is not None:
        updates.append("payment_status = ?")
        params.append(payment_status)
    if current_period_start is not None:
        updates.append("current_period_start = ?")
        params.append(current_period_start)
    if current_period_end is not None:
        updates.append("current_period_end = ?")
        params.append(current_period_end)
    if renewal_date is not None:
        updates.append("renewal_date = ?")
        params.append(renewal_date)
    if cancel_at_period_end is not None:
        updates.append("cancel_at_period_end = ?")
        params.append(1 if cancel_at_period_end else 0)
    if auto_renew_enabled is not None:
        updates.append("auto_renew_enabled = ?")
        params.append(1 if auto_renew_enabled else 0)
    if auto_renew_consent_at is not None:
        updates.append("auto_renew_consent_at = ?")
        params.append(auto_renew_consent_at)
    if provider is not None:
        updates.append("provider = ?")
        params.append(provider)
    if provider_subscription_id is not None:
        updates.append("provider_subscription_id = ?")
        params.append(provider_subscription_id)
    if provider_customer_id is not None:
        updates.append("provider_customer_id = ?")
        params.append(provider_customer_id)
    if pending_plan is not None:
        updates.append("pending_plan = ?")
        params.append(normalize_plan(pending_plan) if pending_plan else None)
    if grace_period_end is not None:
        updates.append("grace_period_end = ?")
        params.append(grace_period_end)
    if trial_ends_at is not None:
        updates.append("trial_ends_at = ?")
        params.append(trial_ends_at)
    if start_date is not None:
        updates.append("start_date = ?")
        params.append(start_date)
    if bump_entitlements:
        updates.append("entitlements_version = entitlements_version + 1")
    elif entitlements_version is not None:
        updates.append("entitlements_version = ?")
        params.append(int(entitlements_version))

    params.append(int(user_id))
    async with get_connection() as db:
        await db.execute(
            f"UPDATE subscription_accounts SET {', '.join(updates)} WHERE user_id = ?",
            params,
        )
        row = await (
            await db.execute(
                "SELECT * FROM subscription_accounts WHERE user_id = ?",
                (int(user_id),),
            )
        ).fetchone()
    return _row_to_dict(row)


async def list_expired_candidates(now_iso: str | None = None) -> list[dict[str, Any]]:
    from database import get_connection

    now = now_iso or _utcnow_iso()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT * FROM subscription_accounts
                WHERE plan != 'free'
                  AND subscription_status IN ('active', 'trialing', 'past_due', 'canceled')
                  AND current_period_end IS NOT NULL
                  AND current_period_end <= ?
                  AND (grace_period_end IS NULL OR grace_period_end <= ?)
                """,
                (now, now),
            )
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


async def list_renewal_warning_candidates(
    *,
    warning_days: int = 5,
    now_iso: str | None = None,
) -> list[dict[str, Any]]:
    """Paid subscriptions expiring within warning_days (not yet expired)."""
    from database import get_connection

    now = datetime.fromisoformat(now_iso) if now_iso else datetime.now(UTC)
    if now.tzinfo is None:
        now = now.replace(tzinfo=UTC)
    horizon = (now + timedelta(days=int(warning_days))).isoformat()
    now_s = now.isoformat()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT * FROM subscription_accounts
                WHERE plan != 'free'
                  AND subscription_status IN ('active', 'trialing', 'canceled')
                  AND current_period_end IS NOT NULL
                  AND current_period_end > ?
                  AND current_period_end <= ?
                """,
                (now_s, horizon),
            )
        ).fetchall()
    return [_row_to_dict(r) for r in rows]


async def list_pending_downgrades(now_iso: str | None = None) -> list[dict[str, Any]]:
    from database import get_connection

    now = now_iso or _utcnow_iso()
    async with get_connection() as db:
        rows = await (
            await db.execute(
                """
                SELECT * FROM subscription_accounts
                WHERE pending_plan IS NOT NULL
                  AND current_period_end IS NOT NULL
                  AND current_period_end <= ?
                """,
                (now,),
            )
        ).fetchall()
    return [_row_to_dict(r) for r in rows]
