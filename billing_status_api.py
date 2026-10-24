"""Shared /api/billing/status payload (GTM fallback when billing router is unavailable)."""

from __future__ import annotations

from typing import Any


async def build_billing_status_payload(user: dict[str, Any] | None) -> dict[str, Any]:
    from billing.subscription_engine import resolve_entitlements_for_user
    from billing_service import (
        billing_configured,
        billing_provider,
        lemon_squeezy_portal_url,
    )
    from database import fetch_active_subscription_for_email, fetch_user_stripe_customer_id
    from payments_usd import BILLING_CURRENCY_DISPLAY, SECURITY_POSTURE

    try:
        provider = billing_provider()
        base = {
            "currency": BILLING_CURRENCY_DISPLAY,
            "billing_configured": billing_configured(),
            "billing_provider": provider,
            "stripe_configured": billing_configured(),
            "stores_card_numbers": False,
            "pci_target": SECURITY_POSTURE["pci_target"],
            "lemon_portal_configured": bool(lemon_squeezy_portal_url()),
        }
        if not user:
            return {"authenticated": False, **base}
        sub = await fetch_active_subscription_for_email(user["email"])
        entitlements = await resolve_entitlements_for_user(int(user["id"]))
        from entitlements_service import async_resolve_entitlements

        feature_bundle = await async_resolve_entitlements(int(user["id"]))
        customer_id = await fetch_user_stripe_customer_id(user["email"])
        return {
            "authenticated": True,
            **base,
            "stripe_customer_id": customer_id,
            "subscription": sub,
            "entitlements": entitlements,
            "features": feature_bundle,
            "tier": feature_bundle.get("effective_plan") or entitlements.get("effective_plan") or user.get("tier"),
            "has_billing_portal": bool(customer_id) or bool(lemon_squeezy_portal_url()),
        }
    except Exception:
        return {
            "authenticated": bool(user),
            "currency": "USD",
            "billing_configured": False,
            "billing_provider": "none",
            "stripe_configured": False,
            "stores_card_numbers": False,
            "error": "billing_status_unavailable",
        }
