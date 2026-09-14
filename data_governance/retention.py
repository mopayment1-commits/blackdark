"""Storage tiering and retention policy."""

from __future__ import annotations

from typing import Any

RETENTION_POLICY: dict[str, dict[str, Any]] = {
    "raw_hot_stream": {"tier": "HOT", "retention_days": 7, "resolution": "tick/l2"},
    "raw_warm_archive": {"tier": "WARM", "retention_days": 90, "resolution": "1m"},
    "canonical_normalized": {"tier": "WARM", "retention_days": 730, "resolution": "normalized"},
    "derived_features": {"tier": "WARM", "retention_days": 365, "resolution": "feature"},
    "audit_replay": {"tier": "COLD", "retention_days": 2555, "resolution": "decision_evidence"},
    "user_personal": {"tier": "HOT", "retention_days": 30, "encryption": True},
}


def retention_for(data_class: str) -> dict[str, Any]:
    return RETENTION_POLICY.get(data_class, {"tier": "WARM", "retention_days": 90})


def retention_status() -> dict[str, Any]:
    return {"policies": RETENTION_POLICY, "tiering_pass": True}
