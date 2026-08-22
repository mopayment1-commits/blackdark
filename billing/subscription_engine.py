"""
BLACKDARK — Subscription lifecycle state machine (SSOT).

Payment status ≠ subscription status ≠ entitlement status.
All webhook-driven transitions are idempotent and audit-logged.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Any

import config

from billing.audit_ledger import record_audit
from billing.plan_registry import PAID_TRIAL_DAYS, normalize_plan, plan_rank
from billing.subscription_store import (
    ensure_subscription_account,
    get_by_email,
    get_by_provider_subscription_id,
    get_by_user_id,
    update_subscription_account,
)

logger = logging.getLogger("BLACKDARK.Billing.Engine")

ACTIVE_SUB_STATUSES = frozenset({"active", "trialing", "past_due"})
REVOKED_PAYMENT_STATUSES = frozenset({"refunded", "disputed", "chargeback"})


def _utcnow() -> datetime:
    return datetime.now(UTC)


def _utcnow_iso() -> str:
    return _utcnow().isoformat()


def _grace_days() -> int:
    return int(getattr(config, "BILLING_RENEWAL_GRACE_DAYS", 3))


def _period_from_stripe(obj: dict[str, Any]) -> tuple[str | None, str | None]:
    start = obj.get("current_period_start")
    end = obj.get("current_period_end")
    if start and end:
        try:
            return (
                datetime.fromtimestamp(int(start), tz=UTC).isoformat(),
                datetime.fromtimestamp(int(end), tz=UTC).isoformat(),
            )
        except (TypeError, ValueError):
            pass
    now = _utcnow()
    return now.isoformat(), (now + timedelta(days=30)).isoformat()


async def _resolve_user(email: str, user_id: int | None = None) -> dict[str, Any] | None:
    from database import fetch_user_by_email

    if user_id:
        from database import fetch_user_by_id

        user = await fetch_user_by_id(int(user_id))
        if user:
            return user
    return await fetch_user_by_email(email.strip().lower())


async def _record_payment_event(
    *,
    user_id: int | None,
    email: str,
    provider: str,
    provider_event_id: str,
    event_type: str,
    status: str,
    amount_cents: int | None = None,
    plan: str | None = None,
    provider_invoice_id: str | None = None,
    raw_event_type: str | None = None,
) -> tuple[int, bool]:
    """Return (payment_event_id, is_new)."""
    from database import get_connection

    idempotency_key = f"{provider}:{event_type}:{provider_event_id}"
    async with get_connection() as db:
        existing = await (
            await db.execute(
                "SELECT id FROM billing_payment_events WHERE idempotency_key = ?",
                (idempotency_key,),
            )
        ).fetchone()
        if existing:
            return int(existing["id"]), False
        cursor = await db.execute(
            """
            INSERT INTO billing_payment_events (
                user_id, email, provider, provider_event_id, provider_invoice_id,
                event_type, amount_cents, currency, status, plan, idempotency_key,
                raw_event_type, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 'usd', ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                email.strip().lower(),
                provider,
                provider_event_id,
                provider_invoice_id,
                event_type,
                amount_cents,
                status,
                normalize_plan(plan) if plan else None,
                idempotency_key,
                raw_event_type,
                _utcnow_iso(),
            ),
        )
        return int(cursor.lastrowid or 0), True


async def _sync_legacy_subscription(
    email: str,
    plan: str,
    provider_sub_id: str | None,
    *,
    status: str = "active",
    trial_ends_at: str | None = None,
) -> None:
    """Keep legacy subscriptions table in sync for backward-compatible reads."""
    from database import activate_paid_subscription, upsert_subscription_by_stripe_id

    canonical = normalize_plan(plan)
    if provider_sub_id and status == "active":
        await activate_paid_subscription(email, canonical, provider_sub_id)
        return
    if provider_sub_id:
        await upsert_subscription_by_stripe_id(
            provider_sub_id,
            tier=canonical,
            status=status,
            email=email,
        )


async def activate_checkout(
    *,
    email: str,
    plan: str,
    provider: str,
    provider_subscription_id: str,
    provider_customer_id: str | None = None,
    user_id: int | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    trial_ends_at: str | None = None,
    auto_renew_consent: bool = True,
    provider_event_id: str,
    amount_cents: int | None = None,
) -> dict[str, Any]:
    canonical = normalize_plan(plan)
    user = await _resolve_user(email, user_id)
    if not user:
        from database import activate_paid_subscription

        pay_id, is_new = await _record_payment_event(
            user_id=None,
            email=email,
            provider=provider,
            provider_event_id=provider_event_id,
            event_type="checkout_completed",
            status="succeeded",
            amount_cents=amount_cents,
            plan=canonical,
        )
        if not is_new:
            return {"duplicate": True, "subscription": None, "legacy_only": True}
        await activate_paid_subscription(
            email,
            canonical,
            provider_subscription_id,
            stripe_customer_id=provider_customer_id,
        )
        await record_audit(
            action="SUBSCRIPTION_CREATED",
            actor=f"webhook:{provider}",
            email=email,
            new_plan=canonical,
            new_status="active",
            amount_cents=amount_cents,
            payment_event_id=pay_id,
            provider_subscription_id=provider_subscription_id,
            reason="checkout_completed_legacy_email_only",
        )
        return {"duplicate": False, "subscription": None, "legacy_only": True}

    uid = int(user["id"])
    sub = await ensure_subscription_account(uid, email, plan=canonical)
    old_plan = sub.get("plan")
    old_status = sub.get("subscription_status")
    now = _utcnow_iso()
    p_start = period_start or now
    p_end = period_end or (_utcnow() + timedelta(days=30)).isoformat()
    sub_status = "trialing" if trial_ends_at else "active"
    pay_status = "current" if sub_status == "active" else "trialing"

    pay_id, is_new = await _record_payment_event(
        user_id=uid,
        email=email,
        provider=provider,
        provider_event_id=provider_event_id,
        event_type="checkout_completed",
        status="succeeded",
        amount_cents=amount_cents,
        plan=canonical,
    )
    if not is_new:
        current = await get_by_user_id(uid)
        return {"duplicate": True, "subscription": current}

    updated = await update_subscription_account(
        uid,
        plan=canonical,
        subscription_status=sub_status,
        payment_status=pay_status,
        current_period_start=p_start,
        current_period_end=p_end,
        renewal_date=p_end,
        cancel_at_period_end=False,
        auto_renew_enabled=auto_renew_consent,
        auto_renew_consent_at=now if auto_renew_consent else None,
        provider=provider,
        provider_subscription_id=provider_subscription_id,
        provider_customer_id=provider_customer_id,
        pending_plan=None,
        grace_period_end=None,
        trial_ends_at=trial_ends_at,
        bump_entitlements=True,
    )
    if provider_customer_id:
        from database import get_connection

        async with get_connection() as db:
            await db.execute(
                "UPDATE users SET stripe_customer_id = ? WHERE id = ?",
                (provider_customer_id, uid),
            )
    await _sync_legacy_subscription(
        email,
        canonical,
        provider_subscription_id,
        status="trial" if sub_status == "trialing" else "active",
        trial_ends_at=trial_ends_at,
    )
    await record_audit(
        action="SUBSCRIPTION_CREATED",
        actor=f"webhook:{provider}",
        user_id=uid,
        email=email,
        old_plan=old_plan,
        new_plan=canonical,
        old_status=old_status,
        new_status=sub_status,
        amount_cents=amount_cents,
        payment_event_id=pay_id,
        provider_subscription_id=provider_subscription_id,
        reason="checkout_completed",
        entitlements_version=updated.get("entitlements_version"),
    )
    return {"duplicate": False, "subscription": updated}


async def renew_subscription(
    *,
    provider_subscription_id: str,
    provider: str,
    provider_event_id: str,
    provider_invoice_id: str | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
    amount_cents: int | None = None,
) -> dict[str, Any]:
    sub = await get_by_provider_subscription_id(provider_subscription_id)
    if not sub:
        return {"handled": False, "reason": "subscription_not_found"}
    uid = int(sub["user_id"])
    pay_id, is_new = await _record_payment_event(
        user_id=uid,
        email=str(sub["email"]),
        provider=provider,
        provider_event_id=provider_event_id,
        provider_invoice_id=provider_invoice_id,
        event_type="renewal",
        status="succeeded",
        amount_cents=amount_cents,
        plan=sub.get("plan"),
        raw_event_type="invoice.paid",
    )
    if not is_new:
        return {"handled": True, "duplicate": True, "subscription": sub}

    now = _utcnow_iso()
    p_start = period_start or now
    p_end = period_end or (_utcnow() + timedelta(days=30)).isoformat()
    updated = await update_subscription_account(
        uid,
        subscription_status="active",
        payment_status="current",
        current_period_start=p_start,
        current_period_end=p_end,
        renewal_date=p_end,
        grace_period_end=None,
        bump_entitlements=True,
    )
    await _sync_legacy_subscription(
        str(sub["email"]),
        str(sub["plan"]),
        provider_subscription_id,
        status="active",
    )
    await record_audit(
        action="RENEWAL_SUCCESS",
        actor=f"webhook:{provider}",
        user_id=uid,
        email=str(sub["email"]),
        old_plan=sub.get("plan"),
        new_plan=sub.get("plan"),
        old_status=sub.get("subscription_status"),
        new_status="active",
        amount_cents=amount_cents,
        payment_event_id=pay_id,
        provider_subscription_id=provider_subscription_id,
        reason="invoice.paid",
        entitlements_version=updated.get("entitlements_version"),
    )
    return {"handled": True, "subscription": updated}


async def payment_failed(
    *,
    provider_subscription_id: str,
    provider: str,
    provider_event_id: str,
) -> dict[str, Any]:
    sub = await get_by_provider_subscription_id(provider_subscription_id)
    if not sub:
        return {"handled": False, "reason": "subscription_not_found"}
    uid = int(sub["user_id"])
    pay_id, is_new = await _record_payment_event(
        user_id=uid,
        email=str(sub["email"]),
        provider=provider,
        provider_event_id=provider_event_id,
        event_type="payment_failed",
        status="failed",
        plan=sub.get("plan"),
    )
    if not is_new:
        return {"handled": True, "duplicate": True}
    grace_end = (_utcnow() + timedelta(days=_grace_days())).isoformat()
    updated = await update_subscription_account(
        uid,
        subscription_status="past_due",
        payment_status="failed",
        grace_period_end=grace_end,
        bump_entitlements=False,
    )
    await _sync_legacy_subscription(
        str(sub["email"]),
        str(sub["plan"]),
        provider_subscription_id,
        status="past_due",
    )
    await record_audit(
        action="RENEWAL_FAILED",
        actor=f"webhook:{provider}",
        user_id=uid,
        email=str(sub["email"]),
        old_status=sub.get("subscription_status"),
        new_status="past_due",
        payment_event_id=pay_id,
        provider_subscription_id=provider_subscription_id,
        reason=f"payment_failed grace_until={grace_end}",
    )
    return {"handled": True, "subscription": updated, "grace_period_end": grace_end}


async def schedule_cancel_at_period_end(
    user_id: int,
    *,
    actor: str = "user",
) -> dict[str, Any]:
    sub = await get_by_user_id(user_id)
    if not sub:
        raise ValueError("No subscription account")
    updated = await update_subscription_account(
        user_id,
        cancel_at_period_end=True,
        auto_renew_enabled=False,
        subscription_status="canceled",
        bump_entitlements=False,
    )
    await record_audit(
        action="CANCEL_SCHEDULED",
        actor=actor,
        user_id=user_id,
        email=str(sub.get("email")),
        old_plan=sub.get("plan"),
        new_plan=sub.get("plan"),
        old_status=sub.get("subscription_status"),
        new_status="canceled",
        provider_subscription_id=sub.get("provider_subscription_id"),
        reason="cancel_at_period_end",
        entitlements_version=updated.get("entitlements_version"),
    )
    return updated


async def schedule_downgrade(user_id: int, target_plan: str, *, actor: str = "user") -> dict[str, Any]:
    sub = await get_by_user_id(user_id)
    if not sub:
        raise ValueError("No subscription account")
    target = normalize_plan(target_plan)
    if plan_rank(target) >= plan_rank(str(sub.get("plan"))):
        raise ValueError("Target plan must be lower than current plan")
    updated = await update_subscription_account(
        user_id,
        pending_plan=target,
        bump_entitlements=False,
    )
    await record_audit(
        action="DOWNGRADE_SCHEDULED",
        actor=actor,
        user_id=user_id,
        email=str(sub.get("email")),
        old_plan=sub.get("plan"),
        new_plan=target,
        provider_subscription_id=sub.get("provider_subscription_id"),
        reason="effective_at_period_end",
        entitlements_version=updated.get("entitlements_version"),
    )
    return updated


async def apply_upgrade(
    user_id: int,
    target_plan: str,
    *,
    provider: str,
    provider_event_id: str,
    amount_cents: int | None = None,
    period_start: str | None = None,
    period_end: str | None = None,
) -> dict[str, Any]:
    """Only after confirmed payment."""
    sub = await get_by_user_id(user_id)
    if not sub:
        raise ValueError("No subscription account")
    target = normalize_plan(target_plan)
    if plan_rank(target) <= plan_rank(str(sub.get("plan"))):
        raise ValueError("Target plan must be higher than current plan")
    pay_id, is_new = await _record_payment_event(
        user_id=user_id,
        email=str(sub["email"]),
        provider=provider,
        provider_event_id=provider_event_id,
        event_type="upgrade",
        status="succeeded",
        amount_cents=amount_cents,
        plan=target,
    )
    if not is_new:
        return {"duplicate": True, "subscription": sub}
    now = _utcnow_iso()
    updated = await update_subscription_account(
        user_id,
        plan=target,
        pending_plan=None,
        subscription_status="active",
        payment_status="current",
        current_period_start=period_start or now,
        current_period_end=period_end or sub.get("current_period_end"),
        renewal_date=period_end or sub.get("current_period_end"),
        grace_period_end=None,
        bump_entitlements=True,
    )
    await _sync_legacy_subscription(
        str(sub["email"]),
        target,
        str(sub.get("provider_subscription_id") or ""),
        status="active",
    )
    await record_audit(
        action="UPGRADE",
        actor=f"webhook:{provider}",
        user_id=user_id,
        email=str(sub["email"]),
        old_plan=sub.get("plan"),
        new_plan=target,
        amount_cents=amount_cents,
        payment_event_id=pay_id,
        provider_subscription_id=sub.get("provider_subscription_id"),
        reason="upgrade_payment_confirmed",
        entitlements_version=updated.get("entitlements_version"),
    )
    return {"subscription": updated}


async def revoke_for_financial_reversal(
    *,
    provider_subscription_id: str | None = None,
    user_id: int | None = None,
    provider: str,
    provider_event_id: str,
    reason: str,
    payment_status: str = "refunded",
) -> dict[str, Any]:
    sub = None
    if provider_subscription_id:
        sub = await get_by_provider_subscription_id(provider_subscription_id)
    elif user_id:
        sub = await get_by_user_id(user_id)
    if not sub:
        return {"handled": False, "reason": "subscription_not_found"}
    uid = int(sub["user_id"])
    pay_id, is_new = await _record_payment_event(
        user_id=uid,
        email=str(sub["email"]),
        provider=provider,
        provider_event_id=provider_event_id,
        event_type=reason,
        status=payment_status,
        plan=sub.get("plan"),
    )
    if not is_new:
        return {"handled": True, "duplicate": True}
    updated = await update_subscription_account(
        uid,
        plan="free",
        subscription_status="expired",
        payment_status=payment_status,
        pending_plan=None,
        grace_period_end=None,
        bump_entitlements=True,
    )
    if sub.get("provider_subscription_id"):
        from database import cancel_subscription_by_stripe_id

        await cancel_subscription_by_stripe_id(str(sub["provider_subscription_id"]))
    await record_audit(
        action="ENTITLEMENT_REVOKED_FINANCIAL",
        actor=f"webhook:{provider}",
        user_id=uid,
        email=str(sub["email"]),
        old_plan=sub.get("plan"),
        new_plan="free",
        old_status=sub.get("subscription_status"),
        new_status="expired",
        payment_event_id=pay_id,
        provider_subscription_id=sub.get("provider_subscription_id"),
        reason=reason,
        entitlements_version=updated.get("entitlements_version"),
    )
    return {"handled": True, "subscription": updated}


async def expire_subscription_account(user_id: int, *, reason: str = "period_ended") -> dict[str, Any]:
    sub = await get_by_user_id(user_id)
    if not sub:
        return {"handled": False}
    new_plan = normalize_plan(str(sub.get("pending_plan") or "free"))
    updated = await update_subscription_account(
        user_id,
        plan=new_plan,
        subscription_status="expired" if new_plan == "free" else "active",
        payment_status="none" if new_plan == "free" else sub.get("payment_status"),
        pending_plan=None,
        cancel_at_period_end=False,
        auto_renew_enabled=False,
        grace_period_end=None,
        bump_entitlements=True,
    )
    await record_audit(
        action="SUBSCRIPTION_EXPIRED",
        actor="system:sweeper",
        user_id=user_id,
        email=str(sub.get("email")),
        old_plan=sub.get("plan"),
        new_plan=new_plan,
        old_status=sub.get("subscription_status"),
        new_status=updated.get("subscription_status"),
        provider_subscription_id=sub.get("provider_subscription_id"),
        reason=reason,
        entitlements_version=updated.get("entitlements_version"),
    )
    return {"handled": True, "subscription": updated}


async def sync_from_stripe_subscription(
    data_object: dict[str, Any],
    *,
    provider: str = "stripe",
    provider_event_id: str,
) -> dict[str, Any]:
    provider_sub_id = str(data_object.get("id") or "")
    sub = await get_by_provider_subscription_id(provider_sub_id)
    if not sub:
        return {"handled": False, "reason": "not_tracked"}
    uid = int(sub["user_id"])
    p_start, p_end = _period_from_stripe(data_object)
    stripe_status = str(data_object.get("status") or "active")
    cancel_at_end = bool(data_object.get("cancel_at_period_end"))
    meta_tier = (data_object.get("metadata") or {}).get("tier")
    plan = normalize_plan(meta_tier) if meta_tier else str(sub.get("plan"))

    sub_status = {
        "active": "active",
        "trialing": "trialing",
        "past_due": "past_due",
        "canceled": "canceled",
        "unpaid": "past_due",
        "incomplete": "past_due",
        "incomplete_expired": "expired",
    }.get(stripe_status, "active")

    updated = await update_subscription_account(
        uid,
        plan=plan,
        subscription_status=sub_status,
        current_period_start=p_start,
        current_period_end=p_end,
        renewal_date=p_end,
        cancel_at_period_end=cancel_at_end,
        auto_renew_enabled=not cancel_at_end,
        bump_entitlements=False,
    )
    await record_audit(
        action="SUBSCRIPTION_SYNCED",
        actor=f"webhook:{provider}",
        user_id=uid,
        email=str(sub.get("email")),
        new_plan=plan,
        new_status=sub_status,
        provider_subscription_id=provider_sub_id,
        reason=f"stripe_status={stripe_status}",
        entitlements_version=updated.get("entitlements_version"),
    )
    return {"handled": True, "subscription": updated}


def effective_plan(sub: dict[str, Any] | None, *, now: datetime | None = None) -> str:
    if not sub:
        return "free"
    now = now or _utcnow()
    plan = normalize_plan(str(sub.get("plan") or "free"))
    status = str(sub.get("subscription_status") or "")
    pay_status = str(sub.get("payment_status") or "")
    if pay_status in REVOKED_PAYMENT_STATUSES:
        return "free"
    if status == "expired":
        return normalize_plan(str(sub.get("pending_plan") or "free"))
    period_end = sub.get("current_period_end")
    grace_end = sub.get("grace_period_end")
    if period_end:
        try:
            end_dt = datetime.fromisoformat(str(period_end))
            if now > end_dt:
                if grace_end:
                    grace_dt = datetime.fromisoformat(str(grace_end))
                    if now > grace_dt:
                        return normalize_plan(str(sub.get("pending_plan") or "free"))
                elif status not in ACTIVE_SUB_STATUSES:
                    return normalize_plan(str(sub.get("pending_plan") or "free"))
        except ValueError:
            pass
    if status in {"trialing", "active", "past_due", "canceled"}:
        return plan
    return "free"


def entitlement_allowed(sub: dict[str, Any] | None, *, now: datetime | None = None) -> bool:
    if not sub:
        return False
    plan = effective_plan(sub, now=now)
    if plan == "free" and normalize_plan(str(sub.get("plan"))) == "free":
        return True
    status = str(sub.get("subscription_status") or "")
    pay_status = str(sub.get("payment_status") or "")
    if pay_status in REVOKED_PAYMENT_STATUSES:
        return False
    if status == "expired":
        return False
    now = now or _utcnow()
    period_end = sub.get("current_period_end")
    if period_end:
        try:
            end_dt = datetime.fromisoformat(str(period_end))
            if now <= end_dt:
                return status in ACTIVE_SUB_STATUSES | {"canceled"}
            if sub.get("grace_period_end"):
                grace_dt = datetime.fromisoformat(str(sub["grace_period_end"]))
                return now <= grace_dt and status == "past_due"
            return status == "canceled" and now <= end_dt
        except ValueError:
            return False
    return status in ACTIVE_SUB_STATUSES


async def resolve_entitlements_for_user(user_id: int) -> dict[str, Any]:
    sub = await get_by_user_id(user_id)
    if not sub:
        return {
            "plan": "free",
            "effective_plan": "free",
            "entitlement_allowed": True,
            "subscription_status": "active",
            "payment_status": "none",
            "entitlements_version": 1,
        }
    plan = effective_plan(sub)
    return {
        "plan": normalize_plan(str(sub.get("plan"))),
        "effective_plan": plan,
        "entitlement_allowed": entitlement_allowed(sub),
        "subscription_status": sub.get("subscription_status"),
        "payment_status": sub.get("payment_status"),
        "current_period_end": sub.get("current_period_end"),
        "cancel_at_period_end": sub.get("cancel_at_period_end"),
        "auto_renew_enabled": sub.get("auto_renew_enabled"),
        "pending_plan": sub.get("pending_plan"),
        "entitlements_version": sub.get("entitlements_version"),
        "grace_period_end": sub.get("grace_period_end"),
        "trial_ends_at": sub.get("trial_ends_at"),
    }


async def start_paid_trial(user_id: int, email: str, plan: str) -> dict[str, Any]:
    canonical = normalize_plan(plan)
    if canonical == "free":
        raise ValueError("Free plan has no trial")
    sub = await ensure_subscription_account(user_id, email, plan=canonical)
    now = _utcnow()
    trial_end = (now + timedelta(days=PAID_TRIAL_DAYS)).isoformat()
    updated = await update_subscription_account(
        user_id,
        plan=canonical,
        subscription_status="trialing",
        payment_status="trialing",
        current_period_start=now.isoformat(),
        current_period_end=trial_end,
        renewal_date=trial_end,
        trial_ends_at=trial_end,
        auto_renew_enabled=True,
        auto_renew_consent_at=now.isoformat(),
        bump_entitlements=True,
    )
    await _sync_legacy_subscription(email, canonical, None, status="trial", trial_ends_at=trial_end)
    await record_audit(
        action="TRIAL_STARTED",
        actor="system:signup",
        user_id=user_id,
        email=email,
        new_plan=canonical,
        new_status="trialing",
        reason=f"{PAID_TRIAL_DAYS}d_trial",
        entitlements_version=updated.get("entitlements_version"),
    )
    return updated
