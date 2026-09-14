"""No false precision guard (DTS-006)."""

from __future__ import annotations

import math
from typing import Any


def _precision_for_magnitude(value: float) -> int:
    av = abs(value)
    if av >= 1000:
        return 2
    if av >= 10:
        return 3
    if av >= 1:
        return 4
    if av >= 0.01:
        return 5
    return 6


def round_value(value: float | None) -> float | None:
    if value is None:
        return None
    if not math.isfinite(value):
        return None
    digits = _precision_for_magnitude(value)
    return round(value, digits)


def guard_precision(payload: dict[str, Any]) -> dict[str, Any]:
    """Round USD-like numeric outputs to defensible precision."""
    out = dict(payload)
    for key in ("value_usd", "gross_edge_usd", "total_costs_usd", "expected_net_edge_usd", "expected_usd", "low_usd", "high_usd"):
        if key in out:
            out[key] = round_value(_as_float(out.get(key)))
    rng = out.get("range_usd")
    if isinstance(rng, dict):
        out["range_usd"] = {
            "low": round_value(_as_float(rng.get("low"))),
            "high": round_value(_as_float(rng.get("high"))),
        }
    edges = out.get("edge_separation")
    if isinstance(edges, dict):
        for edge_key in ("THEORETICAL_EDGE", "EXPECTED_NET_EDGE", "REALIZABLE_NET_EDGE"):
            block = edges.get(edge_key)
            if isinstance(block, dict) and "value_usd" in block:
                block = dict(block)
                block["value_usd"] = round_value(_as_float(block.get("value_usd")))
                edges[edge_key] = block
        out["edge_separation"] = edges
    return out


def _as_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None
