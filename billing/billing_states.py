"""Canonical billing state model (BILL-009) — internal projection, not raw Stripe copy."""

from __future__ import annotations

from enum import StrEnum
from typing import Final

# Canonical internal billing states per BILL-009
BILLING_STATES: Final[tuple[str, ...]] = (
    "FREE",
    "CHECKOUT_PENDING",
    "INCOMPLETE",
    "INCOMPLETE_EXPIRED",
    "TRIALING",
    "ACTIVE",
    "PAST_DUE",
    "UNPAID",
    "PAUSED",
    "CANCEL_AT_PERIOD_END",
    "CANCELED",
    "REFUND_PENDING",
    "PARTIALLY_REFUNDED",
    "REFUNDED",
    "DISPUTE_OPEN",
    "DISPUTE_WON",
    "DISPUTE_LOST",
)


class BillingState(StrEnum):
    FREE = "FREE"
    CHECKOUT_PENDING = "CHECKOUT_PENDING"
    INCOMPLETE = "INCOMPLETE"
    INCOMPLETE_EXPIRED = "INCOMPLETE_EXPIRED"
    TRIALING = "TRIALING"
    ACTIVE = "ACTIVE"
    PAST_DUE = "PAST_DUE"
    UNPAID = "UNPAID"
    PAUSED = "PAUSED"
    CANCEL_AT_PERIOD_END = "CANCEL_AT_PERIOD_END"
    CANCELED = "CANCELED"
    REFUND_PENDING = "REFUND_PENDING"
    PARTIALLY_REFUNDED = "PARTIALLY_REFUNDED"
    REFUNDED = "REFUNDED"
    DISPUTE_OPEN = "DISPUTE_OPEN"
    DISPUTE_WON = "DISPUTE_WON"
    DISPUTE_LOST = "DISPUTE_LOST"


STRIPE_TO_BILLING: dict[str, BillingState] = {
    "active": BillingState.ACTIVE,
    "trialing": BillingState.TRIALING,
    "past_due": BillingState.PAST_DUE,
    "canceled": BillingState.CANCELED,
    "unpaid": BillingState.UNPAID,
    "incomplete": BillingState.INCOMPLETE,
    "incomplete_expired": BillingState.INCOMPLETE_EXPIRED,
    "paused": BillingState.PAUSED,
}


SUBSCRIPTION_STATUS_TO_BILLING: dict[str, BillingState] = {
    "active": BillingState.ACTIVE,
    "trialing": BillingState.TRIALING,
    "past_due": BillingState.PAST_DUE,
    "canceled": BillingState.CANCELED,
    "expired": BillingState.CANCELED,
}


PAYMENT_STATUS_TO_BILLING: dict[str, BillingState] = {
    "refunded": BillingState.REFUNDED,
    "disputed": BillingState.DISPUTE_OPEN,
    "chargeback": BillingState.DISPUTE_LOST,
    "partial_refund": BillingState.PARTIALLY_REFUNDED,
}


def project_billing_state(
    *,
    plan: str,
    subscription_status: str,
    payment_status: str,
    cancel_at_period_end: bool = False,
) -> BillingState:
    """Map subscription_accounts row to canonical billing state."""
    if plan == "free" and subscription_status in {"active", "expired"}:
        return BillingState.FREE
    if payment_status in PAYMENT_STATUS_TO_BILLING:
        return PAYMENT_STATUS_TO_BILLING[payment_status]
    if cancel_at_period_end and subscription_status == "canceled":
        return BillingState.CANCEL_AT_PERIOD_END
    return STRIPE_TO_BILLING.get(subscription_status, BillingState.ACTIVE)
