"""Provenance and lineage assembly — unifies runtime + v4_v2 registries."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from data_governance.raw_landing import hash_raw


def build_lineage(
    *,
    decision_id: str | None = None,
    sources: list[str] | None = None,
    raw_refs: list[str] | None = None,
    normalization_version: str | None = None,
    methodology_versions: dict[str, str] | None = None,
) -> dict[str, Any]:
    lineage_id = f"lin_{uuid4().hex[:12]}"
    graph = {
        "lineage_id": lineage_id,
        "decision_id": decision_id,
        "nodes": [
            {"type": "source", "ids": sources or []},
            {"type": "raw", "refs": raw_refs or []},
            {"type": "normalization", "version": normalization_version},
            {"type": "methodology", "versions": methodology_versions or {}},
        ],
    }
    try:
        from bd_platform.v4_v2_persistent_registries import register_lineage

        register_lineage(
            entity_type="decision",
            entity_id=decision_id or lineage_id,
            version="v1",
            provenance_module="data_governance/provenance.py",
            meta=graph,
        )
    except Exception:
        pass
    return graph


def attach_provenance(payload: dict[str, Any], *, symbol: str = "BTC") -> dict[str, Any]:
    out = dict(payload)
    try:
        from data_provenance_score import attach_provenance as attach_score

        out = attach_score(out)
    except Exception:
        pass
    sources = out.get("sources") or ["live_book", "oracle"]
    raw_hash = hash_raw(out.get("_source_native") or {k: v for k, v in out.items() if k != "data_governance"})
    lineage = build_lineage(
        decision_id=str(out.get("decision_id") or out.get("prediction_id") or ""),
        sources=list(sources) if isinstance(sources, list) else [str(sources)],
        raw_refs=[raw_hash],
        normalization_version=out.get("normalization_version"),
        methodology_versions=(out.get("decision_truth") or {}).get("contract", {}).get("methodology_versions"),
    )
    out["data_governance_provenance"] = {
        "lineage": lineage,
        "raw_payload_hash": raw_hash,
        "provenance_score": (out.get("data_provenance") or {}).get("score") or out.get("provenance_score"),
        "traceable": True,
    }
    return out
