"""Adaptive attack-surface security controls and threat-model delta (spec §15/§31)."""

from __future__ import annotations

import re
from typing import Any

_THREAT_DELTA = {
    "new_api_entry_points": ["/api/adaptive/*"],
    "new_persistence": ["data/adaptive_human_validation.jsonl", "data/mirror_ledger.jsonl"],
    "sensitive_data_flows": ["mirror_ledger_user_stance", "human_validation_metrics"],
    "trust_boundaries": ["adaptive_router → cap646_entitlements", "adaptive_router → decision_truth"],
}


def validate_adaptive_input(body: dict[str, Any]) -> dict[str, Any]:
    """Input validation for adaptive API payloads."""
    errors: list[str] = []
    for key in ("query", "intent_id", "asset", "horizon", "decision_type"):
        val = body.get(key)
        if val is not None and not isinstance(val, str):
            errors.append(f"{key}_must_be_string")
        if isinstance(val, str) and len(val) > 2000:
            errors.append(f"{key}_too_long")
        if isinstance(val, str) and re.search(r"[<>\"']", val):
            errors.append(f"{key}_invalid_chars")
    user_id = body.get("user_id")
    if user_id is not None:
        if not isinstance(user_id, str) or not re.match(r"^[a-zA-Z0-9_-]{1,64}$", user_id):
            errors.append("user_id_invalid")
    return {"ok": not errors, "errors": errors}


def threat_model_delta() -> dict[str, Any]:
    return {
        "delta": _THREAT_DELTA,
        "fail_closed_surfaces": ["safety_floor", "entitlement_denied", "invalid_input"],
        "certification_claimed": False,
    }
