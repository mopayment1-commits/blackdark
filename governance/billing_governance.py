"""Billing governance runtime — BILL durable webhooks + entitlements (BGS-005)."""

from __future__ import annotations

from typing import Any


def billing_governance_status() -> dict[str, Any]:
    from billing_service import billing_configured, billing_provider, stripe_configured

    try:
        from billing.plan_registry import PLAN_DEFINITIONS, SELF_SERVE_PLANS

        plans_ok = len(PLAN_DEFINITIONS) >= 4
    except Exception:
        plans_ok = False

    webhook_durable = False
    try:
        from database import claim_billing_webhook_event  # noqa: F401

        webhook_durable = True
    except Exception:
        pass

    return {
        "billing_configured": billing_configured(),
        "provider": billing_provider(),
        "stripe_configured": stripe_configured(),
        "plans_ok": plans_ok,
        "self_serve_plans": list(SELF_SERVE_PLANS) if plans_ok else [],
        "webhook_dedup_durable": webhook_durable,
        "entitlement_engine": True,
    }
