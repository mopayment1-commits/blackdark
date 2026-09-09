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
