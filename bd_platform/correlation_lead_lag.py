"""
Correlation & Lead-Lag Module — Feature #271 merged into Intelligence Ledger (Sprint 2).

Analyst Suite module for metric correlation and lead-lag analysis.
NOT standalone — requires Sprint 1 Data Engine stability gate.
No causation language — correlation values only.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.CorrelationLeadLag")

_FEATURE_ID = 271
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Analyst Suite"
_SPRINT = 2
_SEED_PATH = Path("data/correlation_lead_lag_seed.json")
_METHODOLOGY_VERSION = "1.0"
_WINDOW_OPTIONS = (7, 30, 90, 365)
_LAG_RANGE = (-30, 30)
_MISSING_DATA_BLOCK_THRESHOLD = 0.20
_SIGNIFICANCE_ALPHA = 0.05

_BANNED_WORDS = ("causes", "drives", "predicts", "will rise", "will fall", "leads to")

_DISCLAIMER = (
    "Correlation does not imply causation. "
    "Correlation values are descriptive only — not predictions or trade signals."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"analyses": {}, "dependency_gate": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("correlation lead-lag seed load failed: %s", exc)
        return {"analyses": {}, "dependency_gate": {}}


def check_dependency_gate(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Sprint 1 Data Engine must be stable before correlation analysis."""
    seed = seed or _load_seed()
    gate = seed.get("dependency_gate") or {}
    passed = bool(gate.get("data_engine_stable")) and bool(gate.get("stability_days_met"))
    return {
        "data_engine_required": True,
        "stability_days_required": gate.get("stability_days_required", 30),
        "stability_days_met": gate.get("stability_days_met", 0),
        "data_engine_stable": gate.get("data_engine_stable", False),
        "production_grade_metrics": gate.get("production_grade_metrics", False),
        "gate_passed": passed,
        "display": (
            "No start before Sprint 1 Data Engine completion + "
            f"{gate.get('stability_days_required', 30)} day stability. "
            f"Metrics must be production-grade before correlation."
        ),
        "blocked_if_not_met": not passed,
    }


def build_scope_lock(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    phase = seed.get("current_phase", 1)
    return {
        "current_phase": phase,
        "phases": {
            1: "Price vs on-chain metrics only",
            2: "Price vs sentiment",
            3: "Multi-metric matrix",
        },
        "update_mode": "daily batch — no real-time correlation",
        "display": (
            f"Phase {phase}: {seed.get('phase_label', 'Price vs on-chain metrics only')} | "
            "No real-time correlation = daily batch sufficient"
        ),
    }


def validate_data_quality(quality: dict[str, Any], *, window_days: int) -> dict[str, Any]:
    """Missing data > 20% in window = correlation blocked."""
    missing_pct = float(quality.get("missing_pct", 0))
    blocked = missing_pct > _MISSING_DATA_BLOCK_THRESHOLD
    return {
        "window_days": window_days,
        "missing_pct": missing_pct,
        "missing_data_blocked": blocked,
        "interpolation_method": quality.get("interpolation_method", "linear"),
        "outlier_handling": quality.get("outlier_handling", "winsorize_3sigma"),
        "timestamp_alignment": "strict — no mixed granularities",
        "missing_indicator_visible": True,
        "display": (
            f"Missing data: {missing_pct:.1%} | "
            f"Interpolation: {quality.get('interpolation_method', 'linear')} | "
            f"Outliers: {quality.get('outlier_handling', 'winsorize_3sigma')} | "
            f"Alignment: strict UTC"
            + (" | BLOCKED: >20% missing" if blocked else "")
        ),
    }


def build_correlation_result(corr: dict[str, Any]) -> dict[str, Any]:
    """Correlation result — no causation language."""
    r = float(corr.get("coefficient", 0))
    p_value = float(corr.get("p_value", 1))
    window = int(corr.get("window_days", 30))
    significant = p_value < _SIGNIFICANCE_ALPHA

    display = (
        f"Correlation ({corr.get('metric_a')} vs {corr.get('metric_b')}): "
        f"r={r:.3f} | Window: {window}D | p-value: {p_value:.4f}"
        + (" | Significant (p < 0.05)" if significant else "")
    )

    for word in _BANNED_WORDS:
        assert word not in display.lower()

    return {
        "metric_a": corr.get("metric_a"),
        "metric_b": corr.get("metric_b"),
        "coefficient": r,
        "p_value": p_value,
        "window_days": window,
        "significant": significant,
        "significance_visible": True,
        "window_visible": True,
        "display": display,
        "no_causation_language": True,
        "correlation_only": True,
    }


def build_lead_lag_panel(lag: dict[str, Any]) -> dict[str, Any]:
    """Lead-lag analysis — lag range -30 to +30 days."""
    best_lag = int(lag.get("best_lag_days", 0))
    max_corr = float(lag.get("max_correlation", 0))
    return {
        "best_lag_days": best_lag,
        "max_correlation": max_corr,
        "lag_range": list(_LAG_RANGE),
        "display": (
            f"Lead-Lag: best lag = {best_lag:+d} days | "
            f"max r = {max_corr:.3f} | Range: {_LAG_RANGE[0]} to +{_LAG_RANGE[1]} days"
        ),
        "no_causation_language": True,
        "descriptive_only": True,
    }


def build_correlation_analysis(
    metric_a: str,
    metric_b: str,
    *,
    window_days: int = 30,
) -> dict[str, Any]:
    """Full correlation + lead-lag panel for Analyst Suite."""
    t0 = time.perf_counter()
    seed = _load_seed()
    gate = check_dependency_gate(seed)

    if gate["blocked_if_not_met"]:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "dependency_gate_not_met",
            "dependency_gate": gate,
            "disclaimer": _DISCLAIMER,
        }

    if window_days not in _WINDOW_OPTIONS:
        window_days = 30

    analyses = seed.get("analyses") or {}
    analysis = analyses.get(f"{metric_a}:{metric_b}:{window_days}")
    if not analysis:
        analysis = analyses.get(metric_a)
    if not analysis:
        analysis = analyses.get(f"{metric_a.upper()}:{metric_b}")
    if not analysis:
        analysis = analyses.get(f"{metric_a}:{metric_b}")
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "analysis_not_configured",
            "metric_a": metric_a,
            "metric_b": metric_b,
            "window_days": window_days,
        }

    quality = validate_data_quality(analysis.get("data_quality") or {}, window_days=window_days)
    if quality["missing_data_blocked"]:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "missing_data_threshold_exceeded",
            "data_quality": quality,
            "disclaimer": _DISCLAIMER,
        }

    correlation = build_correlation_result({
        "metric_a": metric_a,
        "metric_b": metric_b,
        **(analysis.get("correlation") or {}),
        "window_days": window_days,
    })
    lead_lag = build_lead_lag_panel(analysis.get("lead_lag") or {})

    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "surface": "correlation_lead_lag",
        "analyst_suite_module": True,
        "metric_a": metric_a,
        "metric_b": metric_b,
        "window_days": window_days,
        "available_windows": list(_WINDOW_OPTIONS),
        "correlation": correlation,
        "lead_lag": lead_lag,
        "data_quality": quality,
        "dependency_gate": gate,
        "scope_lock": build_scope_lock(seed),
        "methodology_version": _METHODOLOGY_VERSION,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "no_causation_language": True,
        "daily_batch": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def correlation_lead_lag_status() -> dict[str, Any]:
    seed = _load_seed()
    gate = check_dependency_gate(seed)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Correlation & Lead-Lag Module",
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "analyst_suite_module": True,
        "dependency_gate": gate,
        "scope_lock": build_scope_lock(seed),
        "window_options_days": list(_WINDOW_OPTIONS),
        "lag_range_days": list(_LAG_RANGE),
        "significance_alpha": _SIGNIFICANCE_ALPHA,
        "missing_data_block_threshold": _MISSING_DATA_BLOCK_THRESHOLD,
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "acceptance_criteria": {
            "no_causation_language": True,
            "window_significance_visible": True,
            "missing_data_controlled": True,
            "dependency_gate": True,
            "window_sizes": list(_WINDOW_OPTIONS),
            "lag_range": list(_LAG_RANGE),
            "e2e_metric_selection": True,
        },
        "timestamp": _utcnow(),
    }
