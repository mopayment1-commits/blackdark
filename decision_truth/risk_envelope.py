"""Risk Budget / Risk Envelope (DTS-027)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p3-risk-envelope-1.0"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def _dim(value: float | None, *, origin: str, applicable: bool = True, reason: str | None = None) -> dict[str, Any]:
    if not applicable:
        return {"state": "NOT_APPLICABLE", "origin": origin, "reason": reason or "not_applicable"}
    if value is None:
        return {"state": "UNAVAILABLE", "origin": origin, "reason": reason or "missing_evidence"}
    return {"state": "AVAILABLE", "origin": origin, "limit": value}


def build_risk_envelope(payload: dict[str, Any], *, portfolio_context: dict[str, Any]) -> dict[str, Any]:
    """Build machine-readable risk envelope without inventing user preferences."""
    user_settings = portfolio_context.get("risk_settings") or {}
    policy = {
        "max_daily_loss_usd": _optional_float(os.getenv("USER_DEFAULT_MAX_DAILY_LOSS_USD", "500")),
        "max_drawdown_pct": _optional_float(os.getenv("RISK_MAX_DRAWDOWN_PCT", "15")),
        "max_concentration_pct": _optional_float(os.getenv("RISK_MAX_CONCENTRATION_PCT", "40")),
        "max_leverage": _optional_float(os.getenv("RISK_MAX_LEVERAGE", "3")),
        "max_venue_exposure_pct": _optional_float(os.getenv("RISK_MAX_VENUE_EXPOSURE_PCT", "50")),
        "max_stablecoin_exposure_pct": _optional_float(os.getenv("RISK_MAX_STABLECOIN_EXPOSURE_PCT", "60")),
        "max_counterparty_exposure_pct": _optional_float(os.getenv("RISK_MAX_COUNTERPARTY_EXPOSURE_PCT", "50")),
        "min_liquidity_coverage_ratio": _optional_float(os.getenv("RISK_MIN_LIQUIDITY_COVERAGE", "1.2")),
    }

    def _limit(key: str, env_key: str) -> dict[str, Any]:
        if key in user_settings:
            return _dim(_optional_float(user_settings[key]), origin="USER_CONFIGURED")
        if policy.get(env_key) is not None:
            return _dim(policy[env_key], origin="SYSTEM_DERIVED", reason="policy_defined_default")
        return _dim(None, origin="SYSTEM_DERIVED", reason="policy_unconfigured")

    holdings = portfolio_context.get("holdings") or []
    has_portfolio = portfolio_context.get("state") == "AVAILABLE" and bool(holdings)

    current_use = _current_risk_use(holdings) if has_portfolio else {"state": "UNAVAILABLE", "reason": "portfolio_holdings_unavailable"}

    envelope = {
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
        "portfolio_context_state": portfolio_context.get("state"),
        "dimensions": {
            "max_tolerated_loss_usd": _limit("max_daily_loss_usd", "max_daily_loss_usd"),
            "drawdown_pct": _limit("max_drawdown_pct", "max_drawdown_pct"),
            "concentration_pct": _limit("max_concentration_pct", "max_concentration_pct"),
            "leverage": _limit("max_leverage", "max_leverage"),
            "liquidity_coverage": _dim(policy["min_liquidity_coverage_ratio"], origin="SYSTEM_DERIVED", reason="policy_defined_default"),
            "venue_exposure_pct": _limit("max_venue_exposure_pct", "max_venue_exposure_pct"),
            "stablecoin_exposure_pct": _limit("max_stablecoin_exposure_pct", "max_stablecoin_exposure_pct"),
            "counterparty_exposure_pct": _limit("max_counterparty_exposure_pct", "max_counterparty_exposure_pct"),
        },
        "current_use": current_use,
        "policy_disclosed": True,
    }
    return envelope


def _current_risk_use(holdings: list[dict[str, Any]]) -> dict[str, Any]:
    total = sum(float(h.get("value_usd") or 0) for h in holdings)
    if total <= 0:
        return {"state": "UNAVAILABLE", "reason": "zero_portfolio_value"}
    max_pos = max(float(h.get("value_usd") or 0) for h in holdings)
    concentration = max_pos / total * 100.0
    venues: dict[str, float] = {}
    stable = 0.0
    for h in holdings:
        asset = str(h.get("asset") or "")
        value = float(h.get("value_usd") or 0)
        venue = str(h.get("venue") or h.get("exchange") or "unknown")
        venues[venue] = venues.get(venue, 0.0) + value
        if asset in {"USDT", "USDC", "DAI", "BUSD", "USD"}:
            stable += value
    top_venue_pct = max(venues.values()) / total * 100.0 if venues else None
    return {
        "state": "AVAILABLE",
        "concentration_pct": round(concentration, 4),
        "venue_exposure_pct": round(top_venue_pct, 4) if top_venue_pct is not None else None,
        "stablecoin_exposure_pct": round(stable / total * 100.0, 4),
        "total_value_usd": round(total, 4),
        "holdings_count": len(holdings),
    }
