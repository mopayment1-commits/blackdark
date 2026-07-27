"""Billing API router."""

from __future__ import annotations

import stripe
from fastapi import APIRouter, Body, Depends, HTTPException

from api.deps import optional_user

router = APIRouter(prefix="/api/billing", tags=["billing"])


@router.get("/status")
async def billing_status(user: dict | None = Depends(optional_user)):
    from billing_service import stripe_configured
    from database import fetch_active_subscription_for_email, fetch_user_stripe_customer_id

    if not user:
        return {"authenticated": False, "stripe_configured": stripe_configured()}
    sub = await fetch_active_subscription_for_email(user["email"])
    return {
        "authenticated": True,
        "stripe_configured": stripe_configured(),
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
    from billing_service import create_checkout_session, stripe_configured

    if not stripe_configured():
        raise HTTPException(status_code=503, detail="Stripe not configured")
    tier = str(data.get("tier") or "pro")
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
