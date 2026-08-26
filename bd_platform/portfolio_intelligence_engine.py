"""
Portfolio Intelligence Engine — Feature #449 (Sprint-1 Existing).

Renamed from "Portfolio AI" — quantitative portfolio analytics, not a new module.
Integrates existing Sprint-1 Portfolio AI surfaces with mandatory risk integrations.

Merged: #448, #450 into same ticket.
Cancelled: Sharpe ≥1.5, Max Drawdown ≤15%, Win Rate ≥55% acceptance SLAs.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.PortfolioIntelligenceEngine")

_FEATURE_ID = 449
_TITLE = "Portfolio Intelligence Engine"
_LEGAL_NAME = "Portfolio Intelligence Engine"
_RENAMED_FROM = "Portfolio AI"
_STANDALONE = False
_MERGED_INTO = "Portfolio AI / Sprint-1 Existing"
_SPRINT = 1
_PRIORITY = "medium"
_SEED_PATH = Path("data/portfolio_intelligence_engine_seed.json")
_METHODOLOGY_VERSION = "1.0"

_DISCLAIMER = (
    "Portfolio Intelligence — quantitative analytics across existing Portfolio AI modules. "
    "Not investment advice. No automatic execution."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"existing_module": True}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("portfolio intelligence engine seed load failed: %s", exc)
        return {"existing_module": True}


def build_integrated_panel(portfolio_id: str = "demo_portfolio") -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = _load_seed()

    from bd_platform.capital_protection_controls import build_capital_awareness_panel
    from bd_platform.live_breakeven_tracker import build_live_breakeven_panel
    from bd_platform.strategy_simulator import build_strategy_simulator_panel

    capital = build_capital_awareness_panel(portfolio_id)
    breakeven = build_live_breakeven_panel("pos_btc_001")
    simulator = build_strategy_simulator_panel()

    net_edge_sample = None
    portfolio_net_edge = None
    try:
        from bd_platform.net_edge_truth_layer import build_portfolio_net_edge_scores

        portfolio_net_edge = build_portfolio_net_edge_scores(portfolio_id)
        if portfolio_net_edge.get("opportunities"):
            net_edge_sample = portfolio_net_edge["opportunities"][0]
        elif portfolio_net_edge.get("holdings"):
            net_edge_sample = portfolio_net_edge["holdings"][0]
    except Exception:
        logger.debug("net edge sample skipped", exc_info=True)

    fill_risk_sample = None
    try:
        from bd_platform.fill_risk_assessment import build_fill_risk_panel

        fill_risk_sample = build_fill_risk_panel()
    except Exception:
        logger.debug("fill risk sample skipped", exc_info=True)

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "existing_module": True,
        "no_new_module_built": seed.get("no_new_module_built", True),
        "portfolio_id": portfolio_id,
        "capital_protection_410": capital,
        "live_breakeven_404": breakeven,
        "strategy_simulator_411": simulator,
        "net_edge_truth_417_sample": net_edge_sample,
        "net_edge_truth_417_portfolio": portfolio_net_edge,
        "fill_risk_assessment_433_sample": fill_risk_sample,
        "merged_features": seed.get("merged_features") or [448, 450],
        "performance_sla_cancelled": seed.get("sharpe_drawdown_winrate_sla_cancelled", True),
        "risk_adjusted_metrics": {
            "drawdown_pct": (capital.get("portfolio_summary") or {}).get("current_drawdown_pct"),
            "risk_budget_used_pct": (capital.get("risk_budget") or {}).get("budget_used_pct"),
            "breakeven_distance": (breakeven.get("dynamic_breakeven") or {}).get("distance_to_breakeven_pct"),
        },
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def portfolio_intelligence_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "existing_module": True,
        "no_new_module_built": True,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "merged_features": seed.get("merged_features") or [448, 450],
        "integrations": seed.get("integrations") or {},
        "performance_sla_cancelled": seed.get("sharpe_drawdown_winrate_sla_cancelled", True),
        "surface": "portfolio_ai",
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "existing_module", "passed": seed.get("existing_module") is True, "detail": "sprint-1"})
    checks.append({"id": "no_new_module", "passed": seed.get("no_new_module_built") is True, "detail": "reuse"})
    checks.append({"id": "renamed_portfolio_intelligence", "passed": seed.get("legal_name") == "Portfolio Intelligence Engine", "detail": "renamed"})
    checks.append({"id": "sla_cancelled", "passed": seed.get("sharpe_drawdown_winrate_sla_cancelled") is True, "detail": "SLA"})

    panel = build_integrated_panel()
    checks.append({"id": "capital_protection_410", "passed": panel.get("capital_protection_410", {}).get("ok") is True, "detail": "410"})
    checks.append({"id": "live_breakeven_404", "passed": panel.get("live_breakeven_404", {}).get("ok") is True, "detail": "404"})
    checks.append({"id": "merged_448_450", "passed": 448 in (seed.get("merged_features") or []) and 450 in (seed.get("merged_features") or []), "detail": "merged"})

    checks.append({"id": "net_edge_truth_417", "passed": panel.get("net_edge_truth_417_portfolio", {}).get("ok") is True, "detail": "417"})

    passed = sum(1 for c in checks if c["passed"])
    return {"ok": passed == len(checks), "feature_id": _FEATURE_ID, "checks": checks, "passed": passed, "total": len(checks), "timestamp": _utcnow()}
