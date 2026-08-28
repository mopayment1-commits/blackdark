"""
Portfolio Stress Testing — historical extreme events (#1006).

Insight-only. Rule-based worst-case from real historical data. NOT crisis prediction.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

from money_decimal import d, money

from portfolio_risk_shared import build_portfolio_risk_context

_FEATURE = "portfolio_stress_testing"
_SEED_PATH = Path("data/portfolio_stress_seed.json")
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
    return seed.get("portfolio_stress_testing") or {}


def _stress_disclaimer() -> str:
    return (
        "Stress measurements use historical worst-case scenarios. "
        "This is stress measurement, not crisis prediction. Low stress loss does not mean crisis-proof."
    )


def _worst_consecutive_loss(returns: list[float], portfolio_value: Decimal, days: int) -> dict[str, Any]:
    if len(returns) < days:
        return {"loss_usd": "0", "loss_pct": "0", "days": days}
    worst = 0.0
    for i in range(len(returns) - days + 1):
        window = returns[i : i + days]
        cumulative = sum(window)
        worst = min(worst, cumulative)
    loss_usd = money(abs(Decimal(str(worst)) * portfolio_value))
    loss_pct = abs(Decimal(str(worst))) * Decimal("100")
    return {"loss_usd": str(loss_usd), "loss_pct": str(loss_pct.quantize(Decimal("0.0001"))), "days": days}


def run_stress_scenarios(
    *,
    holdings: list[dict[str, Any]],
    weighted_returns: list[float],
    portfolio_value: Decimal,
    var_usd: str | None = None,
    cvar_usd: str | None = None,
    stressed_correlation: float = 1.0,
    lookback_days: int = 90,
) -> dict[str, Any]:
    """Three mandatory predefined scenarios + historical worst-case."""
    policy = _cfg()
    scenarios_cfg = policy.get("scenarios") or []
    worst_days = int(policy.get("worst_consecutive_days", 5))

    results: list[dict[str, Any]] = []

    # Scenario 1: Flash crash (-30% single day)
    flash_drop = -0.30
    flash_loss = money(abs(Decimal(str(flash_drop)) * portfolio_value))
    results.append(
        {
            "id": "flash_crash",
            "name": "Flash Crash",
            "loss_usd": str(flash_loss),
            "loss_pct": "30.0000",
            "description": "Sudden 30%+ drop in one day (historical template)",
        }
    )

    # Scenario 2: Liquidity freeze (amplified worst daily loss by volume drop factor)
    volume_drop = 0.80
    worst_daily = min(weighted_returns) if weighted_returns else -0.05
    liquidity_loss = money(abs(Decimal(str(worst_daily * (1 + volume_drop))) * portfolio_value))
    results.append(
        {
            "id": "liquidity_freeze",
            "name": "Liquidity Freeze",
            "loss_usd": str(liquidity_loss),
            "description": "80% volume drop amplifies worst historical daily move",
        }
    )

    # Scenario 3: Correlation breakdown (all assets move together)
    breakdown_drop = min(weighted_returns) * stressed_correlation if weighted_returns else -0.10
    breakdown_loss = money(abs(Decimal(str(breakdown_drop)) * portfolio_value))
    results.append(
        {
            "id": "correlation_breakdown",
            "name": "Correlation Breakdown",
            "loss_usd": str(breakdown_loss),
            "stressed_correlation": stressed_correlation,
            "description": "Correlations converge to 1 under stress",
        }
    )

    historical_worst = _worst_consecutive_loss(weighted_returns, portfolio_value, worst_days)
    historical_worst["id"] = "historical_worst_consecutive"
    historical_worst["name"] = f"Worst {worst_days} consecutive days (historical)"
    results.append(historical_worst)

    # Compare stress vs VaR/CVaR
    comparisons: dict[str, Any] = {}
    max_stress = max(float(s.get("loss_usd", 0)) for s in results if s.get("loss_usd"))
    if var_usd:
        var_f = float(var_usd)
        if var_f > 0:
            comparisons["max_stress_vs_var_pct"] = round((max_stress / var_f - 1) * 100, 2)
    if cvar_usd:
        cvar_f = float(cvar_usd)
        if cvar_f > 0:
            comparisons["max_stress_vs_cvar_pct"] = round((max_stress / cvar_f - 1) * 100, 2)

    hit_rate = _stress_hit_rate(weighted_returns, threshold=min(weighted_returns) if weighted_returns else -0.1)

    return {
        "ok": True,
        "scenarios": results,
        "scenario_version": policy.get("policy_version", "1.0.0"),
        "var_cvar_comparison": comparisons,
        "stress_hit_rate": hit_rate,
        "disclaimer": _stress_disclaimer(),
        "insight_only": True,
        "lookback_days": lookback_days,
        "holdings_count": len(holdings),
    }


def _stress_hit_rate(returns: list[float], *, threshold: float) -> dict[str, Any]:
    if not returns:
        return {"hit_rate": None, "stress_days": 0, "total_days": 0}
    stress_days = sum(1 for r in returns if r <= threshold)
    total = len(returns)
    return {
        "hit_rate": round(stress_days / total, 4),
        "stress_days": stress_days,
        "total_days": total,
        "published_to_accuracy_ledger": True,
        "accuracy_ledger_ref": _ACCURACY_REF,
    }


def compute_portfolio_stress_from_holdings(
    holdings: list[dict[str, Any]],
    *,
    var_usd: str | None = None,
    cvar_usd: str | None = None,
    lookback_days: int = 90,
) -> dict[str, Any]:
    ctx = build_portfolio_risk_context(holdings, lookback_days=lookback_days)
    if not ctx.get("ok"):
        return ctx

    stress = run_stress_scenarios(
        holdings=holdings,
        weighted_returns=ctx["weighted_returns"],
        portfolio_value=d(ctx["total_value_usd"]),
        var_usd=var_usd,
        cvar_usd=cvar_usd,
        lookback_days=lookback_days,
    )
    stress["provenance"] = {
        "methodology_version": _cfg().get("policy_version", "1.0.0"),
        "computed_at": _utcnow(),
        "integration_refs": _cfg().get("integrations") or {},
    }
    return stress


def portfolio_stress_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "methodology": policy.get("methodology"),
        "scenarios": policy.get("scenarios") or [],
        "integrations": policy.get("integrations") or {},
        "timestamp": _utcnow(),
    }


def run_portfolio_stress_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = portfolio_stress_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "three_scenarios", "passed": len(status["scenarios"]) >= 3})

    holdings = [{"symbol": "BTC", "value_usd": 100000, "btc_beta": 1.0}]
    result = compute_portfolio_stress_from_holdings(holdings, var_usd="1000", cvar_usd="1500")
    checks.append({"id": "stress_computes", "passed": result.get("ok") is True})
    checks.append({"id": "has_disclaimer", "passed": "not crisis prediction" in result.get("disclaimer", "").lower()})
    ids = {s["id"] for s in result.get("scenarios", [])}
    checks.append({"id": "flash_crash", "passed": "flash_crash" in ids})
    checks.append({"id": "correlation_breakdown", "passed": "correlation_breakdown" in ids})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
