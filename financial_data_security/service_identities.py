"""Service and machine identity registry."""

from __future__ import annotations

from typing import Any

SERVICE_IDENTITIES: dict[str, dict[str, Any]] = {
    "billing_webhook_worker": {"scope": "billing.webhook.process", "shared_credential": False},
    "billing_reconciliation": {"scope": "billing.reconcile", "shared_credential": False},
    "stripe_checkout_api": {"scope": "billing.checkout.create", "shared_credential": False},
    "secrets_vault": {"scope": "credentials.encrypt_decrypt", "shared_credential": False},
    "financial_audit_writer": {"scope": "audit.financial.append", "shared_credential": False},
}


def service_identity_status() -> dict[str, Any]:
    return {
        "identities": list(SERVICE_IDENTITIES.keys()),
        "count": len(SERVICE_IDENTITIES),
        "scoped": True,
        "shared_static_production_credential": False,
    }
