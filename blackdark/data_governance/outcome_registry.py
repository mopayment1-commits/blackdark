"""Outcome evaluator versioning — DSR-009, D-07."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from blackdark.data_governance._paths import OUTCOME_REGISTRY_PATH, ensure_governance_dirs

DEFAULT_OUTCOME_EVALUATORS = {
    "oracle_outcome_v1": {
        "evaluator_id": "oracle_outcome_v1",
        "version": "1.0.0",
        "definition": "Oracle prediction resolved against forward market move at horizon",
        "horizons": ["5m", "1h", "4h", "24h"],
        "correction_policy": "append_correction_record",
        "active": True,
        "registered_at": None,
    },
    "decision_outcome_v1": {
        "evaluator_id": "decision_outcome_v1",
        "version": "1.0.0",
        "definition": "Decision action evaluated against realized outcome at linked horizon",
        "horizons": ["1h", "24h"],
        "correction_policy": "append_correction_record",
        "active": True,
        "registered_at": None,
    },
}


def ensure_outcome_registry() -> dict[str, Any]:
    ensure_governance_dirs()
    if not OUTCOME_REGISTRY_PATH.exists():
        payload = {
            "registry_version": "1.0.0",
            "evaluators": {
                k: {**v, "registered_at": datetime.now(UTC).isoformat()}
                for k, v in DEFAULT_OUTCOME_EVALUATORS.items()
            },
        }
        OUTCOME_REGISTRY_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return json.loads(OUTCOME_REGISTRY_PATH.read_text(encoding="utf-8"))


def get_evaluator_version(evaluator_id: str) -> dict[str, Any] | None:
    reg = ensure_outcome_registry()
    return reg.get("evaluators", {}).get(evaluator_id)
