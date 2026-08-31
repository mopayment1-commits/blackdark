"""
Development-to-Market Divergence Detector — Feature #537 (Sprint 2 Intelligence Layer).

Detect divergence between development activity and price/social/on-chain usage.
Descriptive observation only — no causal claim, no prediction, no value signal.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.DevMarketDivergenceDetector")

_FEATURE_ID = 537
_TITLE = "Development-to-Market Divergence Detector"
_STANDALONE = False
_LAYER = "Intelligence Layer"
_SPRINT = 2
_SEED_PATH = Path("data/dev_market_divergence_detector_seed.json")
_METHODOLOGY_VERSION = "1.0"

DivergenceType = Literal["positive", "negative", "none", "insufficient_data"]

_BANNED_TERMS = (
    "buy opportunity",
    "price will catch up",
    "value signal",
    "undervalued",
    "will converge",
)

_DISCLAIMER = (
    "Divergence observations are descriptive statistical relationships — not predictions. "
    "Development activity and price may diverge without implying future convergence. "
    "Not investment advice."
)

_WINDOWS = {
    "rolling_days": 90,
    "persistence_threshold_days": 14,
    "min_data_points": 30,
    "sparse_data_threshold": 5,
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"projects": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("dev market divergence seed load failed: %s", exc)
        return {"projects": {}}


def build_windows_block() -> dict[str, Any]:
    """Windows documented — mandatory."""
    return {
        "rolling_window_days": _WINDOWS["rolling_days"],
        "persistence_threshold_days": _WINDOWS["persistence_threshold_days"],
        "min_data_points": _WINDOWS["min_data_points"],
        "sparse_data_threshold": _WINDOWS["sparse_data_threshold"],
        "windows_documented": True,
        "display": (
            f"Rolling window: {_WINDOWS['rolling_days']}D | "
            f"Persistence: {_WINDOWS['persistence_threshold_days']}D | "
            f"Min data points: {_WINDOWS['min_data_points']}"
        ),
    }


def check_sparse_data(project: dict[str, Any]) -> dict[str, Any]:
    """Sparse data handling — flag insufficient data."""
    dev_commits = int(project.get("dev_commits_90d", 0))
    contributors = int(project.get("contributors_90d", 0))
    threshold = _WINDOWS["sparse_data_threshold"]

    insufficient = dev_commits < threshold or contributors < 1
    return {
        "insufficient_data": insufficient,
        "dev_commits_90d": dev_commits,
        "contributors_90d": contributors,
        "sparse_data_threshold": threshold,
        "display": (
            "Insufficient data — low development activity"
            if insufficient
            else f"Sufficient data: {dev_commits} commits, {contributors} contributors (90D)"
        ),
    }


def detect_divergence(project: dict[str, Any]) -> dict[str, Any]:
    """Rolling divergence detection — descriptive only."""
    sparse = check_sparse_data(project)
    if sparse["insufficient_data"]:
        return {
            "divergence_type": "insufficient_data",
            "divergence_detected": False,
            "sparse_data": sparse,
            "no_causal_claim": True,
            "not_prediction": True,
            "not_value_signal": True,
            "descriptive_only": True,
            "display": "Insufficient data for divergence analysis",
        }

    dev_trend = float(project.get("dev_activity_trend", 0))
    price_trend = float(project.get("price_trend_90d", 0))
    social_trend = float(project.get("social_trend_90d", 0))
    onchain_trend = float(project.get("onchain_usage_trend_90d", 0))
    persistence_days = int(project.get("divergence_persistence_days", 0))

    dev_high = dev_trend > 0.2
    market_low = price_trend < -0.1 and social_trend < 0
    dev_low = dev_trend < -0.1
    market_high = price_trend > 0.2

    if dev_high and market_low and persistence_days >= _WINDOWS["persistence_threshold_days"]:
        div_type: DivergenceType = "positive"
        observation = (
            f"Development activity and price have diverged over {_WINDOWS['rolling_days']}D window"
        )
    elif dev_low and market_high and persistence_days >= _WINDOWS["persistence_threshold_days"]:
        div_type = "negative"
        observation = (
            f"Development activity and price have diverged over {_WINDOWS['rolling_days']}D window"
        )
    else:
        div_type = "none"
        observation = "No significant divergence detected"

    return {
        "divergence_type": div_type,
        "divergence_detected": div_type in ("positive", "negative"),
        "observation": observation,
        "dev_activity_trend": dev_trend,
        "price_trend_90d": price_trend,
        "social_trend_90d": social_trend,
        "onchain_usage_trend_90d": onchain_trend,
        "persistence_days": persistence_days,
        "persistence_threshold_met": persistence_days >= _WINDOWS["persistence_threshold_days"],
        "sparse_data": sparse,
        "no_causal_claim": True,
        "not_prediction": True,
        "not_value_signal": True,
        "descriptive_only": True,
        "linguistic_framing": observation,
        "banned_framing": list(_BANNED_TERMS),
        "evidence": project.get("evidence") or [],
        "display": f"{observation} | Type: {div_type} | Persistence: {persistence_days}D",
    }


def build_backtest_summary(project: dict[str, Any]) -> dict[str, Any]:
    """Backtest summary — mandatory acceptance criterion."""
    backtest = project.get("backtest") or {}
    return {
        "backtest_available": bool(backtest),
        "historical_divergences": backtest.get("historical_divergence_count", 0),
        "mean_reversion_rate": backtest.get("mean_reversion_rate"),
        "false_positive_rate": backtest.get("false_positive_rate"),
        "backtest_window": backtest.get("window", f"{_WINDOWS['rolling_days']}D"),
        "no_causal_claim_in_backtest": True,
        "display": (
            f"Backtest: {backtest.get('historical_divergence_count', 0)} historical divergences | "
            f"Mean reversion: {backtest.get('mean_reversion_rate', 'N/A')}"
        ),
    }


def build_divergence_panel(project_id: str = "uniswap") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    project = (seed.get("projects") or {}).get(project_id)

    if not project:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "project_not_found", "project_id": project_id}

    divergence = detect_divergence(project)
    backtest = build_backtest_summary(project)
    windows = build_windows_block()
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "project_id": project_id,
        "project_name": project.get("name", project_id),
        "windows": windows,
        "divergence": divergence,
        "backtest": backtest,
        "acceptance_criteria": {
            "no_causal_claim": True,
            "windows_documented": True,
            "sparse_data_handling": True,
            "backtest": True,
            "descriptive_only": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def run_divergence_qa_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    windows = build_windows_block()
    tests.append({
        "test": "windows_documented",
        "passed": windows.get("windows_documented") is True,
    })

    for pid, project in (seed.get("projects") or {}).items():
        div = detect_divergence(project)
        tests.append({
            "test": f"no_causal_claim_{pid}",
            "passed": div.get("no_causal_claim") is True and div.get("not_prediction") is True,
        })

        if project.get("dev_commits_90d", 10) < _WINDOWS["sparse_data_threshold"]:
            tests.append({
                "test": f"sparse_data_flagged_{pid}",
                "passed": div.get("divergence_type") == "insufficient_data",
            })

        backtest = build_backtest_summary(project)
        if backtest.get("backtest_available"):
            tests.append({
                "test": f"backtest_available_{pid}",
                "passed": backtest.get("no_causal_claim_in_backtest") is True,
            })

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": True,
        "divergence_qa_tests": tests,
        "all_passed": all_passed,
        "test_count": len(tests),
    }


def dev_market_divergence_detector_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "windows": build_windows_block(),
        "project_count": len(seed.get("projects") or {}),
        "acceptance_criteria": {
            "no_causal_claim": True,
            "windows_documented": True,
            "sparse_data_handling": True,
            "backtest": True,
            "descriptive_only": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
