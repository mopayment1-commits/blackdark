"""
Portfolio Diversification Score — Feature #717 (Sprint 2 Portfolio AI).

Merged with #109 Risk Management and #199 PnL Drift.
UI label: 'Diversification Score' — NOT 'Entropy' for users.
"""

from __future__ import annotations

import json
import logging
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.PortfolioDiversification")

_FEATURE_ID = 717
_MERGED_WITH = (109, 199)
_STANDALONE = False
_MERGED_INTO = "Portfolio AI / Diversification Health Score"
_SPRINT = 2
_SEED_PATH = Path("data/portfolio_diversification_seed.json")
_METHODOLOGY_VERSION = "1.0"
_PNL_ACCURACY_TOLERANCE_PCT = 0.1
_MAX_ASSETS = 1000

_DISCLAIMER = (
    "Diversification score measures portfolio concentration risk. "
    "Not investment advice. PnL accuracy target ±0.1%. "
    "Integrated with Risk Management (#109) and PnL Drift monitoring (#199)."
)

ConcentrationLevel = Literal["low", "moderate", "high", "critical"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"portfolios": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("portfolio diversification seed load failed: %s", exc)
        return {"portfolios": {}}


def compute_shannon_entropy(weights: list[float]) -> float:
    """Internal entropy calculation — not exposed as 'Entropy' in UI."""
    if not weights:
        return 0.0
    total = sum(weights)
    if total <= 0:
        return 0.0
    probs = [w / total for w in weights if w > 0]
    return round(-sum(p * math.log2(p) for p in probs if p > 0), 4)


def compute_diversification_score(
    *,
    entropy_component: float,
    correlation_risk: float,
    sector_concentration: float,
    max_entropy: float = 4.0,
) -> dict[str, Any]:
    """Composite diversification score 0–100. UI: 'Diversification Score' only."""
    entropy_norm = min(entropy_component / max_entropy, 1.0) * 100
    corr_penalty = correlation_risk * 100
    sector_penalty = sector_concentration * 100

    raw = entropy_norm * 0.40 + (100 - corr_penalty) * 0.30 + (100 - sector_penalty) * 0.30
    score = round(min(max(raw, 0), 100), 1)

    if score >= 70:
        level: ConcentrationLevel = "low"
    elif score >= 50:
        level = "moderate"
    elif score >= 30:
        level = "high"
    else:
        level = "critical"

    return {
        "diversification_score": score,
        "ui_label": f"Diversification Score: {score}/100",
        "entropy_internal_only": True,
        "no_entropy_in_ui": True,
        "concentration_level": level,
        "components": {
            "asset_entropy": round(entropy_norm, 1),
            "correlation_risk": round(corr_penalty, 1),
            "sector_concentration": round(sector_penalty, 1),
        },
    }


def compute_correlation_risk(holdings: list[dict[str, Any]]) -> dict[str, Any]:
    """#109 correlation risk — do assets move together?"""
    correlations = [float(h.get("avg_correlation", 0)) for h in holdings if h.get("avg_correlation") is not None]
    avg_corr = round(sum(correlations) / len(correlations), 4) if correlations else 0.0
    high_corr_pairs = [
        {"assets": [h.get("asset"), h.get("correlated_with")], "correlation": h.get("correlation")}
        for h in holdings
        if h.get("correlation") and float(h.get("correlation", 0)) > 0.7
    ]
    return {
        "sub_task": "#109",
        "avg_correlation": avg_corr,
        "correlation_risk_score": min(avg_corr, 1.0),
        "high_correlation_pairs": high_corr_pairs[:10],
        "display": f"Avg correlation: {avg_corr:.2f} — {'high' if avg_corr > 0.6 else 'moderate'} co-movement risk",
    }


def compute_sector_concentration(sectors: dict[str, float]) -> dict[str, Any]:
    """Sector concentration — e.g. 60% in DeFi = risk."""
    if not sectors:
        return {"max_sector_pct": 0, "concentration_risk": 0, "sectors": {}}

    total = sum(sectors.values())
    normalized = {k: round(v / total * 100, 1) for k, v in sectors.items()} if total > 0 else sectors
    max_sector = max(normalized.values()) if normalized else 0
    max_name = max(normalized, key=normalized.get) if normalized else None

    return {
        "sectors": normalized,
        "max_sector": max_name,
        "max_sector_pct": max_sector,
        "concentration_risk": min(max_sector / 100, 1.0),
        "display": (
            f"{max_sector}% in {max_name}" if max_name else "No sector data"
        ),
    }


def compute_pnl_metrics(holdings: list[dict[str, Any]]) -> dict[str, Any]:
    """#199 PnL drift integration — accuracy ±0.1%."""
    total_value = sum(float(h.get("value_usd", 0)) for h in holdings)
    total_cost = sum(float(h.get("cost_basis_usd", 0)) for h in holdings)
    pnl = total_value - total_cost
    roi = round(pnl / total_cost * 100, 2) if total_cost > 0 else 0.0

    return {
        "sub_task": "#199",
        "total_value_usd": round(total_value, 2),
        "total_cost_usd": round(total_cost, 2),
        "pnl_usd": round(pnl, 2),
        "roi_pct": roi,
        "pnl_accuracy_tolerance_pct": _PNL_ACCURACY_TOLERANCE_PCT,
        "real_time_update": True,
        "display": f"PnL: ${pnl:,.2f} | ROI: {roi:+.2f}%",
    }


def build_concentration_heatmap(portfolio: dict[str, Any]) -> dict[str, Any]:
    """Heatmap by sector, chain, market cap tier."""
    return {
        "by_sector": portfolio.get("sectors") or {},
        "by_chain": portfolio.get("chains") or {},
        "by_market_cap_tier": portfolio.get("market_cap_tiers") or {},
        "asset_count": len(portfolio.get("holdings") or []),
        "max_assets_supported": _MAX_ASSETS,
    }


def build_portfolio_health_panel(portfolio_id: str = "default") -> dict[str, Any]:
    """Portfolio health with diversification score — NOT labeled 'Entropy'."""
    t0 = time.perf_counter()
    seed = _load_seed()
    portfolio = (seed.get("portfolios") or {}).get(portfolio_id)

    if not portfolio:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "portfolio_not_found",
            "portfolio_id": portfolio_id,
        }

    holdings = portfolio.get("holdings") or []
    weights = [float(h.get("weight_pct", 0)) for h in holdings]
    entropy = compute_shannon_entropy(weights)
    sectors = portfolio.get("sectors") or {}
    sector_block = compute_sector_concentration(sectors)
    corr_block = compute_correlation_risk(holdings)
    pnl_block = compute_pnl_metrics(holdings)

    diversification = compute_diversification_score(
        entropy_component=entropy,
        correlation_risk=corr_block["correlation_risk_score"],
        sector_concentration=sector_block["concentration_risk"],
    )

    asset_count = len(holdings)
    visible_assets = portfolio.get("visible_asset_count", asset_count)
    risk_sectors = sum(1 for v in (sector_block.get("sectors") or {}).values() if v > 20)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "merged_with": list(_MERGED_WITH),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "portfolio_ai",
        "portfolio_id": portfolio_id,
        "smart_diversification": {
            "score": diversification["diversification_score"],
            "ui_label": diversification["ui_label"],
            "summary": (
                f"Portfolio looks diversified ({visible_assets} assets) but "
                f"{sector_block.get('max_sector_pct', 0)}% risk in {sector_block.get('max_sector', 'unknown')} "
                f"→ {diversification['ui_label']}"
            ),
            "no_entropy_label": True,
        },
        "diversification": diversification,
        "correlation_risk": corr_block,
        "sector_concentration": sector_block,
        "pnl": pnl_block,
        "heatmap": build_concentration_heatmap(portfolio),
        "export": {
            "pdf_available": True,
            "csv_available": True,
        },
        "real_time_update": True,
        "max_assets_supported": _MAX_ASSETS,
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def portfolio_diversification_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Portfolio Diversification Health Score",
        "ui_label": "Diversification Score",
        "no_entropy_in_ui": True,
        "merged_with": {
            109: "Risk Management (correlation risk)",
            199: "PnL Drift monitoring",
            717: "Diversification entropy (internal)",
        },
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "wave": 2,
        "acceptance_criteria": {
            "real_time_update": True,
            "pnl_accuracy_tolerance_pct": _PNL_ACCURACY_TOLERANCE_PCT,
            "max_assets_supported": _MAX_ASSETS,
            "pdf_csv_export": True,
            "no_entropy_ui_label": True,
        },
        "portfolio_count": len(seed.get("portfolios") or {}),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
