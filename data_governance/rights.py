"""Licensing and redistribution rights — delegates to v4_v2 source rights registry."""

from __future__ import annotations

from typing import Any

from bd_platform.v4_v2_persistent_registries import enforce_source_rights, register_source_rights


def ensure_source_rights(source_id: str, *, operation: str = "display") -> dict[str, Any]:
    result = enforce_source_rights(source_id=source_id, operation=operation)
    if not result.get("allowed") and result.get("reason") == "missing_rights_profile":
        register_source_rights(
            source_id=source_id,
            license_class="internal_analysis_only",
            redistribution=False,
            meta={"auto_seeded": True, "commercial_use": "review_required"},
        )
        result = enforce_source_rights(source_id=source_id, operation=operation)
    return result


def rights_matrix(source_ids: list[str] | None = None) -> dict[str, Any]:
    from data_governance.registry import critical_sources

    ids = source_ids or [s.source_id for s in critical_sources()]
    return {"entries": [{**ensure_source_rights(sid), "source_id": sid} for sid in ids]}
