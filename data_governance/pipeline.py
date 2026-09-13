"""Material write pipeline — orchestrates DIG controls (DIG-053/055/057/058/060)."""

from __future__ import annotations

from typing import Any

_PIPELINE_ENABLED = True


def pipeline_enabled() -> bool:
    return _PIPELINE_ENABLED


def run_material_pipeline(surface: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Fail-closed pipeline for material intelligence writes."""
    from data_governance.gates import evaluate_material_gates
    from data_governance.normalization import normalize_payload
    from data_governance.observability import emit_governance_event
    from data_governance.provenance import attach_provenance
    from data_governance.quality import score_quality
    from data_governance.raw_landing import record_raw_landing
    from data_governance.reliability import assert_source_reliability
    from data_governance.retention import apply_retention_class
    from data_governance.schema_evolution import validate_schema_version
    from data_governance.timestamps import ensure_canonical_timestamps

    out = dict(payload)
    out = ensure_canonical_timestamps(out)
    out = normalize_payload(out, surface=surface)
    validate_schema_version(out, surface=surface)
    out = attach_provenance(out, surface=surface)
    out = apply_retention_class(out, surface=surface)
    assert_source_reliability(out)
    quality = score_quality(out)
    out["data_quality_score"] = quality["score"]
    gate = evaluate_material_gates(surface, out, quality_score=quality["score"])
    if not gate["allowed"]:
        from blackdark.data_governance.runtime import GovernanceViolationError

        raise GovernanceViolationError(f"pipeline_gate_denied:{','.join(gate['reasons'])}")
    record_raw_landing(out, surface=surface)
    emit_governance_event(surface, out)
    out["pipeline_enforced"] = True
    return out
