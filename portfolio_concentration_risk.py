"""
Portfolio Concentration Risk Alert — user-configurable position limits insight (#1052).

NOT standalone. Warns about excessive single-asset exposure — does NOT block trades.
Non-custodial · insight-only · no auto-rebalancing.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path
from typing import Any

from money_decimal import d, money

_FEATURE = "portfolio_concentration_risk"
_SEED_PATH = Path("data/portfolio_concentration_seed.json")
_THRESHOLDS_PATH = Path("data/user_concentration_thresholds.json")

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
    return seed.get("portfolio_concentration_risk") or {}


def _load_user_thresholds(user_id: int | None = None) -> dict[str, float]:
    default = float(_cfg().get("default_alert_threshold_pct", 30))
    if not _THRESHOLDS_PATH.is_file():
        return {"default_pct": default}
    try:
        data = json.loads(_THRESHOLDS_PATH.read_text(encoding="utf-8"))
        if user_id is not None and str(user_id) in data:
            return data[str(user_id)]
        return data.get("default", {"default_pct": default})
    except (OSError, json.JSONDecodeError):
        return {"default_pct": default}


def save_user_thresholds(user_id: int, thresholds: dict[str, float]) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if _THRESHOLDS_PATH.is_file():
        try:
            data = json.loads(_THRESHOLDS_PATH.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            data = {}
    data[str(user_id)] = thresholds
    _THRESHOLDS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _THRESHOLDS_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {"ok": True, "user_id": user_id, "thresholds": thresholds}


def compute_concentration(
    holdings: list[dict[str, Any]],
    *,
    user_id: int | None = None,
    per_asset_thresholds: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    concentration % = (position_value / total_portfolio_value) × 100
    Rule-based — backend only.
    """
    total = Decimal("0")
    for h in holdings:
        total += d(h.get("value_usd") or 0)
    if total <= 0:
        return {"ok": False, "error": "empty_portfolio"}

    user_thresh = per_asset_thresholds or _load_user_thresholds(user_id)
    default_pct = float(user_thresh.get("default_pct", 30))

    concentrations: list[dict[str, Any]] = []
    alerts: list[dict[str, Any]] = []
    max_concentration = Decimal("0")
    max_symbol = ""

    for h in holdings:
        symbol = str(h.get("symbol") or "UNKNOWN")
        value = d(h.get("value_usd") or 0)
        if value <= 0:
            continue
        pct = (value / total * Decimal("100")).quantize(Decimal("0.0001"), rounding=ROUND_HALF_EVEN)
        threshold = float(user_thresh.get(symbol, default_pct))
        row = {
            "symbol": symbol,
            "value_usd": str(money(value)),
            "concentration_pct": str(pct),
            "threshold_pct": threshold,
            "exceeded": float(pct) > threshold,
        }
        concentrations.append(row)
        if pct > max_concentration:
            max_concentration = pct
            max_symbol = symbol
        if row["exceeded"]:
            alerts.append(
                {
                    "symbol": symbol,
                    "concentration_pct": str(pct),
                    "threshold_pct": threshold,
                    "message_en": f"High concentration: {symbol} = {pct}% of portfolio (threshold {threshold}%)",
                    "message_ar": f"تركيز مرتفع: {symbol} = {pct}% من المحفظة (الحد {threshold}%)",
                    "alert_type": "in_app",
                }
            )

    risk_score_adjustment = 0
    if float(max_concentration) > 50:
        risk_score_adjustment = 2
    elif float(max_concentration) > default_pct:
        risk_score_adjustment = 1

    return {
        "ok": True,
        "total_value_usd": str(money(total)),
        "holdings_count": len(concentrations),
        "concentrations": concentrations,
        "alerts": alerts,
        "max_concentration": {"symbol": max_symbol, "pct": str(max_concentration)},
        "risk_score_adjustment": risk_score_adjustment,
        "insight_only": True,
        "no_execution": True,
        "disclaimer": _cfg().get(
            "disclaimer",
            "Platform warns about concentration — does not protect or block trades. Not financial advice.",
        ),
        "provenance": {
            "methodology_version": _cfg().get("policy_version", "1.0.0"),
            "computed_at": _utcnow(),
            "price_source_ref": 959,
            "positions_source_ref": 907,
        },
        "accuracy_ledger_ref": _ACCURACY_REF,
        "precision_ref": _PRECISION_REF,
    }


def escalate_with_correlation(
    concentration: dict[str, Any],
    *,
    high_correlation_pairs: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """High concentration + high correlation = combined risk escalation."""
    if not concentration.get("ok"):
        return concentration
    pairs = high_correlation_pairs or []
    escalated = list(concentration.get("alerts") or [])
    for alert in escalated:
        sym = alert["symbol"]
        for pair in pairs:
            if sym in {pair.get("asset_a"), pair.get("asset_b")}:
                try:
                    corr = float(pair.get("correlation", 0))
                except (TypeError, ValueError):
                    corr = 0
                if corr >= 0.85:
                    alert["combined_risk"] = "high_concentration_and_correlation"
                    alert["correlation"] = pair.get("correlation")
                    concentration["risk_score_adjustment"] = max(
                        int(concentration.get("risk_score_adjustment") or 0), 3
                    )
    concentration["alerts"] = escalated
    return concentration


def concentration_risk_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    policy = _cfg(seed)
    return {
        "ok": True,
        "feature": _FEATURE,
        "standalone_rejected": seed.get("standalone_rejected", True),
        "insight_only": policy.get("insight_only", True),
        "user_configurable_thresholds": policy.get("user_configurable_thresholds", True),
        "default_threshold_pct": policy.get("default_alert_threshold_pct", 30),
        "integrations": policy.get("integrations") or {},
        "timestamp": _utcnow(),
    }


def run_concentration_risk_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    status = concentration_risk_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "insight_only", "passed": status["insight_only"] is True})
    checks.append({"id": "user_thresholds", "passed": status["user_configurable_thresholds"] is True})

    holdings = [
        {"symbol": "BTC", "value_usd": 85000},
        {"symbol": "ETH", "value_usd": 15000},
    ]
    result = compute_concentration(holdings, per_asset_thresholds={"default_pct": 30})
    checks.append({"id": "btc_alert", "passed": len(result.get("alerts") or []) >= 1})
    checks.append({"id": "has_disclaimer", "passed": "does not protect" in result.get("disclaimer", "").lower()})

    all_passed = all(c["passed"] for c in checks)
    return {"ok": all_passed, "feature": _FEATURE, "all_passed": all_passed, "checks": checks, "timestamp": _utcnow()}
