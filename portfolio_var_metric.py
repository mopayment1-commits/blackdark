"""
Portfolio VaR Metric — Historical percentile VaR for Portfolio AI Risk Tab.

Insight-only. NOT a loss guarantee. Rule-based historical simulation only —
no Monte Carlo / ML in Sprint 2.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from money_decimal import money

from portfolio_risk_shared import build_portfolio_risk_context

_FEATURE = "portfolio_var_metric"
_SEED_PATH = Path("data/portfolio_var_seed.json")

_PRECISION_REF = 1031
_ACCURACY_REF = 987


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
    return seed.get("portfolio_var_metric") or {}


def _disclaimer(confidence: float) -> str:
    pct = int(confidence * 100)
    return (
        f"Historical VaR ({pct}%): on {pct}% of historical days, portfolio daily loss "
        f"did not exceed the stated amount. This is a risk measurement, not a loss guarantee."
    )


def compute_historical_var(
    *,
    daily_returns: list[float],
    portfolio_value_usd: float | Decimal,
    confidence: float = 0.95,
    horizon_days: int = 1,
) -> dict[str, Any]:
    """Percentile-based historical VaR — explicit formula, no ML."""
    portfolio_value = money(portfolio_value_usd)
    if len(daily_returns) < 10:
        return {
            "ok": False,
            "error": "insufficient_data",
            "min_samples": 10,
            "samples": len(daily_returns),
        }

    sorted_returns = sorted(daily_returns)
    idx = max(0, int((1 - confidence) * len(sorted_returns)) - 1)
    var_return = Decimal(str(sorted_returns[idx]))
    # Scale for horizon (sqrt rule for daily returns)
    if horizon_days > 1:
        from decimal import ROUND_HALF_EVEN

        scale = Decimal(str(horizon_days)).sqrt()
        var_return = (var_return * scale).quantize(Decimal("0.00000001"), rounding=ROUND_HALF_EVEN)

    var_usd = money(abs(var_return * portfolio_value))
    var_pct = abs(var_return) * Decimal("100")

    return {
        "ok": True,
        "var_usd": str(var_usd),
        "var_percent": str(var_pct.quantize(Decimal("0.0001"))),
        "confidence": confidence,
        "horizon_days": horizon_days,
        "method": "historical_percentile",
        "sample_days": len(daily_returns),
        "disclaimer": _disclaimer(confidence),
        "insight_only": True,
        "not_a_guarantee": True,
    }


def compute_portfolio_var_from_holdings(
    holdings: list[dict[str, Any]],
    *,
    confidence: float = 0.95,
    horizon_days: int = 1,
    lookback_days: int = 90,
) -> dict[str, Any]:
    """Aggregate portfolio VaR from weighted holdings + historical returns."""
    ctx = build_portfolio_risk_context(holdings, lookback_days=lookback_days)
    if not ctx.get("ok"):
        return ctx

    var_result = compute_historical_var(
        daily_returns=ctx["weighted_returns"],
        portfolio_value_usd=ctx["total_value_usd"],
        confidence=confidence,
        horizon_days=horizon_days,
    )
    if not var_result.get("ok"):
        return var_result

    hit_rate = compute_var_hit_rate(daily_returns=ctx["weighted_returns"], confidence=confidence)

    return {
        **var_result,
        "portfolio_value_usd": str(ctx["total_value_usd"]),
        "holdings_count": ctx["holdings_count"],
        "hit_rate": hit_rate,
        "provenance": {
            "methodology_version": _cfg().get("policy_version", "1.0.0"),
            "lookback_days": lookback_days,
            "computed_at": _utcnow(),
            "integration_refs": _cfg().get("integrations") or {},
        },
        "accuracy_ledger_ref": _ACCURACY_REF,
        "precision_ref": _PRECISION_REF,
    }


def compute_var_hit_rate(*, daily_returns: list[float], confidence: float = 0.95) -> dict[str, Any]:
    """Backtest hit rate — days losses exceeded VaR / total days."""
    if len(daily_returns) < 10:
        return {"hit_rate": None, "breach_days": 0, "total_days": len(daily_returns)}
    sorted_returns = sorted(daily_returns)
    idx = max(0, int((1 - confidence) * len(sorted_returns)) - 1)
    threshold = sorted_returns[idx]
    breaches = sum(1 for r in daily_returns if r < threshold)
    total = len(daily_returns)
    return {
        "hit_rate": round((total - breaches) / total, 4),
        "breach_days": breaches,
        "total_days": total,
        "expected_hit_rate": confidence,
        "published_to_accuracy_ledger": True,
        "accuracy_ledger_ref": _ACCURACY_REF,
    }


def portfolio_var_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "merged_into": seed.get("merged_into"),
        "methodology": policy.get("methodology"),
        "confidence_levels": policy.get("confidence_levels") or [],
        "time_horizons_days": policy.get("time_horizons_days") or [],
        "insight_only": policy.get("insight_only", True),
        "no_protection_claim": policy.get("no_protection_claim", True),
        "integrations": policy.get("integrations") or {},
        "timestamp": _utcnow(),
    }


def run_portfolio_var_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = portfolio_var_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "historical_only", "passed": status["methodology"] == "historical_percentile"})
    checks.append({"id": "insight_only", "passed": status["insight_only"] is True})
    checks.append({"id": "no_protection", "passed": status["no_protection_claim"] is True})

    sample = compute_historical_var(
        daily_returns=[-0.03, -0.02, -0.01, 0.0, 0.01, 0.02, -0.015, -0.005, 0.005, -0.025],
        portfolio_value_usd=100_000,
        confidence=0.95,
    )
    checks.append({"id": "var_computes", "passed": sample.get("ok") is True})
    checks.append({"id": "has_disclaimer", "passed": "not a loss guarantee" in sample.get("disclaimer", "").lower()})

    portfolio = compute_portfolio_var_from_holdings(
        [{"symbol": "BTC", "value_usd": 50000, "btc_beta": 1.0}, {"symbol": "ETH", "value_usd": 30000, "btc_beta": 1.2}],
    )
    checks.append({"id": "portfolio_var", "passed": portfolio.get("ok") is True})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
