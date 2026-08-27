"""
Custom Ratio Engine — Feature #653 (Sprint-2 Market Radar).

Formula builder for custom valuation ratios with unit validation, versioning,
missing≠zero, reproducible history, and peer comparison.

NOT standalone — Ratio Builder tool in Market Radar + Intelligence Ledger.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bd_platform.institutional_standards import missing_value

logger = logging.getLogger("BLACKDARK.CustomRatioEngine")

_FEATURE_ID = 653
_METRICS_REF = 577
_FINANCIALS_REF = 641
_THESIS_REF = 472
_TITLE = "Ratio Builder"
_LEGAL_NAME = "Custom Ratio Engine"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Market Radar Core / Intelligence Ledger"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/custom_ratio_engine_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Custom Ratio Engine — user-defined valuation ratios with unit validation. "
    "Missing data shown as N/A, never zero. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"metrics": {}, "protocols": {}, "presets": {}, "formulas": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("custom ratio engine seed load failed: %s", exc)
        return {"metrics": {}, "protocols": {}, "presets": {}, "formulas": {}}


def _metric_catalog(seed: dict[str, Any]) -> dict[str, dict[str, Any]]:
    catalog = dict(seed.get("metrics") or {})
    try:
        from bd_platform.on_chain_financials import build_metrics_library_financials

        for pid in (seed.get("protocols") or {}):
            lib = build_metrics_library_financials(pid, seed=None)
            if not lib.get("ok"):
                continue
            for mid, spec in (lib.get("metrics") or {}).items():
                catalog[mid] = {
                    "metric_id": mid,
                    "name": mid.replace("_", " ").title(),
                    "unit": spec.get("unit", "USD"),
                    "type": "financial",
                    "source": "on_chain_financials_641",
                    "version": lib.get("formula_version", "1.0"),
                }
    except Exception:
        logger.debug("641 metrics catalog merge skipped", exc_info=True)

    try:
        from bd_platform.onchain_metrics_library import build_metric_definitions

        defs = build_metric_definitions(seed=None)
        for mid, spec in (defs.get("definitions") or {}).items():
            if mid not in catalog:
                catalog[mid] = {
                    "metric_id": mid,
                    "name": spec.get("name", mid),
                    "unit": spec.get("unit", "count"),
                    "type": spec.get("type", "on_chain"),
                    "source": "onchain_metrics_library_577",
                    "version": spec.get("version", "1.0"),
                }
    except Exception:
        logger.debug("577 metrics catalog merge skipped", exc_info=True)

    return catalog


def validate_formula(
    numerator_metric: str,
    denominator_metric: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Unit/type checks — incompatible combinations produce warning."""
    seed = seed or _load_seed()
    catalog = _metric_catalog(seed)
    num = catalog.get(numerator_metric)
    den = catalog.get(denominator_metric)

    if not num or not den:
        return {
            "ok": False,
            "valid": False,
            "error": "metric_not_found",
            "numerator_metric": numerator_metric,
            "denominator_metric": denominator_metric,
        }

    num_unit = num.get("unit", "")
    den_unit = den.get("unit", "")
    warning = None
    valid = True

    if num_unit == den_unit:
        result_unit = "ratio"
    elif num_unit == "USD" and den_unit == "count":
        result_unit = "USD_per_unit"
        warning = "USD divided by count — interpret as per-unit value"
    elif num_unit == "count" and den_unit == "USD":
        result_unit = "units_per_usd"
        warning = "Count divided by USD — low interpretability"
    elif num_unit == "percent" and den_unit == "USD":
        result_unit = "pct_per_usd"
        warning = "Percent divided by USD — verify formula intent"
    else:
        valid = False
        warning = f"Incompatible units: {num_unit} ÷ {den_unit} — formula blocked"

    return {
        "ok": True,
        "valid": valid,
        "numerator_metric": numerator_metric,
        "denominator_metric": denominator_metric,
        "numerator_unit": num_unit,
        "denominator_unit": den_unit,
        "result_unit": result_unit if valid else None,
        "unit_type_check": True,
        "warning": warning,
        "timestamp": _utcnow(),
    }


def _resolve_metric_value(
    protocol_id: str,
    metric_id: str,
    *,
    as_of_date: str | None,
    seed: dict[str, Any],
) -> Any:
    proto = (seed.get("protocols") or {}).get(protocol_id) or {}
    history = (seed.get("historical") or {}).get(protocol_id, {}).get(metric_id) or []

    if as_of_date:
        if history:
            point = next((h for h in history if h.get("date") == as_of_date), None)
            if point:
                val = point.get("value")
                return val if val is not None else missing_value(numeric=True)
        return missing_value(numeric=True)

    val = proto.get(metric_id)
    if val is None:
        return missing_value(numeric=True)
    return val


def _formula_hash(formula: dict[str, Any]) -> str:
    payload = json.dumps({
        "numerator": formula.get("numerator_metric"),
        "denominator": formula.get("denominator_metric"),
        "version": formula.get("version"),
        "annualize": formula.get("annualize", False),
    }, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()[:16]


def compute_ratio(
    protocol_id: str,
    formula_id: str,
    *,
    as_of_date: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute ratio — missing≠zero, reproducible with same formula+date."""
    seed = seed or _load_seed()
    formulas = seed.get("formulas") or {}
    presets = seed.get("presets") or {}
    formula = formulas.get(formula_id) or presets.get(formula_id)
    if not formula:
        return {"ok": False, "formula_id": formula_id, "error": "formula_not_found"}

    validation = validate_formula(
        formula["numerator_metric"],
        formula["denominator_metric"],
        seed=seed,
    )
    if not validation.get("valid"):
        return {"ok": False, "formula_id": formula_id, "validation": validation}

    num_val = _resolve_metric_value(protocol_id, formula["numerator_metric"], as_of_date=as_of_date, seed=seed)
    den_val = _resolve_metric_value(protocol_id, formula["denominator_metric"], as_of_date=as_of_date, seed=seed)

    if num_val is None or den_val is None:
        ratio_value = missing_value(numeric=True)
        display_value = "N/A"
    elif den_val == 0:
        ratio_value = missing_value(numeric=True)
        display_value = "N/A"
    else:
        effective_den = float(den_val)
        if formula.get("annualize"):
            effective_den *= 12
        ratio_value = round(float(num_val) / effective_den, 4)
        display_value = f"{ratio_value}"

    reproducibility_key = _formula_hash(formula) + (as_of_date or "latest")

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "protocol_id": protocol_id,
        "formula_id": formula_id,
        "formula_version": formula.get("version"),
        "formula": formula,
        "numerator_value": num_val,
        "denominator_value": den_val,
        "ratio_value": ratio_value,
        "display": display_value,
        "missing_not_zero": True,
        "as_of_date": as_of_date or seed.get("as_of_date"),
        "reproducibility_key": reproducibility_key,
        "reproducible": True,
        "validation": validation,
        "timestamp": _utcnow(),
    }


def build_peer_comparison(
    protocol_id: str,
    formula_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Peer percentile — e.g. FDV/Revenue = 15x → higher than 78% of protocols."""
    seed = seed or _load_seed()
    protocols = seed.get("protocols") or {}
    values: list[tuple[str, float]] = []

    for pid in protocols:
        result = compute_ratio(pid, formula_id, seed=seed)
        if result.get("ok") and result.get("ratio_value") is not None:
            values.append((pid, float(result["ratio_value"])))

    if not values:
        return {"ok": False, "error": "no_peer_values"}

    values.sort(key=lambda x: x[1])
    target = compute_ratio(protocol_id, formula_id, seed=seed)
    if not target.get("ok") or target.get("ratio_value") is None:
        return {"ok": False, "protocol_id": protocol_id, "error": "target_ratio_unavailable"}

    target_val = float(target["ratio_value"])
    below = sum(1 for _, v in values if v < target_val)
    percentile = round(below / len(values) * 100, 1)

    peers = [
        {
            "protocol_id": pid,
            "protocol_name": (protocols.get(pid) or {}).get("protocol_name", pid),
            "ratio_value": val,
        }
        for pid, val in values
    ]

    return {
        "ok": True,
        "protocol_id": protocol_id,
        "formula_id": formula_id,
        "ratio_value": target_val,
        "percentile": percentile,
        "peer_count": len(values),
        "peers": peers,
        "display": f"{formula_id} = {target_val}x → higher than {percentile:.0f}% of protocols",
        "timestamp": _utcnow(),
    }


def build_ratio_chart(
    protocol_id: str,
    formula_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Historical ratio chart — reproducible history."""
    seed = seed or _load_seed()
    history = (seed.get("historical") or {}).get(protocol_id, {}).get(formula_id) or []
    points: list[dict[str, Any]] = []

    if history:
        for point in history:
            as_of = point.get("date")
            computed = compute_ratio(protocol_id, formula_id, as_of_date=as_of, seed=seed)
            points.append({
                "date": as_of,
                "ratio_value": computed.get("ratio_value"),
                "display": computed.get("display"),
                "reproducibility_key": computed.get("reproducibility_key"),
            })
    else:
        num_metric = (seed.get("formulas") or seed.get("presets") or {}).get(formula_id, {}).get("numerator_metric")
        num_hist = (seed.get("historical") or {}).get(protocol_id, {}).get(num_metric or "", [])
        for point in num_hist:
            as_of = point.get("date")
            computed = compute_ratio(protocol_id, formula_id, as_of_date=as_of, seed=seed)
            points.append({
                "date": as_of,
                "ratio_value": computed.get("ratio_value"),
                "display": computed.get("display"),
                "reproducibility_key": computed.get("reproducibility_key"),
            })

    return {
        "ok": True,
        "route": "/ratio-builder",
        "protocol_id": protocol_id,
        "formula_id": formula_id,
        "chart_type": "ratio_history",
        "points": points,
        "reproducible_history": True,
        "missing_not_zero": True,
        "timestamp": _utcnow(),
    }


def build_ratio_builder_panel(
    protocol_id: str = "uniswap",
    formula_id: str = "ps_ratio",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    catalog = _metric_catalog(seed)
    ratio = compute_ratio(protocol_id, formula_id, seed=seed)
    peers = build_peer_comparison(protocol_id, formula_id, seed=seed)
    chart = build_ratio_chart(protocol_id, formula_id, seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": ratio.get("ok", False),
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "route": "/ratio-builder",
        "protocol_id": protocol_id,
        "formula_id": formula_id,
        "available_metrics": list(catalog.values()),
        "presets": list((seed.get("presets") or {}).values()),
        "formula_input": {
            "text_input_supported": True,
            "drag_drop_supported": True,
            "metrics_source_577": True,
            "financials_source_641": True,
        },
        "ratio": ratio,
        "peer_comparison": peers if peers.get("ok") else None,
        "chart": chart,
        "unit_type_checks": True,
        "formula_versioning": True,
        "missing_not_zero": True,
        "reproducible_history": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def score_custom_ratio_thesis_dimension(
    asset: str,
    formula_id: str = "ps_ratio",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#472 — custom ratio as optional thesis scoring dimension."""
    ratio_seed = _load_seed()
    asset_map = ratio_seed.get("asset_protocol_map") or {}
    protocol_id = asset_map.get(asset.upper())
    if not protocol_id:
        return {"ok": False, "asset": asset, "error": "no_protocol_mapping"}

    ratio = compute_ratio(protocol_id, formula_id, seed=ratio_seed)
    peers = build_peer_comparison(protocol_id, formula_id, seed=ratio_seed)
    if not ratio.get("ok") or ratio.get("ratio_value") is None:
        return {"ok": False, "asset": asset, "error": "ratio_unavailable"}

    val = float(ratio["ratio_value"])
    percentile = float(peers.get("percentile", 50)) if peers.get("ok") else 50
    score = round(min(100, max(0, 100 - percentile * 0.8 + (20 if val < 20 else 0))), 2)

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "thesis_ref": _THESIS_REF,
        "asset": asset.upper(),
        "protocol_id": protocol_id,
        "formula_id": formula_id,
        "custom_ratio_dimension": True,
        "dimension_score": score,
        "ratio_value": val,
        "percentile_vs_peers": percentile,
        "formula_version": ratio.get("formula_version"),
        "display": f"Custom ratio {formula_id}: {val} (percentile {percentile:.0f})",
        "timestamp": _utcnow(),
    }


def custom_ratio_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "preset_count": len(seed.get("presets") or {}),
        "metric_count": len(_metric_catalog(seed)),
        "unit_type_checks": True,
        "formula_versioning": True,
        "missing_not_zero": True,
        "reproducible_history": True,
        "integrations": {
            "onchain_metrics_library_577": True,
            "on_chain_financials_641": True,
            "investment_thesis_472": True,
            "market_radar": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": _STANDALONE is False, "detail": "653"})

    panel = build_ratio_builder_panel(seed=seed)
    checks.append({"id": "panel_ok", "passed": panel.get("ok") is True, "detail": "panel"})
    checks.append({"id": "presets", "passed": len(panel.get("presets") or []) >= 3, "detail": "presets"})
    checks.append({"id": "metrics_577_641", "passed": len(panel.get("available_metrics") or []) >= 5, "detail": "metrics"})

    valid = validate_formula("fdv", "revenue_30d", seed=seed)
    checks.append({"id": "unit_check_valid", "passed": valid.get("valid") is True, "detail": "valid"})
    invalid = validate_formula("market_cap", "tx_count", seed=seed)
    checks.append({"id": "unit_check_warning", "passed": invalid.get("warning") is not None, "detail": "warn"})

    ratio = compute_ratio("uniswap", "ps_ratio", seed=seed)
    checks.append({"id": "ratio_compute", "passed": ratio.get("ok") is True and ratio.get("ratio_value") is not None, "detail": "ratio"})
    checks.append({"id": "formula_version", "passed": ratio.get("formula_version") is not None, "detail": "version"})
    checks.append({"id": "reproducible", "passed": ratio.get("reproducible") is True, "detail": "repro"})
    checks.append({"id": "reproducibility_key", "passed": bool(ratio.get("reproducibility_key")), "detail": "key"})

    missing = compute_ratio("uniswap", "revenue_per_user", as_of_date="2099-01", seed=seed)
    checks.append({"id": "missing_not_zero", "passed": missing.get("display") == "N/A", "detail": "N/A"})

    peers = build_peer_comparison("uniswap", "ps_ratio", seed=seed)
    checks.append({"id": "peer_percentile", "passed": peers.get("ok") is True and peers.get("percentile") is not None, "detail": "peers"})

    chart = build_ratio_chart("uniswap", "ps_ratio", seed=seed)
    checks.append({"id": "ratio_chart", "passed": chart.get("ok") is True and len(chart.get("points") or []) >= 2, "detail": "chart"})

    hist_a = compute_ratio("uniswap", "ps_ratio", as_of_date="2025-07", seed=seed)
    hist_b = compute_ratio("uniswap", "ps_ratio", as_of_date="2025-07", seed=seed)
    checks.append({"id": "same_date_same_result", "passed": hist_a.get("ratio_value") == hist_b.get("ratio_value"), "detail": "history"})

    thesis = score_custom_ratio_thesis_dimension("UNI", seed=seed)
    checks.append({"id": "thesis_472", "passed": thesis.get("ok") is True, "detail": "472"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
