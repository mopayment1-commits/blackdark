"""Billing API router — USD Trust OS payments (hosted PSP only)."""

from __future__ import annotations

import json

import stripe
from fastapi import APIRouter, Body, Depends, HTTPException, Request

from api.deps import optional_user


def _is_valid_email(email: str) -> bool:
    """Strict structural email check without backtracking-prone regex."""
    if not email or len(email) > 254 or " " in email or "\n" in email or "\r" in email:
        return False
    if email.count("@") != 1:
        return False
    local, domain = email.split("@", 1)
    if not local or not domain or "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith(".") or ".." in domain:
        return False
    # ASCII-ish local/domain only (product emails)
    allowed = set("abcdefghijklmnopqrstuvwxyz0123456789._+-")
    if any(c not in allowed for c in local):
        return False
    allowed_d = set("abcdefghijklmnopqrstuvwxyz0123456789.-")
    return all(c in allowed_d for c in domain)


router = APIRouter(prefix="/api/billing", tags=["billing"])



@router.get("/status")
async def billing_status(user: dict | None = Depends(optional_user)):
    from billing_service import (
        billing_configured,
        billing_provider,
        lemon_squeezy_portal_url,
    )
    from database import fetch_active_subscription_for_email, fetch_user_stripe_customer_id
    from payments_usd import BILLING_CURRENCY_DISPLAY, SECURITY_POSTURE

    provider = billing_provider()
    base = {
        "currency": BILLING_CURRENCY_DISPLAY,
        "billing_configured": billing_configured(),
        "billing_provider": provider,
        "stripe_configured": billing_configured(),  # backward-compatible UI flag
        "stores_card_numbers": False,
        "pci_target": SECURITY_POSTURE["pci_target"],
        "lemon_portal_configured": bool(lemon_squeezy_portal_url()),
    }
    if not user:
        return {"authenticated": False, **base}
    sub = await fetch_active_subscription_for_email(user["email"])
    customer_id = await fetch_user_stripe_customer_id(user["email"])
    return {
        "authenticated": True,
        **base,
        "stripe_customer_id": customer_id,
        "subscription": sub,
        "tier": user.get("tier"),
        "has_billing_portal": bool(customer_id) or bool(lemon_squeezy_portal_url()),
    }


@router.get("/payments")
async def billing_payments_architecture():
    """USD payment architecture + security posture (no secrets)."""
    from payments_usd import payments_architecture

    return payments_architecture()


@router.get("/refund-policy")
async def billing_refund_policy():
    from payments_usd import refund_policy_public

    return refund_policy_public()


@router.post("/checkout")
async def billing_checkout(
    data: dict = Body(default={}),
    user: dict | None = Depends(optional_user),
):
    from billing_service import (
        BILLING_CURRENCY,
        billing_configured,
        create_checkout_session,
        lemon_squeezy_checkout_url,
    )
    from payments_usd import SELF_SERVE_SKUS

    tier = str(data.get("tier") or "pro").lower().strip()
    if tier not in SELF_SERVE_SKUS:
        raise HTTPException(
            status_code=400,
            detail="Invalid tier. Self-serve USD SKUs: pro, whale. Institutional is Talk to us.",
        )

    ls_url = lemon_squeezy_checkout_url(tier)
    if ls_url:
        return {
            "url": ls_url,
            "provider": "lemon_squeezy",
            "tier": tier,
            "currency": BILLING_CURRENCY.upper(),
            "amount_usd": SELF_SERVE_SKUS[tier]["amount_usd"],
            "name": SELF_SERVE_SKUS[tier]["name"],
            "pci_note": "Card data collected only on Lemon Squeezy-hosted Checkout.",
            "trial_days": SELF_SERVE_SKUS[tier].get("trial_days") or 0,
        }
    if not billing_configured():
        raise HTTPException(status_code=503, detail="Billing not configured")
    email = user.get("email") if user else None
    user_id = int(user["id"]) if user and user.get("id") else None
    try:
        payload = create_checkout_session(tier, customer_email=email, user_id=user_id)
        payload["amount_usd"] = SELF_SERVE_SKUS[tier]["amount_usd"]
        payload["name"] = SELF_SERVE_SKUS[tier]["name"]
        return payload
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/portal")
async def billing_portal(user: dict | None = Depends(optional_user)):
    from billing_service import (
        create_billing_portal_session,
        lemon_squeezy_portal_url,
        stripe_configured,
    )
    from database import fetch_user_stripe_customer_id

    if not user:
        raise HTTPException(status_code=401, detail="Login required")

    lemon_portal = lemon_squeezy_portal_url()
    if lemon_portal:
        return {
            "url": lemon_portal,
            "provider": "lemon_squeezy",
            "currency": "USD",
        }

    if not stripe_configured():
        raise HTTPException(
            status_code=503,
            detail="Billing portal not configured (set Stripe or LEMON_SQUEEZY_CUSTOMER_PORTAL_URL)",
        )
    customer_id = await fetch_user_stripe_customer_id(user["email"])
    if not customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer — subscribe first")
    try:
        payload = create_billing_portal_session(customer_id)
        payload["provider"] = "stripe"
        payload["currency"] = "USD"
        return payload
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/institutional-inquiry")
async def institutional_inquiry(data: dict = Body(default={})):
    """Sales-led Institutional path — USD wire / invoice, not self-serve Checkout."""
    from database import insert_institutional_inquiry
    from payments_usd import INSTITUTIONAL_WIRE

    email = str(data.get("email") or "").strip().lower()
    if not email or not _is_valid_email(email):
        raise HTTPException(status_code=400, detail="Valid email required")
    inquiry_id = await insert_institutional_inquiry(
        email=email,
        name=str(data.get("name") or ""),
        company=str(data.get("company") or ""),
        message=str(data.get("message") or ""),
        budget_usd=str(data.get("budget_usd") or data.get("budget") or ""),
    )
    return {
        "ok": True,
        "inquiry_id": inquiry_id,
        "currency": "USD",
        "next": INSTITUTIONAL_WIRE["cta"],
        "message": (
            "Thanks — Institutional is sales-led (invoice / USD wire). "
            "We will follow up with an Integration Addendum checklist."
        ),
        "self_serve": False,
    }


@router.post("/webhook/lemon")
async def lemon_webhook(request: Request):
    """Lemon Squeezy entitlement webhook — HMAC-SHA256 via X-Signature."""
    from billing_service import handle_lemon_webhook_event, verify_lemon_webhook_signature

    raw = await request.body()
    sig = request.headers.get("X-Signature") or request.headers.get("x-signature")
    if not verify_lemon_webhook_signature(raw, sig):
        raise HTTPException(status_code=401, detail="Invalid Lemon Squeezy webhook signature")
    try:
        event = json.loads(raw.decode("utf-8") or "{}")
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON payload") from exc
    if not isinstance(event, dict):
        raise HTTPException(status_code=400, detail="Invalid webhook body")
    result = await handle_lemon_webhook_event(event)
    return {"received": True, "currency": "USD", **result}
