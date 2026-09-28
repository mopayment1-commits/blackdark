"""Canonical Execution Feasibility engine (DTS-013)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p2-execution-feasibility-1.0"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def evaluate_execution_feasibility(opportunity: dict[str, Any], *, economics: dict[str, Any] | None = None) -> dict[str, Any]:
    """Return 0..100 score with explainable reason codes; no optimistic defaults."""
    opp = dict(opportunity or {})
    if opp.get("truth_indicative_only"):
        return {
            "state": "NOT_APPLICABLE",
            "score": None,
            "label": "EXECUTION_FEASIBILITY_NOT_APPLICABLE",
            "reason_codes": ["advisory_only"],
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    reason_codes: list[str] = []
    components: dict[str, float] = {}
    evidence_count = 0

    net = _optional_float(opp.get("net_profit_usdt") or opp.get("net_profit"))
    if net is not None:
        evidence_count += 1
        if net <= 0:
            components["edge"] = 5.0
            reason_codes.append("negative_or_zero_net_edge")
        elif net < 0.5:
            components["edge"] = 25.0
            reason_codes.append("thin_edge")
        else:
            components["edge"] = min(100.0, 40.0 + net * 8.0)
    else:
        reason_codes.append("missing_net_edge")

    slip = _optional_float(opp.get("total_slippage_bps") or opp.get("slippage_bps"))
    if slip is not None:
        evidence_count += 1
        if slip <= 5:
            components["slippage"] = 100.0
        elif slip <= 25:
            components["slippage"] = 100.0 - (slip - 5) * 3.0
        else:
            components["slippage"] = max(0.0, 40.0 - (slip - 25) * 1.5)
    else:
        reason_codes.append("missing_slippage")

    age_ms = _optional_float(opp.get("quote_age_ms") or opp.get("age_ms"))
    if age_ms is not None:
        evidence_count += 1
        max_age = _optional_float(opp.get("max_quote_age_ms")) or 2500.0
        if age_ms <= 400:
            components["latency"] = 100.0
        elif age_ms <= max_age:
            components["latency"] = 100.0 - 55.0 * ((age_ms - 400) / max(max_age - 400, 1.0))
        else:
            components["latency"] = max(0.0, 30.0 - (age_ms - max_age) / 100.0)
            reason_codes.append("stale_quote")
    else:
        reason_codes.append("missing_quote_age")

    depth = _optional_float(opp.get("depth_usd") or opp.get("liquidity_usd"))
    notional = _optional_float(opp.get("quote_amount") or opp.get("notional_usd"))
    if depth is not None and notional is not None and notional > 0:
        evidence_count += 1
        ratio = depth / notional
        if ratio >= 20:
            components["depth"] = 100.0
        elif ratio >= 5:
            components["depth"] = 60.0 + (ratio - 5) * (40.0 / 15.0)
        else:
            components["depth"] = max(10.0, ratio * 12.0)
            reason_codes.append("thin_depth")
    else:
        reason_codes.append("missing_depth_or_notional")

    fill_prob = _optional_float(opp.get("fill_probability") or opp.get("expected_fill_probability"))
    if fill_prob is not None:
        evidence_count += 1
        components["fill_probability"] = max(0.0, min(100.0, fill_prob * 100.0))
    else:
        label = str(opp.get("execution_feasibility") or "").lower()
        if label in {"full", "high", "partial", "medium", "low", "below_threshold", "not_executable"}:
            mapping = {"full": 90.0, "high": 85.0, "partial": 65.0, "medium": 55.0, "low": 25.0, "below_threshold": 20.0, "not_executable": 10.0}
            components["fill_probability"] = mapping[label]
            evidence_count += 1
            reason_codes.append("label_mapped_fill_proxy")
        else:
            reason_codes.append("missing_fill_probability")

    venue_ok = opp.get("venue_available")
    if venue_ok is not None:
        evidence_count += 1
        components["venue"] = 100.0 if bool(venue_ok) else 15.0
        if not venue_ok:
            reason_codes.append("venue_unavailable")

    if economics and economics.get("reject"):
        reason_codes.append("economics_reject")

    if evidence_count < 3:
        return {
            "state": "EXECUTION_FEASIBILITY_UNAVAILABLE",
            "score": None,
            "reason_codes": reason_codes,
            "components": components,
            "evidence_count": evidence_count,
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    weights = {
        "edge": 0.20,
        "slippage": 0.20,
        "latency": 0.20,
        "depth": 0.20,
        "fill_probability": 0.15,
        "venue": 0.05,
    }
    active = {k: v for k, v in components.items() if k in weights}
    if not active:
        return {
            "state": "EXECUTION_FEASIBILITY_UNAVAILABLE",
            "score": None,
            "reason_codes": reason_codes + ["no_scorable_components"],
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }
    weight_sum = sum(weights[k] for k in active)
    score = sum(active[k] * weights[k] for k in active) / weight_sum
    score = round(min(100.0, max(0.0, score)), 2)

    return {
        "state": "AVAILABLE",
        "score": score,
        "reason_codes": reason_codes,
        "components": {k: round(v, 2) for k, v in active.items()},
        "evidence_count": evidence_count,
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
    }
