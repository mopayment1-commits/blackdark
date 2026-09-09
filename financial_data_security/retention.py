"""Retention and secure deletion policy for financial data classes."""

from __future__ import annotations

from typing import Any

RETENTION_POLICY: dict[str, dict[str, Any]] = {
    "payment_references": {"retention_days": 2555, "deletion": "secure_delete_on_account_closure"},
    "billing_audit": {"retention_days": 2555, "deletion": "append_only_then_archive"},
    "webhook_inbox": {"retention_days": 90, "deletion": "purge_processed"},
    "financial_secrets": {"retention_days": 0, "deletion": "revoke_on_rotation"},
    "restricted_auth_data": {"retention_days": 0, "deletion": "never_store"},
}


def retention_for(class_name: str) -> dict[str, Any]:
    return RETENTION_POLICY.get(class_name, {"retention_days": 90, "deletion": "policy_review"})


def retention_status() -> dict[str, Any]:
    return {"policies": RETENTION_POLICY, "indefinite_retention_default": False, "testable": True}
