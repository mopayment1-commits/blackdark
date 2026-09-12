"""Collection policies — DSR-023."""

from __future__ import annotations

import json
from typing import Any

from blackdark.data_governance._paths import COLLECTION_POLICY_PATH, ensure_governance_dirs

COLLECTION_POLICIES: dict[str, dict[str, Any]] = {
    "market_ohlcv": {
        "collection_id": "market_ohlcv",
        "purpose": "Decision-grade market history for intelligence engines",
        "legal_basis": "legitimate_interest_b2b_saas",
        "minimization": "symbols_in_universe_only",
        "retention_class": "rc_operational_hot",
        "deletion_policy": "tier_migration_then_archive",
        "rights_profile_id": "rp_market_data_derived",
    },
    "user_exposure": {
        "collection_id": "user_exposure",
        "purpose": "Link user-facing decisions to outcomes for calibration",
        "legal_basis": "contract_performance",
        "minimization": "no_pii_beyond_user_id_tier",
        "retention_class": "rc_user_telemetry",
        "deletion_policy": "delete_on_request_or_expiry",
        "rights_profile_id": "rp_user_telemetry_minimized",
    },
    "shadow_forward_record": {
        "collection_id": "shadow_forward_record",
        "purpose": "Pre-launch forward track record accumulation",
        "legal_basis": "product_development",
        "minimization": "market_and_system_signals_only",
        "retention_class": "rc_evidence_archive",
        "deletion_policy": "retain_for_dd",
        "rights_profile_id": "rp_proprietary_internal",
    },
}


def ensure_collection_policies() -> dict[str, Any]:
    ensure_governance_dirs()
    if not COLLECTION_POLICY_PATH.exists():
        COLLECTION_POLICY_PATH.write_text(json.dumps({"policies": COLLECTION_POLICIES}, indent=2), encoding="utf-8")
    return json.loads(COLLECTION_POLICY_PATH.read_text(encoding="utf-8"))
