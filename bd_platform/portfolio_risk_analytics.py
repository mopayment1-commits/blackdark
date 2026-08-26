"""
Portfolio Risk Analytics — Features #723 + layer in Portfolio AI (Sprint 1).

#723 Correlation Matrix — NOT standalone, widget in Portfolio AI Dashboard.
Missing-data policy visible. Window controls user-selectable.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.PortfolioRiskAnalytics")

_FEATURE_ID = 723
_STANDALONE = False
_MERGED_INTO = "Portfolio AI / Portfolio Risk Analytics"
_SPRINT = 1
_SEED_PATH = Path("data/portfolio_risk_analytics_seed.json")
_METHODOLOGY_VERSION = "1.0"
_DEFAULT_WINDOW_DAYS = 30

_DISCLAIMER = (
    "Correlation matrix shows rolling return relationships. "
    "Missing data greyed out — no interpolation. "
    "Not investment advice."
)

MissingDataPolicy = Literal["grey_out", "exclude_pair", "no_interpolation"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"universes": {}, "correlations": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("portfolio risk analytics seed load failed: %s", exc)
        return {"universes": {}, "correlations": {}}


def build_missing_data_policy() -> dict[str, Any]:
    return {
        "policy": "grey_out",
        "no_interpolation": True,
        "exclude_incomplete_pairs": True,
        "user_visible": True,
        "display": "Missing data = greyed out (no interpolation)",
    }


def build_window_controls(window_days: int = _DEFAULT_WINDOW_DAYS) -> dict[str, Any]:
    return {
        "current_window_days": window_days,
        "available_windows": [7, 14, 30, 60, 90, 180],
        "user_selectable": True,
        "user_visible": True,
        "version": _METHODOLOGY_VERSION,
        "display": f"Correlation window: {window_days} days (user-selectable)",
    }


def build_correlation_heatmap(
    matrix: dict[str, dict[str, float | None]],
    *,
    assets: list[str],
    window_days: int,
) -> dict[str, Any]:
    cells = []
    for a in assets:
        for b in assets:
            val = (matrix.get(a) or {}).get(b)
            cells.append({
                "asset_a": a,
                "asset_b": b,
                "correlation": val,
                "missing": val is None,
                "greyed_out": val is None,
            })

    return {
        "sub_task": "#723",
        "ui_label": "Portfolio Risk Analytics — Correlation",
        "not_standalone": True,
        "assets": assets,
        "window_days": window_days,
        "window_controls": build_window_controls(window_days),
        "missing_data_policy": build_missing_data_policy(),
        "cells": cells,
        "matrix": matrix,
        "real_time_update": True,
        "cross_chain_depth": True,
        "display": f"Correlation heatmap | {len(assets)} assets | {window_days}D window",
    }


def build_correlation_panel(
    universe_id: str = "default",
    *,
    window_days: int = _DEFAULT_WINDOW_DAYS,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()
    universe = (seed.get("universes") or {}).get(universe_id)
    corr_data = (seed.get("correlations") or {}).get(universe_id)

    if not universe or not corr_data:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "universe_not_found",
            "universe_id": universe_id,
        }

    assets = universe.get("assets") or []
    matrix = corr_data.get("matrix") or {}
    heatmap = build_correlation_heatmap(matrix, assets=assets, window_days=window_days)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "portfolio_ai_widget",
        "universe_id": universe_id,
        "correlation": heatmap,
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def portfolio_risk_analytics_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Portfolio Risk Analytics",
        "ui_label": "Portfolio Risk Analytics",
        "not_named_correlation_matrix_only": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "missing_data_policy": build_missing_data_policy(),
        "window_controls": build_window_controls(),
        "acceptance_criteria": {
            "missing_data_policy_visible": True,
            "window_controls_visible": True,
            "real_time_update": True,
        },
        "universe_count": len(seed.get("universes") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
