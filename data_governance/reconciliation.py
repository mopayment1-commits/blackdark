"""Cross-source reconciliation and divergence detection."""

from __future__ import annotations

from typing import Any


def detect_divergence(
    *,
    primary_value: float | None,
    secondary_value: float | None,
    threshold_pct: float = 0.5,
) -> dict[str, Any]:
    if primary_value is None or secondary_value is None:
        return {"conflict": False, "reason": "insufficient_sources", "canonical_value": primary_value or secondary_value}
    if primary_value == 0:
        return {"conflict": False, "canonical_value": primary_value, "method": "primary_authoritative"}
    pct = abs(primary_value - secondary_value) / abs(primary_value) * 100.0
    conflict = pct > threshold_pct
    return {
        "conflict": conflict,
        "divergence_pct": round(pct, 4),
        "primary_value": primary_value,
        "secondary_value": secondary_value,
        "canonical_value": primary_value if not conflict else None,
        "method": "primary_authoritative" if not conflict else "conflict_recorded",
        "resolution": "preserve_competing_values" if conflict else "primary_selected",
    }


def reconcile_observations(
    observations: list[dict[str, Any]],
    *,
    threshold_pct: float = 5.0,
    max_relative_diff: float | None = None,
) -> dict[str, Any]:
    if max_relative_diff is not None:
        threshold_pct = max_relative_diff * 100.0
    """RESTORE-004/005 canonical reconciliation between source observations."""
    if not observations:
        return {"state": "INSUFFICIENT", "method": "none", "values": []}
    if len(observations) == 1:
        return {
            "state": "SINGLE_SOURCE",
            "method": "single_source_penalty",
            "canonical_value": observations[0].get("value"),
            "sources": [observations[0].get("source_id")],
            "confidence_penalty": True,
        }
    values = [float(o["value"]) for o in observations if o.get("value") is not None]
    if len(values) < 2:
        return {"state": "INSUFFICIENT", "method": "missing_values"}
    primary, secondary = values[0], values[1]
    div = detect_divergence(primary_value=primary, secondary_value=secondary, threshold_pct=threshold_pct)
    if div.get("conflict"):
        return {
            "state": "CONFLICT",
            "method": "quarantine_no_average",
            "canonical_value": None,
            "conflicting_sources": [observations[0].get("source_id"), observations[1].get("source_id")],
            "divergence_pct": div.get("divergence_pct"),
        }
    return {
        "state": "CONSENSUS",
        "method": "primary_authoritative",
        "canonical_value": div.get("canonical_value"),
        "sources": [o.get("source_id") for o in observations],
    }


def reconcile_prices(payload: dict[str, Any]) -> dict[str, Any]:
    out = dict(payload)
    primary = out.get("price") or out.get("mid_price")
    secondary = out.get("secondary_price") or out.get("reference_price")
    div = detect_divergence(
        primary_value=float(primary) if primary is not None else None,
        secondary_value=float(secondary) if secondary is not None else None,
    )
    out["reconciliation"] = div
    if div.get("conflict"):
        out["source_conflict"] = True
        out.setdefault("dimension_conflict", {})["veto"] = True
    return out
