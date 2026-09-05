"""
Portfolio AI Risk Tab — unified VaR + CVaR + Correlation + Stress (#1021-#1022-#1049-#1006).

Single ingest path from holdings (#907). Insight-only. Non-custodial.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from portfolio_correlation_analysis import compute_portfolio_correlation_from_holdings
from portfolio_cvar_metric import compute_portfolio_cvar_from_holdings
from portfolio_stress_testing import compute_portfolio_stress_from_holdings
from portfolio_var_metric import compute_portfolio_var_from_holdings

_FEATURE = "portfolio_risk_tab"


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def compute_portfolio_risk_tab(
    holdings: list[dict[str, Any]],
    *,
    confidence: float = 0.95,
    horizon_days: int = 1,
    lookback_days: int = 90,
) -> dict[str, Any]:
    """Risk Tab trio + stress — VaR never shown without CVaR."""
    var_metric = compute_portfolio_var_from_holdings(
        holdings, confidence=confidence, horizon_days=horizon_days, lookback_days=lookback_days
    )
    cvar_metric = compute_portfolio_cvar_from_holdings(
        holdings, confidence=confidence, horizon_days=horizon_days, lookback_days=lookback_days
    )
    correlation = compute_portfolio_correlation_from_holdings(holdings, lookback_days=lookback_days)
    stress = compute_portfolio_stress_from_holdings(
        holdings,
        var_usd=var_metric.get("var_usd") if var_metric.get("ok") else None,
        cvar_usd=cvar_metric.get("cvar_usd") if cvar_metric.get("ok") else None,
        lookback_days=lookback_days,
    )

    return {
        "ok": True,
        "feature": _FEATURE,
        "insight_only": True,
        "non_custodial": True,
        "confidence": confidence,
        "horizon_days": horizon_days,
        "lookback_days": lookback_days,
        "var_metric": var_metric,
        "cvar_metric": cvar_metric,
        "correlation_analysis": correlation,
        "stress_testing": stress,
        "risk_tab_trio": ["var", "cvar", "correlation"],
        "combined_disclaimer": (
            "VaR measures a percentile loss bound; CVaR measures average tail loss beyond VaR. "
            "Correlation warns of false diversification. Stress tests use historical extremes. "
            "None of these protect your portfolio or predict crises."
        ),
        "computed_at": _utcnow(),
    }


def portfolio_risk_tab_status() -> dict[str, Any]:
    from portfolio_correlation_analysis import portfolio_correlation_status
    from portfolio_cvar_metric import portfolio_cvar_status
    from portfolio_stress_testing import portfolio_stress_status
    from portfolio_var_metric import portfolio_var_status

    return {
        "ok": True,
        "feature": _FEATURE,
        "merged_into": "Portfolio AI Risk Tab",
        "standalone_rejected": True,
        "components": {
            "var": portfolio_var_status(),
            "cvar": portfolio_cvar_status(),
            "correlation": portfolio_correlation_status(),
            "stress": portfolio_stress_status(),
        },
        "timestamp": _utcnow(),
    }


def run_portfolio_risk_tab_e2e() -> dict[str, Any]:
    from portfolio_correlation_analysis import run_portfolio_correlation_e2e
    from portfolio_cvar_metric import run_portfolio_cvar_e2e
    from portfolio_stress_testing import run_portfolio_stress_e2e
    from portfolio_var_metric import run_portfolio_var_e2e

    checks: list[dict[str, Any]] = []
    for name, fn in [
        ("var", run_portfolio_var_e2e),
        ("cvar", run_portfolio_cvar_e2e),
        ("correlation", run_portfolio_correlation_e2e),
        ("stress", run_portfolio_stress_e2e),
    ]:
        result = fn()
        checks.append({"id": f"{name}_e2e", "passed": result.get("all_passed", False)})

    holdings = [
        {"symbol": "BTC", "value_usd": 60000, "btc_beta": 1.0},
        {"symbol": "ETH", "value_usd": 40000, "btc_beta": 1.1},
    ]
    tab = compute_portfolio_risk_tab(holdings)
    checks.append({"id": "unified_tab", "passed": tab.get("ok") is True})
    checks.append({"id": "var_and_cvar_together", "passed": tab["var_metric"].get("ok") and tab["cvar_metric"].get("ok")})
    checks.append({"id": "correlation_matrix", "passed": tab["correlation_analysis"].get("ok") is True})
    checks.append({"id": "stress_scenarios", "passed": tab["stress_testing"].get("ok") is True})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
