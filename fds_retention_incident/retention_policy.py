"""Canonical financial data retention matrix (FDS-20)."""

from __future__ import annotations

from typing import Any, Literal

from financial_data.classification import FDSClass

POLICY_VERSION = "fds-retention-v1"

DeletionMethod = Literal[
    "DELETE",
    "ANONYMIZE",
    "CRYPTO_ERASE",
    "REVOKE",
    "TOKEN_REVOKE",
    "BACKUP_EXPIRY",
    "ZERO_RETENTION",
]

_FINANCIAL_RETENTION: dict[str, dict[str, Any]] = {
    "financial_credentials": {
        "fds_classes": [FDSClass.C3_BANKING.value, FDSClass.C4_SECRET.value],
        "purpose": "exchange_and_financial_api_credentials",
        "owner": "user_keys_service",
        "legal_basis": "contract",
        "retention_days": 0,
        "retention_note": "retain_until_account_active_or_legal_hold",
        "max_retention_days": 365,
        "deletion_trigger": "account_closure_or_credential_revocation",
        "deletion_method": "CRYPTO_ERASE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "credential_revocation_audit",
    },
    "payment_references": {
        "fds_classes": [FDSClass.C6_PAYMENT_REFERENCE.value],
        "purpose": "payment_provider_reconciliation",
        "owner": "billing/subscription_engine",
        "legal_basis": "contract_and_legal_obligation",
        "retention_days": 2555,
        "deletion_trigger": "retention_expiry_or_account_closure_anonymize",
        "deletion_method": "ANONYMIZE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "billing_audit_ledger",
    },
    "subscription_identifiers": {
        "fds_classes": [FDSClass.C6_PAYMENT_REFERENCE.value],
        "purpose": "subscription_lifecycle_and_provider_reconciliation",
        "owner": "billing/subscription_engine",
        "legal_basis": "contract_and_legal_obligation",
        "retention_days": 2555,
        "deletion_trigger": "retention_expiry_or_account_closure_anonymize",
        "deletion_method": "ANONYMIZE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "subscription_accounts_audit",
    },
    "billing_history": {
        "fds_classes": [FDSClass.C6_PAYMENT_REFERENCE.value],
        "purpose": "billing_payment_events_and_invoice_reconciliation",
        "owner": "billing/subscription_engine",
        "legal_basis": "legal_obligation",
        "retention_days": 2555,
        "deletion_trigger": "retention_expiry_only",
        "deletion_method": "ANONYMIZE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "billing_payment_events_audit",
    },
    "financial_account_metadata": {
        "fds_classes": [FDSClass.C5_SENSITIVE_FINANCIAL.value],
        "purpose": "financial_account_profile_and_tier_metadata",
        "owner": "database/subscription_accounts",
        "legal_basis": "contract",
        "retention_days": 365,
        "deletion_trigger": "account_closure_or_dsr_erase",
        "deletion_method": "DELETE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "account_closure_audit",
    },
    "user_personal": {
        "fds_classes": [FDSClass.C5_SENSITIVE_FINANCIAL.value],
        "purpose": "user_financial_intelligence",
        "owner": "gdpr_service",
        "legal_basis": "contract",
        "retention_days": 365,
        "deletion_trigger": "account_closure_or_dsr_erase",
        "deletion_method": "DELETE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "dsr_erase_audit",
    },
    "support_export_artifacts": {
        "fds_classes": [FDSClass.C5_SENSITIVE_FINANCIAL.value, FDSClass.C6_PAYMENT_REFERENCE.value],
        "purpose": "dsr_export_and_support_artifacts_with_financial_metadata",
        "owner": "gdpr_service",
        "legal_basis": "contract",
        "retention_days": 30,
        "deletion_trigger": "export_delivery_or_account_closure",
        "deletion_method": "DELETE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "dsr_export_audit",
    },
    "audit_replay": {
        "fds_classes": [],
        "purpose": "tamper_evident_audit_and_security",
        "owner": "audit_registry",
        "legal_basis": "legal_obligation",
        "retention_days": 2555,
        "deletion_trigger": "retention_expiry_only",
        "deletion_method": "ANONYMIZE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "audit_retention_review",
    },
    "credential_rotation": {
        "fds_classes": [FDSClass.C4_SECRET.value],
        "purpose": "rotated_financial_secrets_metadata",
        "owner": "secrets_crypto/lifecycle",
        "legal_basis": "security",
        "retention_days": 90,
        "deletion_trigger": "rotation_grace_expired",
        "deletion_method": "REVOKE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "secret_lifecycle_evidence",
    },
    "revoked_financial_credentials": {
        "fds_classes": [FDSClass.C3_BANKING.value, FDSClass.C4_SECRET.value],
        "purpose": "revoked_or_expired_financial_credential_metadata",
        "owner": "secrets_crypto/lifecycle",
        "legal_basis": "security",
        "retention_days": 90,
        "deletion_trigger": "revocation_grace_expired",
        "deletion_method": "TOKEN_REVOKE",
        "backup_handling": "BACKUP_EXPIRY",
        "verification": "credential_revocation_audit",
    },
    "zero_retention": {
        "fds_classes": [FDSClass.C1_SAD.value, FDSClass.C2_PAN.value],
        "purpose": "prohibited_storage",
        "owner": "financial_data/boundary",
        "legal_basis": "prohibited",
        "retention_days": 0,
        "deletion_trigger": "immediate_reject",
        "deletion_method": "ZERO_RETENTION",
        "backup_handling": "ZERO_RETENTION",
        "verification": "scanner_and_boundary",
    },
}


def financial_retention_matrix() -> list[dict[str, Any]]:
    return [
        {"policy_key": key, "policy_version": POLICY_VERSION, **value}
        for key, value in _FINANCIAL_RETENTION.items()
    ]


def retention_for_class(fds_class: FDSClass | str) -> dict[str, Any]:
    cls = fds_class.value if isinstance(fds_class, FDSClass) else str(fds_class)
    for key, policy in _FINANCIAL_RETENTION.items():
        if cls in policy.get("fds_classes", []):
            return {"policy_key": key, "policy_version": POLICY_VERSION, **policy}
    from financial_data.classification import class_definition

    link = class_definition(FDSClass(cls) if cls.startswith("FDS-") else FDSClass.UNKNOWN).retention_link
    policy = _FINANCIAL_RETENTION.get(link)
    if policy:
        return {"policy_key": link, "policy_version": POLICY_VERSION, **policy}
    return {
        "policy_key": "unclassified_hold",
        "policy_version": POLICY_VERSION,
        "retention_days": 30,
        "deletion_method": "DELETE",
        "verification": "manual_review_required",
    }


def reject_indefinite_retention(policy: dict[str, Any]) -> bool:
    days = policy.get("retention_days")
    if days is None:
        return False
    if int(days) < 0:
        return False
    max_days = policy.get("max_retention_days")
    if max_days is not None and int(max_days) < 0:
        return False
    if int(days) == 0 and policy.get("deletion_method") not in {
        "ZERO_RETENTION",
        "CRYPTO_ERASE",
        "REVOKE",
        "TOKEN_REVOKE",
    }:
        if policy.get("retention_note"):
            return True
        return False
    return True


def all_fds_classes_have_policy() -> bool:
    for cls in (FDSClass.C3_BANKING, FDSClass.C4_SECRET, FDSClass.C5_SENSITIVE_FINANCIAL, FDSClass.C6_PAYMENT_REFERENCE):
        policy = retention_for_class(cls)
        if policy.get("policy_key") == "unclassified_hold":
            return False
        if not reject_indefinite_retention(policy):
            return False
    return True
