"""
Risk Score Surface — visible risk index on every asset + portfolio.

Merged into Portfolio AI / Capital Protection (#410).
Monitoring only — not investment advice.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Any

_FEATURE_ID = 410
_TITLE = "Risk Score Surface"
_METHODOLOGY_VERSION = "1.0"

_DEFAULT_ASSETS = ("BTC", "ETH", "SOL", "BNB", "XRP", "UNI", "USDT", "USDC")


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _risk_band(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score >= 75:
        return "elevated"
    if score >= 55:
        return "moderate"
    return "low"


def score_asset_risk(asset: str, *, portfolio_id: str = "demo_portfolio") -> dict[str, Any]:
    """Risk score for one asset — position data or diligence proxy."""
    symbol = asset.upper().split("/")[0]
    score: float | None = None
    source = "diligence_proxy"
    display = f"{symbol} risk index unavailable"

    try:
        from bd_platform.capital_protection_controls import _load_seed, compute_position_risk_score

        seed = _load_seed()
        for pos in (seed.get("positions") or {}).values():
            if str(pos.get("symbol", "")).upper() == symbol or str(pos.get("asset", "")).upper() == symbol:
                block = compute_position_risk_score(pos)
                score = float(block.get("risk_score", 50))
                source = "position_risk_410"
                display = block.get("display") or display
                break
    except Exception:
        pass

    if score is None:
        try:
            from bd_platform.diligence_risk_scoring import score_entity_risk

            dr = score_entity_risk(symbol)
            if dr.get("ok"):
                score = float(dr.get("overall_risk_score", 50))
                source = "diligence_risk_460"
                display = f"{symbol} diligence risk {score}/100"
        except Exception:
            score = 50.0
            display = f"{symbol} default risk proxy 50/100"

    return {
        "ok": True,
        "asset": symbol,
        "risk_score": score,
        "risk_band": _risk_band(score),
        "source": source,
        "portfolio_id": portfolio_id,
        "display": display,
        "monitoring_only": True,
        "timestamp": _utcnow(),
    }


def build_portfolio_risk_surface(*, portfolio_id: str = "demo_portfolio") -> dict[str, Any]:
    """Portfolio-level risk summary + per-position scores."""
    t0 = time.perf_counter()
    position_scores: dict[str, Any] = {}
    portfolio_summary: dict[str, Any] = {}
    aggregate_score: float | None = None

    try:
        from bd_platform.capital_protection_controls import build_capital_awareness_panel

        panel = build_capital_awareness_panel(portfolio_id)
        position_scores = panel.get("position_risk_scores") or {}
        portfolio_summary = panel.get("portfolio_summary") or {}
        scores = [
            float(v.get("risk_score"))
            for v in position_scores.values()
            if v.get("risk_score") is not None
        ]
        if scores:
            aggregate_score = round(sum(scores) / len(scores), 1)
    except Exception:
        pass

    asset_scores = [score_asset_risk(a, portfolio_id=portfolio_id) for a in _DEFAULT_ASSETS]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "portfolio_id": portfolio_id,
        "portfolio_risk_score": aggregate_score,
        "portfolio_risk_band": _risk_band(aggregate_score),
        "position_risk_scores": position_scores,
        "asset_risk_scores": asset_scores,
        "portfolio_summary": portfolio_summary,
        "methodology_version": _METHODOLOGY_VERSION,
        "monitoring_only": True,
        "disclaimer": "Risk scores are monitoring indices only — not investment advice.",
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def risk_score_surface_status() -> dict[str, Any]:
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "methodology_version": _METHODOLOGY_VERSION,
        "default_assets": list(_DEFAULT_ASSETS),
        "surfaces": ["portfolio", "per_asset", "capability_pages", "dashboard"],
        "timestamp": _utcnow(),
    }
