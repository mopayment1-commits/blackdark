"""Schema registry — DSR-006, D-03."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

from blackdark.data_governance._paths import SCHEMA_DIR, ensure_governance_dirs

SCHEMA_REGISTRY: dict[str, dict[str, Any]] = {
    "signal_registry": {
        "schema_id": "signal_registry",
        "current_version": "1.0.0",
        "compatibility": "backward",
        "required_fields": ["signal_id", "signal_type", "evidence_class"],
        "migration_policy": "append_new_fields_only",
    },
    "decision_ledger": {
        "schema_id": "decision_ledger",
        "current_version": "1.0.0",
        "compatibility": "backward",
        "required_fields": ["decision_id", "prediction_id", "decision_action", "evidence_class"],
        "migration_policy": "append_new_fields_only",
    },
    "oracle_audit_chain": {
        "schema_id": "oracle_audit_chain",
        "current_version": "1.0.0",
        "compatibility": "strict",
        "required_fields": ["chain_hash", "prev_hash"],
        "migration_policy": "version_bump_with_migration_record",
    },
}


def ensure_schema_registry() -> None:
    ensure_governance_dirs()
    for sid, schema in SCHEMA_REGISTRY.items():
        path = SCHEMA_DIR / f"{sid}.json"
        if not path.exists():
            payload = dict(schema)
            payload["registered_at"] = datetime.now(UTC).isoformat()
            path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def get_schema(schema_id: str) -> dict[str, Any] | None:
    ensure_schema_registry()
    path = SCHEMA_DIR / f"{schema_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return SCHEMA_REGISTRY.get(schema_id)


def validate_record_against_schema(schema_id: str, record: dict[str, Any]) -> tuple[bool, list[str]]:
    schema = get_schema(schema_id)
    if not schema:
        return False, [f"unknown_schema:{schema_id}"]
    missing = [f for f in schema.get("required_fields", []) if f not in record]
    return len(missing) == 0, missing
