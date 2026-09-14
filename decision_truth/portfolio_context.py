"""Legitimate user-specific portfolio context (DTS-057)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p3-portfolio-context-1.0"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def resolve_portfolio_context(payload: dict[str, Any]) -> dict[str, Any]:
    """Resolve portfolio context only from explicit user-provided or authenticated sources."""
    user_id = payload.get("user_id")
    explicit_holdings = payload.get("portfolio_holdings") or payload.get("holdings")
    risk_settings = payload.get("user_risk_settings") or payload.get("risk_preferences")
    portfolio_summary = payload.get("portfolio_summary")

    if explicit_holdings and isinstance(explicit_holdings, list) and len(explicit_holdings) > 0:
        normalized = []
        total = 0.0
        for row in explicit_holdings:
            if not isinstance(row, dict):
                continue
            value = _optional_float(row.get("value_usd") or row.get("notional_usd"))
            if value is None:
                continue
            normalized.append(
                {
                    "asset": str(row.get("asset") or row.get("symbol") or "UNKNOWN").upper(),
                    "value_usd": value,
                    "venue": row.get("exchange") or row.get("venue"),
                    "source": row.get("source") or "user_provided",
                }
            )
            total += value
        if normalized:
            return {
                "state": "AVAILABLE",
                "source": "USER_PROVIDED_HOLDINGS",
                "user_id": user_id,
                "holdings": normalized,
                "total_value_usd": round(total, 4),
                "risk_settings": _normalize_risk_settings(risk_settings),
                "methodology_version": METHODOLOGY_VERSION,
                "timestamp_utc": _utc_now(),
                "assumptions": ["holdings_explicitly_supplied_by_caller"],
            }

    if portfolio_summary and isinstance(portfolio_summary, dict) and portfolio_summary.get("status") not in {"not_connected", "unavailable"}:
        holdings = portfolio_summary.get("holdings") or []
        if holdings:
            return {
                "state": "AVAILABLE",
                "source": "PORTFOLIO_SUMMARY",
                "user_id": user_id,
                "holdings": holdings,
                "total_value_usd": _optional_float(portfolio_summary.get("total_value_usd")),
                "risk_settings": _normalize_risk_settings(risk_settings or portfolio_summary.get("risk_settings")),
                "methodology_version": METHODOLOGY_VERSION,
                "timestamp_utc": _utc_now(),
            }

    if risk_settings and user_id is not None:
        return {
            "state": "PARTIAL",
            "source": "USER_RISK_SETTINGS_ONLY",
            "user_id": user_id,
            "holdings": [],
            "total_value_usd": None,
            "risk_settings": _normalize_risk_settings(risk_settings),
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
            "reason": "portfolio_holdings_unavailable",
        }

    return {
        "state": "PORTFOLIO_CONTEXT_UNAVAILABLE",
        "source": "none",
        "user_id": user_id,
        "holdings": [],
        "total_value_usd": None,
        "risk_settings": None,
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
        "reason": "no_legitimate_portfolio_or_risk_data",
    }


def _normalize_risk_settings(raw: Any) -> dict[str, Any] | None:
    if not isinstance(raw, dict):
        return None
    out: dict[str, Any] = {"origin": "USER_CONFIGURED"}
    for key in ("max_slippage_bps", "max_risk_score", "max_daily_loss_usd", "max_drawdown_pct", "max_concentration_pct", "max_leverage"):
        if key in raw and raw[key] is not None:
            out[key] = raw[key]
    return out if len(out) > 1 else None
