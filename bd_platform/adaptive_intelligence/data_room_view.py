"""Institutional Data Room — views over existing SSOT, no parallel registries (spec §19, AIE-019)."""

from __future__ import annotations

from typing import Any


def data_room_manifest() -> dict[str, Any]:
    return {
        "views": [
            "capability",
            "data_source",
            "lineage",
            "model_or_rule",
            "methodology",
            "api",
            "evidence",
            "version",
            "freshness_quality",
            "reliability",
            "security_controls",
            "audit",
            "limitations",
            "change_history",
        ],
        "ssot_sources": [
            "cap646/catalog.py",
            "decision_truth/pipeline.py",
            "blackdark/data_governance/runtime.py",
            "cap646/evidence_class.py",
        ],
        "parallel_registry_forbidden": True,
    }


def capability_data_room_view(capability_id: int) -> dict[str, Any]:
    from cap646.catalog import catalog_by_id

    row = catalog_by_id().get(int(capability_id))
    if not row:
        return {"ok": False, "error": "capability_not_found", "capability_id": capability_id}
    return {
        "ok": True,
        "capability_id": capability_id,
        "capability": row.get("capability"),
        "lineage": {"source": "cap646", "catalog_id": capability_id},
        "methodology": row.get("methodology") or "see_cap646_catalog",
        "limitations": row.get("limitations") or [],
        "evidence_class_binding": "cap646/evidence_class.py",
        "freshness_quality": {"coverage": row.get("coverage") or "partial"},
        "security_controls": ["entitlement_engine", "data_governance_runtime"],
        "audit": {"registry": "cap646/catalog.py"},
        "change_history": row.get("change_history") or [],
        "ssot_only": True,
    }
