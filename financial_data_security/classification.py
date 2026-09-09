"""Financial data classification — FDS-C1 through FDS-C6."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

FORBIDDEN_STORAGE_FIELDS = frozenset(
    {
        "pan",
        "card_number",
        "cardnumber",
        "cvv",
        "cvc",
        "cvc2",
        "cvv2",
        "pin",
        "track_data",
        "track1",
        "track2",
        "magnetic_stripe",
        "full_magnetic_stripe",
        "sad",
        "sensitive_authentication_data",
    }
)

ALLOWED_PAYMENT_REFERENCE_FIELDS = frozenset(
    {
        "provider_customer_id",
        "stripe_customer_id",
        "payment_method_id",
        "subscription_id",
        "payment_intent_id",
        "invoice_id",
        "card_brand",
        "card_last4",
        "card_exp_month",
        "card_exp_year",
    }
)


class FinancialDataClass(StrEnum):
    C1_RESTRICTED_PAYMENT_AUTH = "FDS-C1"
    C2_RESTRICTED_CARD = "FDS-C2"
    C3_RESTRICTED_BANKING = "FDS-C3"
    C4_FINANCIAL_SECRETS = "FDS-C4"
    C5_SENSITIVE_FINANCIAL = "FDS-C5"
    C6_PAYMENT_REFERENCES = "FDS-C6"


CLASSIFICATION_REGISTRY: dict[str, dict[str, Any]] = {
    FinancialDataClass.C1_RESTRICTED_PAYMENT_AUTH.value: {
        "policy": "NEVER_STORE_LOG_CACHE_BACKUP_AI",
        "examples": ["cvv", "cvc", "pin", "track_data"],
    },
    FinancialDataClass.C2_RESTRICTED_CARD.value: {
        "policy": "NO_BACKEND_PAN_WHERE_HOSTED_AVAILABLE",
        "examples": ["full_pan", "card_number"],
    },
    FinancialDataClass.C3_RESTRICTED_BANKING.value: {
        "policy": "TOKENIZED_PROVIDER_PREFERRED",
        "examples": ["iban", "routing_number", "account_number"],
    },
    FinancialDataClass.C4_FINANCIAL_SECRETS.value: {
        "policy": "SECRET_MANAGER_ONLY",
        "examples": ["stripe_secret", "webhook_secret", "api_secret"],
    },
    FinancialDataClass.C5_SENSITIVE_FINANCIAL.value: {
        "policy": "ENCRYPT_NEED_TO_KNOW_AUDIT",
        "examples": ["balance", "transaction", "portfolio"],
    },
    FinancialDataClass.C6_PAYMENT_REFERENCES.value: {
        "policy": "ALLOWED_OPERATIONAL_REFERENCES",
        "examples": list(ALLOWED_PAYMENT_REFERENCE_FIELDS),
    },
}


def classification_status() -> dict[str, Any]:
    return {"classes": list(CLASSIFICATION_REGISTRY.keys()), "count": len(CLASSIFICATION_REGISTRY)}
