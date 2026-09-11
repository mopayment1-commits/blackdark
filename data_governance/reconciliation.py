"""Cross-source reconciliation (RESTORE-004/005)."""

from __future__ import annotations

from typing import Any


def reconcile_observations(observations: list[dict[str, Any]], *, max_relative_diff: float = 0.05) -> dict[str, Any]:
    """Reconcile multi-source values; never silently average conflicting critical evidence."""
    if not observations:
        return {"state": "UNAVAILABLE", "reason": "no_observations", "canonical_value": None}

    usable = [o for o in observations if o.get("value") is not None]
    if not usable:
        return {"state": "UNAVAILABLE", "reason": "no_values", "canonical_value": None}

    if len(usable) == 1:
        o = usable[0]
        return {
            "state": "SINGLE_SOURCE",
            "canonical_value": o.get("value"),
            "confidence_penalty": True,
            "sources": [o.get("source_id")],
            "observations": usable,
        }

    values = [float(o["value"]) for o in usable]
    baseline = values[0]
    for v in values[1:]:
        if baseline == 0:
            rel = abs(v)
        else:
            rel = abs(v - baseline) / abs(baseline)
        if rel > max_relative_diff:
            return {
                "state": "CONFLICT",
                "reason": "material_disagreement",
                "canonical_value": None,
                "observations": usable,
                "relative_diff": rel,
            }

    consensus = sum(values) / len(values)
    return {
        "state": "CONSENSUS",
        "canonical_value": consensus,
        "observations": usable,
        "method": "agreement_within_threshold",
    }
