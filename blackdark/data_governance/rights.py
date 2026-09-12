"""Rights Profiles — DSR-005, D-05."""

from __future__ import annotations

import json
from typing import Any

from blackdark.data_governance._paths import RIGHTS_DIR, ensure_governance_dirs

RIGHTS_PROFILES: dict[str, dict[str, Any]] = {
    "rp_proprietary_internal": {
        "profile_id": "rp_proprietary_internal",
        "storage_allowed": True,
        "derived_use_allowed": True,
        "training_allowed": True,
        "redistribution_allowed": False,
        "api_resale_allowed": False,
        "licensing_allowed": False,
        "retention_max_days": None,
        "enforcement": "block_export_without_profile",
    },
    "rp_market_data_derived": {
        "profile_id": "rp_market_data_derived",
        "storage_allowed": True,
        "derived_use_allowed": True,
        "training_allowed": True,
        "redistribution_allowed": False,
        "api_resale_allowed": False,
        "licensing_allowed": False,
        "retention_max_days": 3650,
        "enforcement": "block_export_without_profile",
        "license_note": "Derived from licensed market APIs — no permanent commercial dataset without contract",
    },
    "rp_user_telemetry_minimized": {
        "profile_id": "rp_user_telemetry_minimized",
        "storage_allowed": True,
        "derived_use_allowed": True,
        "training_allowed": False,
        "redistribution_allowed": False,
        "api_resale_allowed": False,
        "licensing_allowed": False,
        "retention_max_days": 365,
        "enforcement": "block_training_and_export",
        "minimization": True,
        "deletion_on_request": True,
    },
    "rp_do_not_use": {
        "profile_id": "rp_do_not_use",
        "storage_allowed": False,
        "derived_use_allowed": False,
        "training_allowed": False,
        "redistribution_allowed": False,
        "api_resale_allowed": False,
        "licensing_allowed": False,
        "enforcement": "hard_block_all_paths",
    },
}


def ensure_rights_materialized() -> None:
    ensure_governance_dirs()
    for pid, profile in RIGHTS_PROFILES.items():
        path = RIGHTS_DIR / f"{pid}.json"
        if not path.exists():
            path.write_text(json.dumps(profile, indent=2), encoding="utf-8")


def get_rights_profile(profile_id: str) -> dict[str, Any] | None:
    ensure_rights_materialized()
    path = RIGHTS_DIR / f"{profile_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return RIGHTS_PROFILES.get(profile_id)


def check_rights(profile_id: str, action: str) -> tuple[bool, str]:
    """Machine-enforceable rights check. Returns (allowed, reason)."""
    profile = get_rights_profile(profile_id)
    if not profile:
        return False, f"unknown_rights_profile:{profile_id}"
    mapping = {
        "storage": "storage_allowed",
        "derived_use": "derived_use_allowed",
        "training": "training_allowed",
        "redistribution": "redistribution_allowed",
        "api_resale": "api_resale_allowed",
        "licensing": "licensing_allowed",
        "export": "redistribution_allowed",
    }
    key = mapping.get(action)
    if not key:
        return False, f"unknown_action:{action}"
    allowed = bool(profile.get(key))
    if not allowed:
        return False, f"rights_denied:{profile_id}:{action}"
    return True, "ok"
