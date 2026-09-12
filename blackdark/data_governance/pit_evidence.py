"""Point-in-Time Evidence Contracts — DSR-003, DSR-004, D-02."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from blackdark.data_governance._paths import PIT_DIR, ensure_governance_dirs


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _hash_obj(obj: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()


def create_pit_contract(
    *,
    replay_id: str,
    knowledge_cutoff: str,
    event_time_field: str = "event_time",
    ingest_time_field: str = "ingest_time",
    universe_snapshot_id: str | None = None,
    revision_policy: str = "as_available_at_cutoff",
    data_snapshot_hash: str | None = None,
    code_sha: str | None = None,
    model_version: str | None = None,
    config_version: str | None = None,
    oracle: str | None = None,
    horizon: str | None = None,
    survivorship_controls: dict[str, Any] | None = None,
    reconstructed_with_later_data: bool = False,
) -> dict[str, Any]:
    """Create PIT evidence contract preventing look-ahead/revision leakage."""
    ensure_governance_dirs()
    contract = {
        "pit_id": f"pit_{uuid4().hex[:12]}",
        "replay_id": replay_id,
        "knowledge_cutoff": knowledge_cutoff,
        "event_time_field": event_time_field,
        "ingest_time_field": ingest_time_field,
        "universe_snapshot_id": universe_snapshot_id,
        "revision_policy": revision_policy,
        "data_snapshot_hash": data_snapshot_hash,
        "code_sha": code_sha,
        "model_version": model_version,
        "config_version": config_version,
        "oracle": oracle,
        "horizon": horizon,
        "survivorship_controls": survivorship_controls or {"no_winner_only": True},
        "reconstructed_with_later_data": reconstructed_with_later_data,
        "integrity_label": (
            "reconstructed-with-later-data"
            if reconstructed_with_later_data
            else "point-in-time-faithful"
        ),
        "created_at": _utcnow(),
    }
    contract["contract_hash"] = _hash_obj(contract)
    path = PIT_DIR / f"{contract['pit_id']}.json"
    path.write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return contract


def validate_pit_framing(*, is_replay: bool, claim_text: str) -> tuple[bool, str]:
    """§8 integrity: replay discoveries must not be labeled as real-time predictions."""
    forbidden = ("real-time prediction", "predicted at the time", "issued live at event")
    lower = claim_text.lower()
    if is_replay and any(f in lower for f in forbidden):
        return False, "replay_labeled_as_live_prediction"
    if is_replay and "successfully detected the historical event under point-in-time replay" not in lower:
        return True, "acceptable_if_not_claiming_live"
    return True, "ok"


def load_pit_contract(pit_id: str) -> dict[str, Any] | None:
    path = PIT_DIR / f"{pit_id}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return None
