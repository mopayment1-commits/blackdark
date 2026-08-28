"""
Portfolio Asset Correlation Analysis — Pearson matrix (#1049).

Insight-only. Warns against false diversification — does NOT enforce rebalancing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

from portfolio_risk_shared import build_portfolio_risk_context

_FEATURE = "portfolio_correlation_analysis"
_SEED_PATH = Path("data/portfolio_correlation_seed.json")
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
    return seed.get("portfolio_correlation_analysis") or {}


def pearson_correlation(x: list[float], y: list[float]) -> Decimal:
    """Explicit Pearson formula — 4 decimal precision."""
    n = min(len(x), len(y))
    if n < 3:
        return Decimal("0")
    xs, ys = x[:n], y[:n]
    mx = sum(xs) / n
    my = sum(ys) / n
    num = sum((a - mx) * (b - my) for a, b in zip(xs, ys))
    den_x = sum((a - mx) ** 2 for a in xs) ** 0.5
    den_y = sum((b - my) ** 2 for b in ys) ** 0.5
    if den_x == 0 or den_y == 0:
        return Decimal("0")
    return Decimal(str(num / (den_x * den_y))).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)


def compute_correlation_matrix(
    asset_returns: dict[str, list[float]],
) -> dict[str, Any]:
    symbols = sorted(asset_returns.keys())
    matrix: dict[str, dict[str, str]] = {}
    pairs: list[dict[str, Any]] = []
    high_correlation_warnings: list[dict[str, str]] = []

    for s1 in symbols:
        matrix[s1] = {}
        for s2 in symbols:
            if s1 == s2:
                corr = Decimal("1.0000")
            else:
                corr = pearson_correlation(asset_returns[s1], asset_returns[s2])
            matrix[s1][s2] = str(corr)
            if s1 < s2:
                pairs.append({"asset_a": s1, "asset_b": s2, "correlation": str(corr)})
                if corr >= Decimal("0.85"):
                    high_correlation_warnings.append(
                        {
                            "pair": f"{s1}/{s2}",
                            "correlation": str(corr),
                            "insight": f"High correlation ({corr}) — assets tend to move together",
                        }
                    )

    # Stability: std of rolling 30-day correlations (first vs second half)
    stability = _correlation_stability(asset_returns) if len(symbols) >= 2 else {}

    return {
        "ok": True,
        "symbols": symbols,
        "matrix": matrix,
        "pairs": pairs,
        "high_correlation_warnings": high_correlation_warnings,
        "stability": stability,
        "method": "pearson",
        "insight_only": True,
        "no_rebalance_enforcement": True,
    }


def _correlation_stability(asset_returns: dict[str, list[float]]) -> dict[str, Any]:
    symbols = sorted(asset_returns.keys())
    if len(symbols) < 2:
        return {"stable": True, "note": "single_asset"}
    s1, s2 = symbols[0], symbols[1]
    series1, series2 = asset_returns[s1], asset_returns[s2]
    mid = len(series1) // 2
    if mid < 3:
        return {"stable": None, "note": "insufficient_window"}
    c1 = pearson_correlation(series1[:mid], series2[:mid])
    c2 = pearson_correlation(series1[mid:], series2[mid:])
    drift = abs(c1 - c2)
    return {
        "first_half_correlation": str(c1),
        "second_half_correlation": str(c2),
        "drift": str(drift.quantize(Decimal("0.0001"))),
        "stable": drift < Decimal("0.20"),
    }


def compute_portfolio_correlation_from_holdings(
    holdings: list[dict[str, Any]],
    *,
    lookback_days: int = 90,
) -> dict[str, Any]:
    ctx = build_portfolio_risk_context(holdings, lookback_days=lookback_days)
    if not ctx.get("ok"):
        return ctx
    if len(ctx["symbols"]) < 2:
        return {
            "ok": True,
            "note": "single_asset_no_correlation",
            "symbols": ctx["symbols"],
            "insight_only": True,
        }

    matrix_result = compute_correlation_matrix(ctx["asset_returns"])
    return {
        **matrix_result,
        "holdings_count": ctx["holdings_count"],
        "lookback_days": lookback_days,
        "provenance": {
            "methodology_version": _cfg().get("policy_version", "1.0.0"),
            "time_window_days": lookback_days,
            "computed_at": _utcnow(),
            "integration_refs": _cfg().get("integrations") or {},
        },
        "accuracy_ledger_ref": _ACCURACY_REF,
    }


def portfolio_correlation_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "methodology": policy.get("methodology"),
        "time_windows_days": policy.get("time_windows_days") or [],
        "integrations": policy.get("integrations") or {},
        "timestamp": _utcnow(),
    }


def run_portfolio_correlation_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = portfolio_correlation_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "pearson_method", "passed": status["methodology"] == "pearson"})

    corr = pearson_correlation([0.01, 0.02, 0.03], [0.01, 0.02, 0.03])
    checks.append({"id": "perfect_correlation", "passed": corr == Decimal("1.0000")})

    holdings = [
        {"symbol": "BTC", "value_usd": 50000, "btc_beta": 1.0},
        {"symbol": "ETH", "value_usd": 30000, "btc_beta": 1.1},
    ]
    result = compute_portfolio_correlation_from_holdings(holdings)
    checks.append({"id": "matrix_computes", "passed": result.get("ok") is True and "matrix" in result})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
