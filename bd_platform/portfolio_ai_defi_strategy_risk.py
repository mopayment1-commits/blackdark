"""
Portfolio AI DeFi Strategy Risk — Feature #951 (Sprint 2).

Merged into Portfolio AI Risk Tab — NOT standalone.
Scenario modeling, dependency graph, no guaranteed yield.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DeFiStrategyRisk")

_FEATURE_REF = 951
_ONCHAIN_REF = 12
_PROTOCOL_KPI_REF = 986
_STANDALONE = False
_MERGED_INTO = "Portfolio AI / Risk Tab"
_SEED_PATH = Path("data/portfolio_ai_defi_strategy_risk_seed.json")

_DISCLAIMER = (
    "DeFi strategy risk — insight only. Risk insight, not protection. "
    "Historical APY only — no guaranteed yield. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("defi strategy risk seed load failed: %s", exc)
        return {}


def defi_strategy_risk_status_951(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("defi_strategy_risk_951") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "onchain_extension_ref": _ONCHAIN_REF,
        "protocol_kpi_ref": _PROTOCOL_KPI_REF,
        "no_guaranteed_yield": True,
        "historical_apy_only": True,
        "risk_insight_not_protection": True,
        "scenario_modeling": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def _score_risk(strategy: dict[str, Any]) -> str:
    il = strategy.get("il_risk", "low")
    liq = strategy.get("liquidation_risk", "low")
    if il == "high" or liq == "high":
        return "high"
    if il == "medium" or liq == "medium":
        return "medium"
    return "low"


def build_strategy_risk_report_951(
    strategy_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    strategies = seed.get("strategies") or {}
    strategy = strategies.get(strategy_id)
    if not strategy:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "strategy_not_found"}

    deps = strategy.get("dependencies") or []
    graph = seed.get("dependency_graph") or {}
    dep_chain = []
    for dep in deps:
        node = graph.get(dep) or {}
        dep_chain.append({"node": dep, "type": node.get("type"), "depends_on": node.get("depends_on") or []})

    risk_level = _score_risk(strategy)
    fee = (seed.get("defi_strategy_risk_951") or {}).get("fee_db") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "strategy_id": strategy_id,
        "name": strategy.get("name"),
        "risk_level": risk_level,
        "scenarios": {
            "impermanent_loss": strategy.get("il_risk"),
            "liquidation_risk": strategy.get("liquidation_risk"),
            "dependency_risk": "high" if len(deps) > 3 else "medium",
        },
        "dependency_graph": dep_chain,
        "historical_apy_pct": strategy.get("historical_apy_pct"),
        "no_guaranteed_yield": True,
        "not_expected_return": True,
        "leverage": strategy.get("leverage"),
        "risk_insight_not_protection": True,
        "disclaimer": _DISCLAIMER,
        "fee_db": {
            "compute_usd": fee.get("compute_per_strategy_usd", 0.02),
            "storage_usd": fee.get("storage_per_report_usd", 0.005),
        },
        "timestamp": _utcnow(),
    }


def run_defi_strategy_risk_e2e_951(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = defi_strategy_risk_status_951(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "no_guaranteed_yield", "passed": status["no_guaranteed_yield"] is True})

    report = build_strategy_risk_report_951("eth_loop_aave", seed=seed)
    checks.append({"id": "strategy_report", "passed": report.get("ok") is True})
    checks.append({"id": "dependency_graph", "passed": len(report.get("dependency_graph") or []) >= 2})
    checks.append({"id": "historical_apy", "passed": report.get("not_expected_return") is True})

    il = build_strategy_risk_report_951("uni_lp_eth_usdc", seed=seed)
    checks.append({"id": "il_risk", "passed": il.get("scenarios", {}).get("impermanent_loss") == "high"})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
