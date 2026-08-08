"""Billing API router."""

from __future__ import annotations

import json

import stripe
from fastapi import APIRouter, Body, Depends, HTTPException, Request

from api.deps import optional_user
from security_auth import require_admin

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/status")
async def billing_status(user: dict | None = Depends(optional_user)):
    from billing_service import billing_configured, billing_provider
    from database import fetch_active_subscription_for_email, fetch_user_stripe_customer_id

    if not user:
        return {
            "authenticated": False,
            "billing_configured": billing_configured(),
            "billing_provider": billing_provider(),
        }
    sub = await fetch_active_subscription_for_email(user["email"])
    return {
        "authenticated": True,
        "billing_configured": billing_configured(),
        "billing_provider": billing_provider(),
        "stripe_customer_id": await fetch_user_stripe_customer_id(user["email"]),
        "subscription": sub,
        "tier": user.get("tier"),
        "has_billing_portal": bool(await fetch_user_stripe_customer_id(user["email"])),
    }


@router.post("/checkout")
async def billing_checkout(
    data: dict = Body(default={}),
    user: dict | None = Depends(optional_user),
):
    from billing_service import billing_configured, create_checkout_session, lemon_squeezy_checkout_url

    tier = str(data.get("tier") or "pro")
    ls_url = lemon_squeezy_checkout_url(tier)
    if ls_url:
        return {"url": ls_url, "provider": "lemon_squeezy", "tier": tier}
    if not billing_configured():
        raise HTTPException(status_code=503, detail="Billing not configured")
    email = user.get("email") if user else None
    user_id = int(user["id"]) if user and user.get("id") else None
    try:
        return create_checkout_session(tier, customer_email=email, user_id=user_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/portal")
async def billing_portal(user: dict | None = Depends(optional_user)):
    from billing_service import create_billing_portal_session, stripe_configured
    from database import fetch_user_stripe_customer_id

    if not user:
        raise HTTPException(status_code=401, detail="Login required")
    if not stripe_configured():
        raise HTTPException(status_code=503, detail="Stripe not configured")
    customer_id = await fetch_user_stripe_customer_id(user["email"])
    if not customer_id:
        raise HTTPException(status_code=400, detail="No Stripe customer — subscribe first")
    try:
        return create_billing_portal_session(customer_id)
    except stripe.StripeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


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
    return {"received": True, **result}


@router.get("/reports/mrr")
async def billing_reports_mrr(admin: dict = Depends(require_admin)):
    from billing_service import generate_mrr_report

    report = await generate_mrr_report()
    report["requested_by"] = admin.get("email")
    return report


@router.get("/reports/churn")
async def billing_reports_churn(
    window_days: int = 30,
    admin: dict = Depends(require_admin),
):
    from billing_service import compute_churn_rate

    report = await compute_churn_rate(window_days=window_days)
    report["requested_by"] = admin.get("email")
    return report
