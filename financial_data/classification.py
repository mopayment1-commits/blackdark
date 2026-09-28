"""Canonical FDS-C1..C6 financial data classification (runtime authority)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

CLASS_POLICY_VERSION = "fds-c-v1.0.0"


class FDSClass(str, Enum):
    C1_SAD = "FDS-C1"
    C2_PAN = "FDS-C2"
    C3_BANKING = "FDS-C3"
    C4_SECRET = "FDS-C4"
    C5_SENSITIVE_FINANCIAL = "FDS-C5"
    C6_PAYMENT_REFERENCE = "FDS-C6"
    UNKNOWN = "UNKNOWN"


class Sensitivity(str, Enum):
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"
    INTERNAL = "internal"


@dataclass(frozen=True)
class ClassPolicy:
    classification: FDSClass
    sensitivity: Sensitivity
    allowed_purposes: frozenset[str]
    prohibited_sinks: frozenset[str]
    logging_policy: str
    analytics_policy: str
    ai_llm_policy: str
    storage_policy: str
    retention_link: str
    masking_required: bool
    reason: str


_CLASS_POLICIES: dict[FDSClass, ClassPolicy] = {
    FDSClass.C1_SAD: ClassPolicy(
        classification=FDSClass.C1_SAD,
        sensitivity=Sensitivity.RESTRICTED,
        allowed_purposes=frozenset(),
        prohibited_sinks=frozenset({"logs", "analytics", "ai_llm", "support_export", "storage", "backups", "cache"}),
        logging_policy="deny",
        analytics_policy="deny",
        ai_llm_policy="deny",
        storage_policy="never_store",
        retention_link="zero_retention",
        masking_required=True,
        reason="CVV/CVC/PIN/track/SAD must never persist or leave PSP boundary",
    ),
    FDSClass.C2_PAN: ClassPolicy(
        classification=FDSClass.C2_PAN,
        sensitivity=Sensitivity.RESTRICTED,
        allowed_purposes=frozenset(),
        prohibited_sinks=frozenset({"logs", "analytics", "ai_llm", "support_export", "storage", "backups"}),
        logging_policy="deny",
        analytics_policy="deny",
        ai_llm_policy="deny",
        storage_policy="never_store",
        retention_link="zero_retention",
        masking_required=True,
        reason="Full PAN must not enter BLACKDARK backend where hosted collection exists",
    ),
    FDSClass.C3_BANKING: ClassPolicy(
        classification=FDSClass.C3_BANKING,
        sensitivity=Sensitivity.RESTRICTED,
        allowed_purposes=frozenset({"tokenized_reference_only"}),
        prohibited_sinks=frozenset({"logs", "analytics", "ai_llm", "support_export"}),
        logging_policy="mask",
        analytics_policy="deny",
        ai_llm_policy="deny",
        storage_policy="tokenized_only",
        retention_link="financial_credentials",
        masking_required=True,
        reason="Bank account/routing credentials require provider tokenization",
    ),
    FDSClass.C4_SECRET: ClassPolicy(
        classification=FDSClass.C4_SECRET,
        sensitivity=Sensitivity.RESTRICTED,
        allowed_purposes=frozenset({"runtime_secret_use"}),
        prohibited_sinks=frozenset({"logs", "analytics", "ai_llm", "support_export", "source_code", "client"}),
        logging_policy="deny",
        analytics_policy="deny",
        ai_llm_policy="deny",
        storage_policy="encrypted_secret_manager",
        retention_link="credential_rotation",
        masking_required=True,
        reason="Financial/API secrets must never appear in logs, code, or browser",
    ),
    FDSClass.C5_SENSITIVE_FINANCIAL: ClassPolicy(
        classification=FDSClass.C5_SENSITIVE_FINANCIAL,
        sensitivity=Sensitivity.CONFIDENTIAL,
        allowed_purposes=frozenset({"authorized_operations", "minimized_analytics"}),
        prohibited_sinks=frozenset({"ai_llm", "public_export"}),
        logging_policy="mask",
        analytics_policy="minimize",
        ai_llm_policy="deny",
        storage_policy="encrypted_at_rest",
        retention_link="user_personal",
        masking_required=True,
        reason="Balances/transactions/metadata need need-to-know access",
    ),
    FDSClass.C6_PAYMENT_REFERENCE: ClassPolicy(
        classification=FDSClass.C6_PAYMENT_REFERENCE,
        sensitivity=Sensitivity.CONFIDENTIAL,
        allowed_purposes=frozenset({"billing_operations", "support_with_auth"}),
        prohibited_sinks=frozenset({"ai_llm", "public_export"}),
        logging_policy="mask",
        analytics_policy="aggregate_only",
        ai_llm_policy="deny",
        storage_policy="allowed_encrypted",
        retention_link="payment_references",
        masking_required=True,
        reason="Provider IDs allowed when operationally necessary",
    ),
    FDSClass.UNKNOWN: ClassPolicy(
        classification=FDSClass.UNKNOWN,
        sensitivity=Sensitivity.RESTRICTED,
        allowed_purposes=frozenset(),
        prohibited_sinks=frozenset({"logs", "analytics", "ai_llm", "support_export", "storage"}),
        logging_policy="deny",
        analytics_policy="deny",
        ai_llm_policy="deny",
        storage_policy="deny_until_classified",
        retention_link="unclassified_hold",
        masking_required=True,
        reason="Unclassified financial-sensitive input fails closed",
    ),
}

_FIELD_HINTS: dict[FDSClass, tuple[str, ...]] = {
    FDSClass.C1_SAD: ("cvv", "cvc", "pin", "track_data", "magnetic_stripe", "sad", "sensitive_auth"),
    FDSClass.C2_PAN: ("pan", "card_number", "primary_account_number", "full_card"),
    FDSClass.C3_BANKING: ("iban", "routing_number", "bank_account", "account_number", "swift"),
    FDSClass.C4_SECRET: (
        "api_key",
        "secret_key",
        "webhook_secret",
        "stripe_secret",
        "refresh_token",
        "private_key",
        "bearer_token",
        "password",
        "dsn",
    ),
    FDSClass.C5_SENSITIVE_FINANCIAL: (
        "balance",
        "transaction",
        "portfolio_value",
        "pnl",
        "budget_usd",
        "amount_usd",
    ),
    FDSClass.C6_PAYMENT_REFERENCE: (
        "stripe_customer_id",
        "customer_id",
        "payment_method_id",
        "subscription_id",
        "payment_intent_id",
        "provider_subscription_id",
        "provider_customer_id",
    ),
}

_PAN_RE = re.compile(r"\b(?:\d[ -]*?){13,19}\b")
_CVV_RE = re.compile(r"(?i)\b(?:cvv|cvc|pin)\b[^0-9]{0,8}(\d{3,4})\b")
_SECRET_RE = re.compile(
    r"(?i)(sk_live_[a-zA-Z0-9]{10,}|sk_test_[a-zA-Z0-9]{10,}|"
    r"AKIA[0-9A-Z]{16}|whsec_[a-zA-Z0-9]+|"
    r"postgres(ql)?://[^\s]+|redis://[^\s]+)"
)
_IBAN_RE = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")


def class_definition(cls: FDSClass) -> ClassPolicy:
    return _CLASS_POLICIES[cls]


def _normalize_field(name: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", "_", (name or "").strip().lower())


def _digits_only(text: str) -> str:
    return re.sub(r"\D", "", text)


def luhn_valid(number: str) -> bool:
    digits = _digits_only(number)
    if len(digits) < 13 or len(digits) > 19:
        return False
    total = 0
    reverse = digits[::-1]
    for i, ch in enumerate(reverse):
        n = int(ch)
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


def _classify_by_field_name(field_name: str | None) -> FDSClass | None:
    norm = _normalize_field(field_name)
    if not norm:
        return None
    for cls, hints in _FIELD_HINTS.items():
        if any(h in norm for h in hints):
            return cls
    if norm.endswith("_id") and any(x in norm for x in ("stripe", "subscription", "payment", "customer")):
        return FDSClass.C6_PAYMENT_REFERENCE
    return None


def _classify_by_value(value: Any) -> FDSClass | None:
    if value is None or value == "":
        return None
    text = str(value)
    if _SECRET_RE.search(text):
        return FDSClass.C4_SECRET
    if _CVV_RE.search(text):
        return FDSClass.C1_SAD
    if _IBAN_RE.search(text):
        return FDSClass.C3_BANKING
    for match in _PAN_RE.finditer(text):
        candidate = _digits_only(match.group())
        if luhn_valid(candidate):
            return FDSClass.C2_PAN
    return None


def classify_field(field_name: str | None, value: Any) -> FDSClass | None:
    by_name = _classify_by_field_name(field_name)
    by_value = _classify_by_value(value)
    if by_name in {FDSClass.C1_SAD, FDSClass.C2_PAN, FDSClass.C3_BANKING, FDSClass.C4_SECRET}:
        return by_name
    if by_value in {FDSClass.C1_SAD, FDSClass.C2_PAN, FDSClass.C3_BANKING, FDSClass.C4_SECRET}:
        return by_value
    if by_name:
        return by_name
    if by_value:
        return by_value
    if field_name and value not in (None, ""):
        norm = _normalize_field(field_name)
        if any(tok in norm for tok in ("financial", "billing", "payment", "bank", "card", "secret")):
            return FDSClass.UNKNOWN
    return None


def classify_payload(payload: dict[str, Any] | None, *, prefix: str = "") -> dict[str, FDSClass]:
    out: dict[str, FDSClass] = {}
    if not isinstance(payload, dict):
        return out
    for key, value in payload.items():
        path = f"{prefix}.{key}" if prefix else str(key)
        if isinstance(value, dict):
            out.update(classify_payload(value, prefix=path))
            continue
        cls = classify_field(str(key), value)
        if cls is not None:
            out[path] = cls
    return out
