"""Retention registry — ID-048."""

from __future__ import annotations

from typing import Any

RETENTION_REGISTRY: list[dict[str, Any]] = [
    {
        "category": "account_credentials",
        "purpose": "authentication",
        "lawful_basis": "contract",
        "retention_days": None,
        "delete_behavior": "on_account_deletion",
    },
    {
        "category": "identity_audit_events",
        "purpose": "security_investigation",
        "lawful_basis": "legitimate_interest",
        "retention_days": 365,
        "delete_behavior": "anonymize_actor",
    },
    {
        "category": "login_history",
        "purpose": "user_security_visibility",
        "lawful_basis": "legitimate_interest",
        "retention_days": 90,
        "delete_behavior": "purge",
    },
    {
        "category": "billing_records",
        "purpose": "tax_and_contract",
        "lawful_basis": "legal_obligation",
        "retention_days": 2555,
        "delete_behavior": "retain_anonymized_reference",
    },
]


def retention_manifest() -> dict[str, Any]:
    return {"categories": RETENTION_REGISTRY, "operational_target_days": 30}
