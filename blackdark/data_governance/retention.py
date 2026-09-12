"""Retention classes and storage tiers — DSR-014, D-04, D-11, Table 17."""

from __future__ import annotations

import json
from typing import Any

from blackdark.data_governance._paths import RETENTION_PATH, ensure_governance_dirs

RETENTION_CLASSES: dict[str, dict[str, Any]] = {
    "rc_operational_hot": {
        "class_id": "rc_operational_hot",
        "tier": "HOT",
        "retention_days": 90,
        "deletion_behavior": "compact_to_warm",
        "legal_basis": "operational_necessity",
        "owner": "platform-ops",
    },
    "rc_operational_warm": {
        "class_id": "rc_operational_warm",
        "tier": "WARM",
        "retention_days": 365,
        "deletion_behavior": "archive_to_cold",
        "legal_basis": "business_analytics",
        "owner": "platform-intelligence",
    },
    "rc_evidence_archive": {
        "class_id": "rc_evidence_archive",
        "tier": "COLD",
        "retention_days": 2555,
        "deletion_behavior": "anonymize_after_expiry",
        "legal_basis": "audit_and_dd",
        "owner": "platform-trust",
    },
    "rc_user_telemetry": {
        "class_id": "rc_user_telemetry",
        "tier": "WARM",
        "retention_days": 365,
        "deletion_behavior": "delete_on_request_or_expiry",
        "legal_basis": "consent_and_minimization",
        "owner": "platform-privacy",
    },
}


def ensure_retention_registry() -> dict[str, Any]:
    ensure_governance_dirs()
    if not RETENTION_PATH.exists():
        RETENTION_PATH.write_text(json.dumps({"classes": RETENTION_CLASSES}, indent=2), encoding="utf-8")
    return json.loads(RETENTION_PATH.read_text(encoding="utf-8"))


def get_retention_class(class_id: str) -> dict[str, Any] | None:
    reg = ensure_retention_registry()
    return reg.get("classes", {}).get(class_id)
