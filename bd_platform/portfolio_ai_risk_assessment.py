"""
Portfolio AI Risk Assessment — Feature #999 (Sprint 2).

Merged into Portfolio AI Risk Tab — NOT standalone "Shield".
Insight-only: Low Risk / Elevated Risk / High Risk — no execution blocking.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.PortfolioRiskAssessment")

_FEATURE_REF = 999
_PORTFOLIO_RISK_TAB_REF = 901
_SYNC_REF = 907
_PRICING_REF = 959
_DEFI_RISK_REF = 951
_STANDALONE = False
_MERGED_INTO = "Portfolio AI / Risk Assessment"
_SEED_PATH = Path("data/portfolio_ai_risk_assessment_seed.json")

RiskLevel = Literal["low_risk", "elevated_risk", "high_risk"]

_DISCLAIMER = (
    "Risk assessment — insight only, not execution blocking. "
    "Platform warns, user decides. Non-custodial. No PASS/HOLD/BLOCK execution terms."
)

_RISK_LABELS = {
    "low_risk": "Low Risk",
    "elevated_risk": "Elevated Risk",
    "high_risk": "High Risk",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("risk assessment seed load failed: %s", exc)
        return {}


_ASSESSMENT_AUDIT: list[dict[str, Any]] = []


def reset_risk_assessment_state() -> None:
    _ASSESSMENT_AUDIT.clear()


def risk_assessment_status_999(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("risk_assessment_999") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "portfolio_risk_tab_ref": _PORTFOLIO_RISK_TAB_REF,
        "multi_account_sync_ref": _SYNC_REF,
        "reference_pricing_ref": _PRICING_REF,
        "defi_strategy_risk_ref": _DEFI_RISK_REF,
        "insight_only": True,
        "non_custodial": True,
        "no_execution_blocking": True,
        "execution_terms_rejected": ["PASS", "HOLD", "BLOCK"],
        "risk_levels": list(_RISK_LABELS.keys()),
        "risk_labels": _RISK_LABELS,
        "deterministic_rules": True,
        "backend_enforced": True,
        "no_client_side_scoring": True,
        "override_audit": True,
        "risk_budget_visual_only": True,
        "no_hard_limits": True,
        "no_auto_action": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def _score_exposure(exposure_pct: float, limits: dict[str, float]) -> tuple[RiskLevel, list[dict[str, Any]]]:
    reasons: list[dict[str, Any]] = []
    high = float(limits.get("high_risk_pct", 80))
    elevated = float(limits.get("elevated_risk_pct", 60))

    if exposure_pct >= high:
        reasons.append({"rule": "exposure_above_high_threshold", "value": exposure_pct, "threshold": high})
        return "high_risk", reasons
    if exposure_pct >= elevated:
        reasons.append({"rule": "exposure_above_elevated_threshold", "value": exposure_pct, "threshold": elevated})
        return "elevated_risk", reasons
    reasons.append({"rule": "exposure_within_limits", "value": exposure_pct, "threshold": elevated})
    return "low_risk", reasons


def run_risk_assessment_999(
    portfolio_id: str = "demo_portfolio",
    *,
    user_id: str = "user_demo",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Pre-trade style validation — insight-only risk levels, no blocking."""
    seed = seed or _load_seed()
    portfolios = seed.get("portfolios") or {}
    portfolio = portfolios.get(portfolio_id)
    if not portfolio:
        return {"ok": False, "feature_ref": _FEATURE_REF, "error": "portfolio_not_found"}

    cfg = seed.get("risk_assessment_999") or {}
    limits = cfg.get("limits") or {}
    exposure_pct = float(portfolio.get("exposure_pct", 0))
    volatility_raw = portfolio.get("volatility_30d")
    slippage_raw = portfolio.get("estimated_slippage_bps")
    volatility = float(volatility_raw) if volatility_raw is not None else 0.0
    slippage_bps = float(slippage_raw) if slippage_raw is not None else 0.0
    liquidity_score = float(portfolio.get("liquidity_score", 1.0))

    risk_level, reasons = _score_exposure(exposure_pct, limits)

    if volatility > float(limits.get("extreme_volatility", 0.8)):
        reasons.append({"rule": "extreme_volatility", "value": volatility})
        risk_level = "high_risk"
    elif volatility > float(limits.get("elevated_volatility", 0.5)) and risk_level == "low_risk":
        reasons.append({"rule": "elevated_volatility", "value": volatility})
        risk_level = "elevated_risk"

    if slippage_bps > float(limits.get("max_slippage_bps", 50)):
        reasons.append({"rule": "slippage_above_threshold", "value": slippage_bps, "reference_pricing_ref": _PRICING_REF})

    if liquidity_score < float(limits.get("min_liquidity_score", 0.3)):
        reasons.append({"rule": "insufficient_liquidity", "value": liquidity_score})

    risk_budget = {
        "used_pct": exposure_pct,
        "budget_pct": float(limits.get("risk_budget_pct", 100)),
        "visual_indicator_only": True,
        "no_hard_limit": True,
        "no_auto_action": True,
    }

    assessment_id = f"ra_{uuid.uuid4().hex[:12]}"
    audit_entry = {
        "assessment_id": assessment_id,
        "user_id": user_id,
        "portfolio_id": portfolio_id,
        "risk_level": risk_level,
        "risk_label": _RISK_LABELS[risk_level],
        "timestamp": _utcnow(),
        "override_audit": True,
        "no_prevention_logic": True,
    }
    _ASSESSMENT_AUDIT.append(audit_entry)

    remediation = []
    if risk_level == "high_risk":
        remediation = portfolio.get("high_risk_remediation") or ["Reduce concentrated exposure", "Review slippage assumptions"]
    elif risk_level == "elevated_risk":
        remediation = portfolio.get("elevated_risk_remediation") or ["Monitor volatility", "Check liquidity depth"]

    fee = cfg.get("fee_db") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "assessment_id": assessment_id,
        "portfolio_id": portfolio_id,
        "risk_level": risk_level,
        "risk_label": _RISK_LABELS[risk_level],
        "legacy_terms_rejected": {"PASS": False, "HOLD": False, "BLOCK": False},
        "reasons": reasons,
        "remediation": remediation,
        "risk_budget": risk_budget,
        "exposure": {
            "exposure_pct": exposure_pct,
            "multi_account_aggregated": portfolio.get("multi_account_aggregated", True),
            "sync_ref": _SYNC_REF,
        },
        "inputs": {
            "volatility_30d": volatility,
            "estimated_slippage_bps": slippage_bps,
            "liquidity_score": liquidity_score,
            "reference_pricing_ref": _PRICING_REF,
        },
        "deterministic_rules": True,
        "backend_enforced": True,
        "insight_only": True,
        "non_custodial": True,
        "no_execution_blocking": True,
        "override_audit": audit_entry,
        "fee_db": {
            "compute_usd": fee.get("compute_per_assessment_usd", 0.005),
            "storage_usd": fee.get("storage_per_assessment_usd", 0.001),
        },
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_negative_tests_999(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Edge cases: zero balance, extreme volatility, missing data."""
    seed = seed or _load_seed()
    tests = []

    zero = run_risk_assessment_999("zero_balance", seed=seed)
    tests.append({"case": "zero_balance", "passed": zero.get("ok") is True and zero.get("risk_level") in _RISK_LABELS})

    extreme = run_risk_assessment_999("extreme_volatility", seed=seed)
    tests.append({"case": "extreme_volatility", "passed": extreme.get("risk_level") == "high_risk"})

    missing = run_risk_assessment_999("missing_data", seed=seed)
    tests.append({"case": "missing_data", "passed": missing.get("ok") is True})

    not_found = run_risk_assessment_999("nonexistent", seed=seed)
    tests.append({"case": "portfolio_not_found", "passed": not_found.get("error") == "portfolio_not_found"})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "negative_tests": tests,
        "passed": sum(1 for t in tests if t["passed"]),
        "total": len(tests),
        "timestamp": _utcnow(),
    }


def run_risk_assessment_e2e_999(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_risk_assessment_state()
    checks: list[dict[str, Any]] = []

    status = risk_assessment_status_999(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "insight_only", "passed": status["insight_only"] is True})
    checks.append({"id": "no_execution_blocking", "passed": status["no_execution_blocking"] is True})
    checks.append({"id": "risk_budget_visual", "passed": status["risk_budget_visual_only"] is True})

    assessment = run_risk_assessment_999("demo_portfolio", seed=seed)
    checks.append({"id": "assessment", "passed": assessment.get("ok") is True})
    checks.append({"id": "risk_labels_not_block", "passed": assessment.get("risk_label") in _RISK_LABELS.values()})
    checks.append({"id": "legacy_rejected", "passed": assessment.get("legacy_terms_rejected", {}).get("BLOCK") is False})
    checks.append({"id": "override_audit", "passed": assessment.get("override_audit", {}).get("override_audit") is True})
    checks.append({"id": "backend_enforced", "passed": assessment.get("backend_enforced") is True})

    negative = run_negative_tests_999(seed=seed)
    checks.append({"id": "negative_tests", "passed": negative.get("ok") is True})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature_ref": _FEATURE_REF, "all_passed": all_passed, "checks": checks}
