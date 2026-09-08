"""Entitlement state model and decision engine (BILL-010, BILL-011) — separate from billing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from billing.billing_states import BillingState, project_billing_state
from billing.plan_registry import normalize_plan, plan_rank


class EntitlementState(StrEnum):
    FREE = "FREE"
    PAID_PENDING = "PAID_PENDING"
    PAID_ACTIVE = "PAID_ACTIVE"
    PAID_RECOVERY = "PAID_RECOVERY"
    PAID_CANCELING_AT_PERIOD_END = "PAID_CANCELING_AT_PERIOD_END"
    SUSPENDED = "SUSPENDED"
    REVOKED = "REVOKED"
    MANUAL_TEMPORARY_OVERRIDE = "MANUAL_TEMPORARY_OVERRIDE"


REVOKED_PAYMENT = frozenset({"refunded", "disputed", "chargeback"})
ACTIVE_BILLING = frozenset(
    {BillingState.ACTIVE, BillingState.TRIALING, BillingState.PAST_DUE, BillingState.CANCEL_AT_PERIOD_END}
)


@dataclass(frozen=True)
class EntitlementDecision:
    state: EntitlementState
    effective_tier: str
    paid_through: str | None
    allowed: bool
    verification_source: str
    payment_reference: str | None = None
    subscription_reference: str | None = None
    reason: str = ""


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def decide_entitlement(
    sub: dict[str, Any] | None,
    *,
    now: datetime | None = None,
    manual_override: dict[str, Any] | None = None,
) -> EntitlementDecision:
    """Fail-closed entitlement decision from verified billing projection evidence."""
    now = now or datetime.now(UTC)
    if manual_override:
        expires = _parse_dt(manual_override.get("expires_at"))
        if expires and now <= expires:
            tier = normalize_plan(str(manual_override.get("new_tier") or "free"))
            return EntitlementDecision(
                state=EntitlementState.MANUAL_TEMPORARY_OVERRIDE,
                effective_tier=tier,
                paid_through=manual_override.get("paid_through"),
                allowed=tier != "free",
                verification_source="break_glass",
                reason=str(manual_override.get("reason") or "manual_override"),
            )

    if not sub:
        return EntitlementDecision(
            state=EntitlementState.FREE,
            effective_tier="free",
            paid_through=None,
            allowed=True,
            verification_source="default_free",
        )

    plan = normalize_plan(str(sub.get("plan") or "free"))
    pay_status = str(sub.get("payment_status") or "none")
    sub_status = str(sub.get("subscription_status") or "")
    period_end = sub.get("current_period_end")
    grace_end = sub.get("grace_period_end")
    paid_through = str(period_end) if period_end else None
    provider_sub = sub.get("provider_subscription_id")
    billing = project_billing_state(
        plan=plan,
        subscription_status=sub_status,
        payment_status=pay_status,
        cancel_at_period_end=bool(sub.get("cancel_at_period_end")),
    )

    if pay_status in REVOKED_PAYMENT or billing in {
        BillingState.REFUNDED,
        BillingState.DISPUTE_OPEN,
        BillingState.DISPUTE_LOST,
    }:
        return EntitlementDecision(
            state=EntitlementState.REVOKED,
            effective_tier="free",
            paid_through=paid_through,
            allowed=False,
            verification_source="financial_reversal",
            subscription_reference=str(provider_sub) if provider_sub else None,
            reason=f"payment_status={pay_status}",
        )

    if plan == "free":
        return EntitlementDecision(
            state=EntitlementState.FREE,
            effective_tier="free",
            paid_through=None,
            allowed=True,
            verification_source="internal_free",
        )

    # BILL-001 / BILL-016: subscription.updated alone is not payment proof
    if pay_status in {"none", ""} and sub_status in {"active", "trialing"}:
        return EntitlementDecision(
            state=EntitlementState.PAID_PENDING,
            effective_tier="free",
            paid_through=paid_through,
            allowed=False,
            verification_source="fail_closed_no_payment_proof",
            subscription_reference=str(provider_sub) if provider_sub else None,
            reason="missing_payment_proof",
        )

    end_dt = _parse_dt(paid_through)
    grace_dt = _parse_dt(str(grace_end) if grace_end else None)

    # Stripe outage: proven paid_through still valid — no blind revoke (BILL-011)
    if end_dt and now <= end_dt and billing in ACTIVE_BILLING:
        if sub_status == "past_due" or billing == BillingState.PAST_DUE:
            return EntitlementDecision(
                state=EntitlementState.PAID_RECOVERY,
                effective_tier=plan,
                paid_through=paid_through,
                allowed=True,
                verification_source="paid_through_recovery",
                subscription_reference=str(provider_sub) if provider_sub else None,
                reason="past_due_within_paid_through",
            )
        if sub_status == "canceled" or billing == BillingState.CANCEL_AT_PERIOD_END:
            return EntitlementDecision(
                state=EntitlementState.PAID_CANCELING_AT_PERIOD_END,
                effective_tier=plan,
                paid_through=paid_through,
                allowed=True,
                verification_source="paid_through_cancel_scheduled",
                subscription_reference=str(provider_sub) if provider_sub else None,
            )
        if sub_status in {"active", "trialing"}:
            return EntitlementDecision(
                state=EntitlementState.PAID_ACTIVE,
                effective_tier=plan,
                paid_through=paid_through,
                allowed=True,
                verification_source="checkout_or_renewal_proof",
                subscription_reference=str(provider_sub) if provider_sub else None,
            )

    if grace_dt and now <= grace_dt and sub_status == "past_due":
        return EntitlementDecision(
            state=EntitlementState.PAID_RECOVERY,
            effective_tier=plan,
            paid_through=grace_dt.isoformat(),
            allowed=True,
            verification_source="grace_policy",
            subscription_reference=str(provider_sub) if provider_sub else None,
            reason="grace_period",
        )

    if sub_status == "expired" or (end_dt and now > end_dt):
        pending = normalize_plan(str(sub.get("pending_plan") or "free"))
        return EntitlementDecision(
            state=EntitlementState.REVOKED if pending == "free" else EntitlementState.PAID_ACTIVE,
            effective_tier=pending,
            paid_through=paid_through,
            allowed=pending != "free",
            verification_source="period_expired",
            subscription_reference=str(provider_sub) if provider_sub else None,
        )

    # Unknown/unverified — fail closed for paid tiers (BILL-001)
    if plan_rank(plan) > 0:
        return EntitlementDecision(
            state=EntitlementState.PAID_PENDING,
            effective_tier="free",
            paid_through=paid_through,
            allowed=False,
            verification_source="fail_closed",
            reason="unverified_paid_entitlement",
        )

    return EntitlementDecision(
        state=EntitlementState.FREE,
        effective_tier="free",
        paid_through=None,
        allowed=True,
        verification_source="fallback_free",
    )


async def resolve_entitlement_decision(user_id: int) -> EntitlementDecision:
    from billing.break_glass import active_override_for_user
    from billing.subscription_store import get_by_user_id

    sub = await get_by_user_id(user_id)
    override = await active_override_for_user(user_id)
    return decide_entitlement(sub, manual_override=override)
