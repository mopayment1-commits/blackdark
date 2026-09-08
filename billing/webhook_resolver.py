"""Resolve Stripe charge/refund/dispute events to subscription accounts (BILL-027, BILL-028)."""

from __future__ import annotations

from typing import Any


async def resolve_subscription_from_charge(charge: dict[str, Any]) -> dict[str, Any] | None:
    """Map charge object to subscription via invoice → subscription or customer lookup."""
    from billing.subscription_store import get_by_provider_subscription_id
    from database import get_connection

    invoice_id = charge.get("invoice")
    customer_id = charge.get("customer")
    payment_intent = charge.get("payment_intent")

    # Direct subscription on charge metadata
    meta_sub = (charge.get("metadata") or {}).get("subscription_id")
    if meta_sub:
        sub = await get_by_provider_subscription_id(str(meta_sub))
        if sub:
            return sub

    async with get_connection() as db:
        if invoice_id:
            row = await (
                await db.execute(
                    """
                    SELECT sa.* FROM subscription_accounts sa
                    JOIN billing_payment_events bpe ON bpe.user_id = sa.user_id
                    WHERE bpe.provider_invoice_id = ?
                    ORDER BY bpe.id DESC LIMIT 1
                    """,
                    (str(invoice_id),),
                )
            ).fetchone()
            if row:
                return dict(row)

        if customer_id:
            row = await (
                await db.execute(
                    """
                    SELECT * FROM subscription_accounts
                    WHERE provider_customer_id = ?
                    ORDER BY updated_at DESC LIMIT 1
                    """,
                    (str(customer_id),),
                )
            ).fetchone()
            if row:
                return dict(row)

        if payment_intent:
            row = await (
                await db.execute(
                    """
                    SELECT sa.* FROM subscription_accounts sa
                    JOIN billing_payment_events bpe ON bpe.user_id = sa.user_id
                    WHERE bpe.provider_event_id LIKE ?
                    ORDER BY bpe.id DESC LIMIT 1
                    """,
                    (f"%{payment_intent}%",),
                )
            ).fetchone()
            if row:
                return dict(row)
    return None


async def handle_refund_event(
    charge: dict[str, Any],
    *,
    provider: str,
    provider_event_id: str,
    partial: bool = False,
) -> dict[str, Any]:
    from billing.subscription_engine import revoke_for_financial_reversal

    sub = await resolve_subscription_from_charge(charge)
    if not sub:
        return {"handled": False, "reason": "subscription_not_found_for_charge"}
    payment_status = "partial_refund" if partial else "refunded"
    return await revoke_for_financial_reversal(
        provider_subscription_id=sub.get("provider_subscription_id"),
        user_id=int(sub["user_id"]),
        provider=provider,
        provider_event_id=provider_event_id,
        reason="charge_refunded" if not partial else "partial_refund",
        payment_status=payment_status,
    )


async def handle_dispute_event(
    charge: dict[str, Any],
    *,
    provider: str,
    provider_event_id: str,
    dispute_status: str = "open",
) -> dict[str, Any]:
    from billing.subscription_engine import revoke_for_financial_reversal

    sub = await resolve_subscription_from_charge(charge)
    if not sub:
        return {"handled": False, "reason": "subscription_not_found_for_charge"}
    pay_status = {"open": "disputed", "won": "current", "lost": "chargeback"}.get(
        dispute_status, "disputed"
    )
    if pay_status == "current":
        from billing.subscription_store import update_subscription_account

        updated = await update_subscription_account(
            int(sub["user_id"]),
            payment_status="current",
            subscription_status="active",
            bump_entitlements=True,
        )
        return {"handled": True, "action": "dispute_won", "subscription": updated}
    return await revoke_for_financial_reversal(
        provider_subscription_id=sub.get("provider_subscription_id"),
        user_id=int(sub["user_id"]),
        provider=provider,
        provider_event_id=provider_event_id,
        reason=f"charge_dispute_{dispute_status}",
        payment_status=pay_status,
    )
