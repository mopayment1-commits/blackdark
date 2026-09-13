"""v4_v2 persistent registries — lineage, source rights, PIT availability (JSONL spine)."""

from __future__ import annotations

import json
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

_DATA = Path("data")
_LOCK = threading.Lock()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")


def _read_jsonl(path: Path, *, limit: int = 500) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines()[-limit:]:
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


# --- Dataset / model / rule lineage ---

_LINEAGE_PATH = _DATA / "v4_v2_lineage_registry.jsonl"


def register_lineage(
    *,
    entity_type: str,
    entity_id: str,
    parent_id: str | None = None,
    version: str = "v1",
    provenance_module: str | None = None,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "lineage_id": f"lin_{uuid4().hex[:16]}",
        "entity_type": entity_type,
        "entity_id": entity_id,
        "parent_id": parent_id,
        "version": version,
        "provenance_module": provenance_module,
        "meta": meta or {},
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append_jsonl(_LINEAGE_PATH, row)
    return row


def resolve_lineage(*, entity_type: str, entity_id: str) -> list[dict[str, Any]]:
    return [
        r
        for r in _read_jsonl(_LINEAGE_PATH, limit=2000)
        if r.get("entity_type") == entity_type and r.get("entity_id") == entity_id
    ]


def lineage_registry_status() -> dict[str, Any]:
    rows = _read_jsonl(_LINEAGE_PATH, limit=2000)
    return {"registry": "v4_v2_lineage", "row_count": len(rows), "store": str(_LINEAGE_PATH)}


# --- Source rights ---

_RIGHTS_PATH = _DATA / "v4_v2_source_rights_registry.jsonl"


def register_source_rights(
    *,
    source_id: str,
    license_class: str = "internal_analysis_only",
    retention_days: int = 90,
    redistribution: bool = False,
    training_allowed: bool = False,
    resale_allowed: bool = False,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "rights_id": f"rights_{uuid4().hex[:12]}",
        "source_id": source_id,
        "license_class": license_class,
        "retention_days": retention_days,
        "redistribution": redistribution,
        "training_allowed": training_allowed,
        "resale_allowed": resale_allowed,
        "enforced": True,
        "meta": meta or {},
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append_jsonl(_RIGHTS_PATH, row)
    return row


def enforce_source_rights(*, source_id: str, operation: str) -> dict[str, Any]:
    rows = [r for r in _read_jsonl(_RIGHTS_PATH, limit=2000) if r.get("source_id") == source_id]
    profile = rows[-1] if rows else None
    if profile is None:
        return {"allowed": False, "reason": "missing_rights_profile", "source_id": source_id, "operation": operation}
    blocked_ops = {
        "redistribute": profile.get("redistribution") is False,
        "train": profile.get("training_allowed") is False,
        "resale": profile.get("resale_allowed") is False,
    }
    if operation in blocked_ops and blocked_ops[operation]:
        return {"allowed": False, "reason": f"{operation}_blocked", "profile": profile}
    return {"allowed": True, "profile": profile, "operation": operation}


def source_rights_registry_status() -> dict[str, Any]:
    rows = _read_jsonl(_RIGHTS_PATH, limit=2000)
    return {"registry": "v4_v2_source_rights", "row_count": len(rows), "store": str(_RIGHTS_PATH)}


# --- PIT availability index ---

_PIT_PATH = _DATA / "v4_v2_pit_availability_index.jsonl"


def register_pit_availability(
    *,
    dataset_id: str,
    event_time: str,
    observed_time: str,
    available_time: str,
    as_of_cutoff: str,
    meta: dict[str, Any] | None = None,
) -> dict[str, Any]:
    row = {
        "pit_id": f"pit_{uuid4().hex[:12]}",
        "dataset_id": dataset_id,
        "event_time": event_time,
        "observed_time": observed_time,
        "available_time": available_time,
        "as_of_cutoff": as_of_cutoff,
        "meta": meta or {},
        "registered_at": _utcnow(),
    }
    with _LOCK:
        _append_jsonl(_PIT_PATH, row)
    return row


def query_pit_available(*, dataset_id: str, as_of: str) -> list[dict[str, Any]]:
    from temporal_leakage_firewall import filter_point_in_time

    rows = [r for r in _read_jsonl(_PIT_PATH, limit=5000) if r.get("dataset_id") == dataset_id]
    return filter_point_in_time(rows, cutoff=as_of, time_field="available_time")


def pit_registry_status() -> dict[str, Any]:
    rows = _read_jsonl(_PIT_PATH, limit=5000)
    return {"registry": "v4_v2_pit_availability", "row_count": len(rows), "store": str(_PIT_PATH)}


def bootstrap_default_registries() -> dict[str, Any]:
    """Ensure institutional seed profiles exist for closure verification."""
    rights = enforce_source_rights(source_id="institutional_seed", operation="read")
    if not rights.get("allowed"):
        register_source_rights(source_id="institutional_seed")
    lineage = resolve_lineage(entity_type="dataset", entity_id="institutional_seed")
    if not lineage:
        register_lineage(entity_type="dataset", entity_id="institutional_seed", version="v4_v2_seed")
    pit_rows = query_pit_available(dataset_id="institutional_seed", as_of="2099-01-01T00:00:00+00:00")
    if not pit_rows:
        register_pit_availability(
            dataset_id="institutional_seed",
            event_time="2026-01-01T00:00:00+00:00",
            observed_time="2026-01-01T00:01:00+00:00",
            available_time="2026-01-01T00:01:00+00:00",
            as_of_cutoff="2026-01-02T00:00:00+00:00",
        )
    return {
        "lineage": lineage_registry_status(),
        "source_rights": source_rights_registry_status(),
        "pit": pit_registry_status(),
    }
