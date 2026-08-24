"""
Confidence Engine — Feature #149 (Sprint 2, phased rollout).

Phase 1 (now): Rule-based scoring — 10-15 criteria, score 0-100.
Phase 2 (3-6 months): ML models on accumulated data.
Phase 3 (12 months): Full engine with 2-year backtest.

Label: "Confidence: Experimental" — no Sharpe ≥1.5 promises on day one.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ConfidenceEngine")

_FEATURE_ID = 149
_PHASE = 1
_PHASE_LABEL = "Experimental"
_SCORES_PATH = Path("data/confidence_engine_scores.jsonl")

_ROADMAP = {
    "phase_1": {
        "status": "active",
        "label": "Rule-based scoring (10-15 criteria)",
        "ml": False,
    },
    "phase_2": {
        "status": "planned",
        "label": "ML models on accumulated data (3-6 months)",
        "ml": True,
    },
    "phase_3": {
        "status": "planned",
        "label": "Full Confidence Engine + 2-year backtest (12 months)",
        "ml": True,
    },
}

# Honest transparency — no fabricated Sharpe; targets are goals not promises
_PERFORMANCE_DISCLOSURE = {
    "phase": 1,
    "label": _PHASE_LABEL,
    "sharpe_target_phase_3": 1.5,
    "sharpe_current": None,
    "max_drawdown_target_phase_3_pct": 15,
    "max_drawdown_current_pct": None,
    "win_rate_target_phase_3_pct": 55,
    "win_rate_current_pct": None,
    "backtest_years_target": 2,
    "backtest_years_current": 0,
    "note": "Phase 1 is rule-based only — historical ML metrics not claimed until Phase 3.",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _append_score(row: dict[str, Any]) -> None:
    _SCORES_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _SCORES_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, default=str) + "\n")


def _criterion(name: str, score: float, weight: float, detail: str) -> dict[str, Any]:
    return {
        "criterion": name,
        "score": round(max(0.0, min(100.0, score)), 1),
        "weight": weight,
        "detail": detail,
    }


def compute_rule_based_confidence(
    *,
    asset: str,
    price_data: dict[str, Any] | None = None,
    market_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Phase 1 — 12 weighted criteria → confidence score 0-100.
    """
    sym = asset.upper().replace("/USDT", "")
    pd = price_data or {}
    md = market_data or {}
    meta = pd.get("source_metadata") or {}

    connectors_ok = int(meta.get("connectors_ok") or 0)
    connectors_polled = int(meta.get("connectors_polled") or 1)
    outlier_count = int(pd.get("outlier_count") or 0)
    quotes_clean = int(pd.get("quotes_clean") or 0)
    accuracy = float(pd.get("accuracy_estimate") or 0.9)
    price_verified = bool(pd.get("price_verified", pd.get("validation", {}).get("price_verified", False)))
    latency_ms = float(pd.get("latency_ms") or 500)
    change_24h = abs(float(md.get("change_24h") or md.get("change_pct") or 0))
    volume = float(md.get("quote_volume") or md.get("volume_24h_usd") or 0)
    sources_used = len(meta.get("sources_used") or [])

    criteria: list[dict[str, Any]] = [
        _criterion("multi_source_agreement", min(100, connectors_ok * 12), 0.10, f"{connectors_ok}/{connectors_polled} connectors OK"),
        _criterion("source_diversity", min(100, sources_used * 15), 0.08, f"{sources_used} sources in VWAP"),
        _criterion("outlier_cleanliness", max(0, 100 - outlier_count * 25), 0.10, f"{outlier_count} outliers removed"),
        _criterion("data_validation", 95 if price_verified else 40, 0.10, "Price Verified" if price_verified else "validation pending"),
        _criterion("accuracy_estimate", accuracy * 100, 0.08, f"rolling accuracy {accuracy:.2%}"),
        _criterion("latency_freshness", max(0, 100 - latency_ms / 20), 0.07, f"{latency_ms:.0f}ms fetch latency"),
        _criterion("liquidity_depth", min(100, volume / 10_000_000 * 100) if volume else 30, 0.10, f"${volume/1e6:.1f}M 24h volume" if volume else "volume unknown"),
        _criterion("price_stability", max(0, 100 - change_24h * 3), 0.08, f"24h move {change_24h:.1f}%"),
        _criterion("clean_quote_ratio", min(100, quotes_clean / max(connectors_polled, 1) * 100), 0.07, f"{quotes_clean} clean quotes"),
        _criterion("connector_success_rate", connectors_ok / max(connectors_polled, 1) * 100, 0.07, "connector success rate"),
        _criterion("vwap_available", 90 if pd.get("vwap_usd") else 30, 0.05, "VWAP computed" if pd.get("vwap_usd") else "no VWAP"),
        _criterion("live_path_available", 85 if any(s.get("is_live") for s in meta.get("sources_used", [])) else 50, 0.05, "WS/Redis live path"),
        _criterion("asset_tier", 90 if sym in {"BTC", "ETH"} else 70 if sym in {"SOL", "BNB", "XRP"} else 55, 0.05, f"{sym} liquidity tier"),
    ]

    weighted = sum(c["score"] * c["weight"] for c in criteria)
    total_weight = sum(c["weight"] for c in criteria)
    confidence = round(weighted / total_weight, 1) if total_weight else 50.0

    if confidence >= 80:
        band = "high"
        band_ar = "مرتفع"
    elif confidence >= 60:
        band = "moderate"
        band_ar = "متوسط"
    else:
        band = "low"
        band_ar = "منخفض"

    return {
        "feature_id": _FEATURE_ID,
        "phase": _PHASE,
        "phase_label": _PHASE_LABEL,
        "confidence_score": confidence,
        "confidence_band": band,
        "confidence_band_ar": band_ar,
        "display": f"Confidence: {_PHASE_LABEL} — {confidence:.0f}/100 ({band})",
        "display_ar": f"الثقة: {_PHASE_LABEL} — {confidence:.0f}/100 ({band_ar})",
        "criteria": criteria,
        "criteria_count": len(criteria),
        "no_ml_yet": True,
        "no_sharpe_promise": True,
        "performance_disclosure": _PERFORMANCE_DISCLOSURE,
        "roadmap": _ROADMAP,
        "timestamp": _utcnow(),
    }


async def score_asset_confidence(
    asset: str = "BTC",
    *,
    include_price_fetch: bool = True,
) -> dict[str, Any]:
    """Full confidence scoring for an asset."""
    t0 = time.perf_counter()
    sym = asset.upper().replace("/USDT", "")
    price_data: dict[str, Any] = {}
    market_data: dict[str, Any] = {}

    if include_price_fetch:
        try:
            from bd_platform.price_aggregation_engine import aggregate_prices

            price_data = await aggregate_prices(sym, use_cache=True)
            if price_data.get("validation"):
                price_data["price_verified"] = price_data["validation"].get("price_verified")
        except Exception:
            logger.debug("Price fetch for confidence failed", exc_info=True)

    try:
        from market_context import fetch_binance_ticker

        ticker = await fetch_binance_ticker(sym)
        if ticker:
            market_data = {
                "change_24h": float(ticker.get("change_pct") or ticker.get("change") or 0),
                "quote_volume": float(ticker.get("quote_volume") or 0),
            }
    except Exception:
        pass

    block = compute_rule_based_confidence(asset=sym, price_data=price_data, market_data=market_data)
    elapsed = time.perf_counter() - t0

    out = {
        "ok": True,
        "asset": sym,
        **block,
        "price_verified_badge": price_data.get("user_badge") or price_data.get("validation", {}).get("user_badge"),
        "latency_ms": round(elapsed * 1000, 1),
        "sla_met": elapsed <= 2.0,
        "timestamp": _utcnow(),
    }
    _append_score({**out, "stage": "score"})
    return out


def confidence_engine_status() -> dict[str, Any]:
    score_rows = 0
    if _SCORES_PATH.exists():
        score_rows = sum(1 for ln in _SCORES_PATH.read_text(encoding="utf-8").splitlines() if ln.strip())

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "phase": _PHASE,
        "phase_label": _PHASE_LABEL,
        "mode": "rule_based",
        "ml_enabled": False,
        "criteria_count": 13,
        "score_range": "0-100",
        "roadmap": _ROADMAP,
        "performance_disclosure": _PERFORMANCE_DISCLOSURE,
        "scores_logged": score_rows,
        "integrated_with": ["#125", "#133", "#147"],
        "timestamp": _utcnow(),
    }
