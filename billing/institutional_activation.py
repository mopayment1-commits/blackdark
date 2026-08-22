"""Activate INSTITUTIONAL subscriptions from sales-led commerce (invoice / wire)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from billing.audit_ledger import record_audit
from billing.plan_registry import normalize_plan
from billing.subscription_engine import _record_payment_event
from billing.subscription_store import ensure_subscription_account, get_by_user_id, update_subscription_account

INSTITUTIONAL_MIN_USD = 999.0
DEFAULT_CONTRACT_MONTHS = 12


def _utcnow_iso() -> str:
    return datetime.now(UTC).isoformat()


def _contract_months(amount_usd: float) -> int:
    if amount_usd >= 12000:
        return 12
    if amount_usd >= 6000:
        return 6
    return DEFAULT_CONTRACT_MONTHS


async def activate_institutional_from_invoice(
    *,
    email: str,
    invoice_id: str,
    amount_usd: float,
    plan: str | None = None,
    org_id: str | None = None,
    source: str = "institutional_commerce",
    external_ref: str = "",
    period_months: int | None = None,
) -> dict[str, Any]:
    """
    Wire institutional_commerce paid invoice → subscription_accounts SSOT.
    Idempotent on invoice_id via payment event key.
    """
    from database import fetch_user_by_email

    email = email.strip().lower()
    canonical = normalize_plan(plan or "institutional")
    if canonical != "institutional":
        canonical = "institutional"
    if float(amount_usd) < INSTITUTIONAL_MIN_USD:
        raise ValueError(f"institutional_amount_below_minimum:{INSTITUTIONAL_MIN_USD}")

    user = await fetch_user_by_email(email)
    if not user:
        raise ValueError("user_not_found_register_first")

    uid = int(user["id"])
    months = period_months or _contract_months(float(amount_usd))
    now = datetime.now(UTC)
    period_start = now.isoformat()
    period_end = (now + timedelta(days=30 * months)).isoformat()
    provider_sub_id = f"inst_{invoice_id}"

    pay_id, is_new = await _record_payment_event(
        user_id=uid,
        email=email,
        provider="manual",
        provider_event_id=invoice_id,
        event_type="institutional_invoice_paid",
        status="succeeded",
        amount_cents=int(round(float(amount_usd) * 100)),
        plan=canonical,
        raw_event_type=source,
    )
    if not is_new:
        sub = await get_by_user_id(uid)
        return {"duplicate": True, "subscription": sub, "payment_event_id": pay_id}

    await ensure_subscription_account(uid, email, plan=canonical)
    updated = await update_subscription_account(
        uid,
        plan=canonical,
        subscription_status="active",
        payment_status="current",
        start_date=period_start,
        current_period_start=period_start,
        current_period_end=period_end,
        renewal_date=period_end,
        cancel_at_period_end=False,
        auto_renew_enabled=True,
        auto_renew_consent_at=period_start,
        provider="institutional",
        provider_subscription_id=provider_sub_id,
        pending_plan=None,
        grace_period_end=None,
        bump_entitlements=True,
    )

    from database import activate_paid_subscription

    await activate_paid_subscription(email, canonical, provider_sub_id)

    await record_audit(
        action="INSTITUTIONAL_ACTIVATED",
        actor=f"commerce:{source}",
        user_id=uid,
        email=email,
        old_plan=None,
        new_plan=canonical,
        new_status="active",
        amount_cents=int(round(float(amount_usd) * 100)),
        payment_event_id=pay_id,
        provider_subscription_id=provider_sub_id,
        reason=f"invoice={invoice_id} ref={external_ref} org={org_id or ''} months={months}",
        entitlements_version=updated.get("entitlements_version"),
        metadata={"org_id": org_id, "period_months": months},
    )
    return {
        "duplicate": False,
        "subscription": updated,
        "payment_event_id": pay_id,
        "period_months": months,
        "entitlements_version": updated.get("entitlements_version"),
    }
