"""
Strategy Vetting Algorithm — Feature #492 (Intelligence Ledger Sprint-2).

Strategy Quality Gate — evaluates strategies before display or reliance.
NOT standalone — merged into Intelligence Ledger.

Mandatory:
  - No guaranteed-return claims (auto-reject)
  - 6-factor score: backtest length, out-of-sample, max drawdown, turnover,
    Sharpe stability, regime coverage
  - Overfit penalty, small-sample penalty (< 100 trades = ineligible)
  - Versioned thresholds

Integrations:
  - #429 Unified Arbitrage: only grade ≥ B strategies displayed
  - #421 Strategy Simulator: paper portfolio uses approved strategies only
"""

from __future__ import annotations

import json
import logging
import re
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.StrategyVetting")

_FEATURE_ID = 492
_TITLE = "Strategy Quality Gate"
_LEGAL_NAME = "Strategy Vetting Algorithm"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Intelligence Ledger / Strategy Quality Gate"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/strategy_vetting_seed.json")
_METHODOLOGY_VERSION = "1.0"

_MANDATORY_FACTORS = (
    "backtest_length",
    "out_of_sample_period",
    "max_drawdown",
    "turnover",
    "sharpe_stability",
    "regime_coverage",
)

_BANNED_CLAIM_PATTERNS = (
    r"\bمضمون\b",
    r"\bربح مؤكد\b",
    r"\bguaranteed return\b",
    r"\bguaranteed profit\b",
    r"\brisk[- ]free return\b",
    r"\bمضمونة\b",
)

_MIN_ELIGIBLE_GRADE = "B"
_MIN_TRADE_COUNT = 100

_DISCLAIMER = (
    "Strategy Quality Gate — multi-factor vetting with overfit and small-sample penalties. "
    "No guaranteed-return claims permitted. Grade A–F with documented evidence. "
    "Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"strategies": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("strategy vetting seed load failed: %s", exc)
        return {"strategies": {}}


def _grade_from_score(score: float, *, seed: dict[str, Any]) -> str:
    thresholds = seed.get("grade_thresholds") or {}
    if score >= float(thresholds.get("A", 85)):
        return "A"
    if score >= float(thresholds.get("B", 70)):
        return "B"
    if score >= float(thresholds.get("C", 55)):
        return "C"
    if score >= float(thresholds.get("D", 40)):
        return "D"
    return "F"


def _grade_rank(grade: str) -> int:
    return {"A": 5, "B": 4, "C": 3, "D": 2, "F": 1}.get(grade, 0)


def _has_guaranteed_return_claim(strategy: dict[str, Any]) -> bool:
    text = " ".join(
        str(strategy.get(k, "")) for k in ("name", "description", "marketing_claim")
    ).lower()
    return any(re.search(p, text, re.IGNORECASE) for p in _BANNED_CLAIM_PATTERNS)


def vet_strategy(
    strategy_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#492 — multi-factor vetting with penalties and eligibility."""
    seed = seed or _load_seed()
    cfg = seed.get("vetting_config") or {}
    data = (seed.get("strategies") or {}).get(strategy_id)
    if not data:
        return {"ok": False, "strategy_id": strategy_id, "error": "strategy_not_found"}

    weaknesses: list[str] = []
    evidence: list[dict[str, Any]] = list(data.get("evidence_links") or [])

    if _has_guaranteed_return_claim(data):
        return {
            "ok": True,
            "feature_id": _FEATURE_ID,
            "strategy_id": strategy_id,
            "name": data.get("name"),
            "strategy_grade": "F",
            "eligible": False,
            "auto_rejected": True,
            "rejection_reason": "guaranteed_return_claim",
            "no_guaranteed_return_claims": True,
            "weaknesses": ["Contains prohibited guaranteed-return language"],
            "evidence": evidence,
            "thresholds_version": cfg.get("thresholds_version"),
            "display": f"Strategy {strategy_id} auto-rejected — guaranteed-return claim",
            "timestamp": _utcnow(),
        }

    trade_count = int(data.get("trade_count", 0))
    if trade_count < _MIN_TRADE_COUNT:
        return {
            "ok": True,
            "feature_id": _FEATURE_ID,
            "strategy_id": strategy_id,
            "name": data.get("name"),
            "strategy_grade": "F",
            "eligible": False,
            "small_sample_penalty": True,
            "trade_count": trade_count,
            "min_trade_count": _MIN_TRADE_COUNT,
            "weaknesses": [f"Sample size {trade_count} < {_MIN_TRADE_COUNT} trades"],
            "evidence": evidence,
            "thresholds_version": cfg.get("thresholds_version"),
            "display": f"Strategy {strategy_id} ineligible — small sample ({trade_count} trades)",
            "timestamp": _utcnow(),
        }

    weights = seed.get("factor_weights") or {}
    factors: dict[str, Any] = {}
    score = 0.0

    bt_months = float(data.get("backtest_months", 0))
    bt_score = min(100, bt_months / 24 * 100)
    factors["backtest_length"] = {"value": bt_months, "score": round(bt_score, 1)}
    score += bt_score * weights.get("backtest_length", 0.15)

    oos_pct = float(data.get("out_of_sample_pct", 0))
    oos_score = min(100, oos_pct * 2.5)
    factors["out_of_sample_period"] = {"value": oos_pct, "score": round(oos_score, 1)}
    score += oos_score * weights.get("out_of_sample_period", 0.20)
    if oos_pct < 20:
        weaknesses.append(f"Out-of-sample period low ({oos_pct}%)")

    mdd = float(data.get("max_drawdown_pct", 50))
    mdd_score = max(0, 100 - mdd * 3)
    factors["max_drawdown"] = {"value": mdd, "score": round(mdd_score, 1)}
    score += mdd_score * weights.get("max_drawdown", 0.20)
    if mdd > 25:
        weaknesses.append(f"Max drawdown elevated ({mdd}%)")

    turnover = float(data.get("turnover_annual", 5))
    turnover_score = max(0, 100 - turnover * 5)
    factors["turnover"] = {"value": turnover, "score": round(turnover_score, 1)}
    score += turnover_score * weights.get("turnover", 0.15)

    sharpe_stab = float(data.get("sharpe_stability", 0.5))
    sharpe_score = min(100, sharpe_stab * 100)
    factors["sharpe_stability"] = {"value": sharpe_stab, "score": round(sharpe_score, 1)}
    score += sharpe_score * weights.get("sharpe_stability", 0.15)

    regimes = int(data.get("regime_coverage_count", 1))
    regime_score = min(100, regimes * 25)
    factors["regime_coverage"] = {"value": regimes, "score": round(regime_score, 1)}
    score += regime_score * weights.get("regime_coverage", 0.15)
    if regimes < 3:
        weaknesses.append(f"Regime coverage limited ({regimes} regimes)")

    live_sharpe = float(data.get("live_sharpe", 0))
    backtest_sharpe = float(data.get("backtest_sharpe", 0))
    overfit_penalty = 0.0
    if backtest_sharpe > 0 and live_sharpe < backtest_sharpe * 0.6:
        overfit_penalty = min(30, (backtest_sharpe - live_sharpe) * 10)
        weaknesses.append(
            f"Overfit penalty: live Sharpe {live_sharpe:.2f} << backtest {backtest_sharpe:.2f}"
        )

    final_score = round(max(0, score - overfit_penalty), 1)
    grade = _grade_from_score(final_score, seed=seed)
    eligible = _grade_rank(grade) >= _grade_rank(_MIN_ELIGIBLE_GRADE)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "strategy_id": strategy_id,
        "name": data.get("name"),
        "strategy_grade": grade,
        "quality_score": final_score,
        "eligible": eligible,
        "min_display_grade": _MIN_ELIGIBLE_GRADE,
        "factors": factors,
        "mandatory_factors": list(_MANDATORY_FACTORS),
        "overfit_penalty": round(overfit_penalty, 1),
        "small_sample_penalty": False,
        "trade_count": trade_count,
        "weaknesses": weaknesses,
        "evidence": evidence,
        "out_of_sample_evidence": data.get("out_of_sample_evidence", True),
        "thresholds_version": cfg.get("thresholds_version"),
        "no_guaranteed_return_claims": True,
        "not_investment_advice": True,
        "display": (
            f"Strategy {strategy_id}: grade {grade} ({final_score}/100) | "
            f"{'eligible' if eligible else 'ineligible'}"
        ),
        "timestamp": _utcnow(),
    }


def list_vetted_strategies(
    *,
    eligible_only: bool = False,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    results = [vet_strategy(sid, seed=seed) for sid in (seed.get("strategies") or {})]
    valid = [r for r in results if r.get("ok")]
    if eligible_only:
        valid = [r for r in valid if r.get("eligible")]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "strategies": valid,
        "count": len(valid),
        "eligible_only": eligible_only,
        "min_display_grade": _MIN_ELIGIBLE_GRADE,
        "timestamp": _utcnow(),
    }


def is_strategy_eligible(strategy_id: str, *, seed: dict[str, Any] | None = None) -> bool:
    result = vet_strategy(strategy_id, seed=seed)
    return result.get("eligible") is True


def filter_displayable_strategies(
    strategy_ids: list[str],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#492 → #429: only grade ≥ B strategies for user display."""
    seed = seed or _load_seed()
    approved: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for sid in strategy_ids:
        vet = vet_strategy(sid, seed=seed)
        if vet.get("eligible"):
            approved.append(vet)
        else:
            rejected.append(vet)

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "integration": "unified_arbitrage_429",
        "approved": approved,
        "rejected": rejected,
        "approved_count": len(approved),
        "rejected_count": len(rejected),
        "min_display_grade": _MIN_ELIGIBLE_GRADE,
        "timestamp": _utcnow(),
    }


def build_approved_strategies_for_simulator(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#492 → #421: paper portfolio uses vetted strategies only."""
    vetted = list_vetted_strategies(eligible_only=True, seed=seed)
    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "integration": "strategy_simulator_421",
        "approved_strategies": vetted.get("strategies") or [],
        "count": vetted.get("count", 0),
        "simulation_only": True,
        "timestamp": _utcnow(),
    }


def build_strategy_quality_gate_panel(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    all_vetted = list_vetted_strategies(seed=seed)
    eligible = list_vetted_strategies(eligible_only=True, seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "merged_into": _MERGED_INTO,
        "strategies": all_vetted.get("strategies") or [],
        "eligible_strategies": eligible.get("strategies") or [],
        "total_count": all_vetted.get("count", 0),
        "eligible_count": eligible.get("count", 0),
        "thresholds_version": (seed.get("vetting_config") or {}).get("thresholds_version"),
        "mandatory_factors": list(_MANDATORY_FACTORS),
        "min_display_grade": _MIN_ELIGIBLE_GRADE,
        "no_guaranteed_return_claims": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def strategy_vetting_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "strategy_count": len(seed.get("strategies") or {}),
        "thresholds_version": (seed.get("vetting_config") or {}).get("thresholds_version"),
        "integrations": {
            "unified_arbitrage_429": True,
            "strategy_simulator_421": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "492"})
    checks.append({"id": "thresholds_versioned", "passed": (seed.get("vetting_config") or {}).get("thresholds_version") is not None, "detail": "version"})
    checks.append({"id": "six_factors", "passed": len(_MANDATORY_FACTORS) == 6, "detail": "factors"})

    good = vet_strategy("momentum_cross_venue", seed=seed)
    checks.append({"id": "eligible_strategy", "passed": good.get("eligible") is True and good.get("strategy_grade") in ("A", "B"), "detail": good.get("strategy_grade")})

    bad_claim = vet_strategy("guaranteed_alpha", seed=seed)
    checks.append({"id": "reject_guaranteed_claim", "passed": bad_claim.get("auto_rejected") is True, "detail": "claim"})

    small = vet_strategy("low_sample_scalper", seed=seed)
    checks.append({"id": "small_sample_penalty", "passed": small.get("small_sample_penalty") is True, "detail": "trades"})

    overfit = vet_strategy("overfit_momentum", seed=seed)
    checks.append({"id": "overfit_penalty", "passed": overfit.get("overfit_penalty", 0) > 0, "detail": "overfit"})

    filter_result = filter_displayable_strategies(list((seed.get("strategies") or {}).keys()), seed=seed)
    checks.append({"id": "grade_b_filter_429", "passed": filter_result.get("approved_count", 0) >= 1, "detail": "429"})

    sim = build_approved_strategies_for_simulator(seed=seed)
    checks.append({"id": "simulator_421", "passed": sim.get("count", 0) >= 1, "detail": "421"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
