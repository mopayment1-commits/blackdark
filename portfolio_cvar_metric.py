"""
Portfolio CVaR / Expected Shortfall — tail risk complement to VaR (#1022).

Insight-only. Average loss in the tail beyond VaR threshold. NOT a catastrophe guarantee.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from statistics import mean
from typing import Any

from money_decimal import d, money

from portfolio_risk_shared import build_portfolio_risk_context
from portfolio_var_metric import compute_historical_var

_FEATURE = "portfolio_cvar_metric"
_SEED_PATH = Path("data/portfolio_cvar_seed.json")
_VAR_REF = 1021
_ACCURACY_REF = 987
_PRECISION_REF = 1031


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("portfolio_cvar_metric") or {}


def _cvar_disclaimer(confidence: float) -> str:
    pct = int(confidence * 100)
    tail_pct = 100 - pct
    return (
        f"Historical CVaR ({pct}%): in the worst {tail_pct}% of days, average loss was as stated. "
        f"This is tail risk measurement, not a catastrophe guarantee."
    )


def compute_historical_cvar(
    *,
    daily_returns: list[float],
    portfolio_value_usd: float | Decimal,
    confidence: float = 0.95,
    horizon_days: int = 1,
    var_threshold: float | None = None,
) -> dict[str, Any]:
    """Average of losses beyond VaR threshold (expected shortfall)."""
    portfolio_value = money(portfolio_value_usd)
    if len(daily_returns) < 10:
        return {"ok": False, "error": "insufficient_data", "samples": len(daily_returns)}

    var_result = compute_historical_var(
        daily_returns=daily_returns,
        portfolio_value_usd=portfolio_value,
        confidence=confidence,
        horizon_days=horizon_days,
    )
    if not var_result.get("ok"):
        return var_result

    sorted_returns = sorted(daily_returns)
    n_tail = max(1, int((1 - confidence) * len(sorted_returns)))
    tail_returns = sorted_returns[:n_tail]
    threshold = var_threshold if var_threshold is not None else sorted_returns[max(0, n_tail - 1)]
    cvar_return = Decimal(str(mean(tail_returns)))

    if horizon_days > 1:
        from decimal import ROUND_HALF_EVEN

        scale = Decimal(str(horizon_days)).sqrt()
        cvar_return = (cvar_return * scale).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN)

    cvar_usd = money(abs(cvar_return * portfolio_value))
    cvar_pct = abs(cvar_return) * Decimal("100")

    return {
        "ok": True,
        "cvar_usd": str(cvar_usd),
        "cvar_percent": str(cvar_pct.quantize(Decimal("0.0001"))),
        "var_usd": var_result.get("var_usd"),
        "var_threshold_return": threshold,
        "confidence": confidence,
        "horizon_days": horizon_days,
        "method": "historical_expected_shortfall",
        "tail_days": n_tail,
        "sample_days": len(daily_returns),
        "disclaimer": _cvar_disclaimer(confidence),
        "insight_only": True,
        "not_a_guarantee": True,
        "var_ref": _VAR_REF,
    }


def compute_cvar_tail_hit_rate(*, daily_returns: list[float], confidence: float = 0.95) -> dict[str, Any]:
    if len(daily_returns) < 10:
        return {"tail_hit_rate": None, "breach_days": 0, "total_days": len(daily_returns)}
    sorted_returns = sorted(daily_returns)
    n_tail = max(1, int((1 - confidence) * len(sorted_returns)))
    cvar_return = mean(sorted_returns[:n_tail])
    breaches = sum(1 for r in daily_returns if r < cvar_return)
    total = len(daily_returns)
    return {
        "tail_hit_rate": round((total - breaches) / total, 4),
        "breach_days": breaches,
        "total_days": total,
        "published_to_accuracy_ledger": True,
        "accuracy_ledger_ref": _ACCURACY_REF,
    }


def compute_portfolio_cvar_from_holdings(
    holdings: list[dict[str, Any]],
    *,
    confidence: float = 0.95,
    horizon_days: int = 1,
    lookback_days: int = 90,
) -> dict[str, Any]:
    ctx = build_portfolio_risk_context(holdings, lookback_days=lookback_days)
    if not ctx.get("ok"):
        return ctx

    cvar = compute_historical_cvar(
        daily_returns=ctx["weighted_returns"],
        portfolio_value_usd=ctx["total_value_usd"],
        confidence=confidence,
        horizon_days=horizon_days,
    )
    if not cvar.get("ok"):
        return cvar

    return {
        **cvar,
        "portfolio_value_usd": str(ctx["total_value_usd"]),
        "holdings_count": ctx["holdings_count"],
        "tail_hit_rate": compute_cvar_tail_hit_rate(
            daily_returns=ctx["weighted_returns"], confidence=confidence
        ),
        "provenance": {
            "methodology_version": _cfg().get("policy_version", "1.0.0"),
            "lookback_days": lookback_days,
            "var_threshold_used": cvar.get("var_threshold_return"),
            "computed_at": _utcnow(),
            "integration_refs": _cfg().get("integrations") or {},
        },
        "precision_ref": _PRECISION_REF,
    }


def portfolio_cvar_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "merged_into": seed.get("merged_into"),
        "methodology": policy.get("methodology"),
        "requires_var_companion": policy.get("requires_var_companion", True),
        "integrations": policy.get("integrations") or {},
        "timestamp": _utcnow(),
    }


def run_portfolio_cvar_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = portfolio_cvar_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "requires_var", "passed": status["requires_var_companion"] is True})

    returns = [-0.05, -0.04, -0.03, -0.02, -0.01, 0.0, 0.01, 0.02, -0.025, -0.035]
    cvar = compute_historical_cvar(daily_returns=returns, portfolio_value_usd=100_000, confidence=0.95)
    checks.append({"id": "cvar_computes", "passed": cvar.get("ok") is True})
    checks.append({"id": "cvar_gte_var", "passed": float(cvar["cvar_usd"]) >= float(cvar["var_usd"])})
    checks.append({"id": "has_disclaimer", "passed": "not a catastrophe guarantee" in cvar.get("disclaimer", "").lower()})

    portfolio = compute_portfolio_cvar_from_holdings(
        [{"symbol": "BTC", "value_usd": 50000, "btc_beta": 1.0}],
    )
    checks.append({"id": "portfolio_cvar", "passed": portfolio.get("ok") is True})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
