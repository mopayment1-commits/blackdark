"""Pre-Impact Protection and Portfolio Pre-Impact surface (DTS-028, DTS-045)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p3-pre-impact-1.0"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def evaluate_pre_impact(
    payload: dict[str, Any],
    *,
    envelope: dict[str, Any],
    portfolio_context: dict[str, Any],
    economics: dict[str, Any] | None = None,
    venue_health: dict[str, Any] | None = None,
    depeg: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Compute pre-decision portfolio impact; fail closed on material breach."""
    ctx_state = portfolio_context.get("state")
    if ctx_state == "PORTFOLIO_CONTEXT_UNAVAILABLE":
        return {
            "state": "UNAVAILABLE",
            "reason": "PORTFOLIO_CONTEXT_UNAVAILABLE",
            "portfolio_pre_impact": _unavailable_surface("no_legitimate_portfolio_context"),
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    current = envelope.get("current_use") or {}
    dims = envelope.get("dimensions") or {}
    opportunity_notional = _optional_float(payload.get("quote_amount") or payload.get("notional_usd")) or 0.0
    projected_loss = _optional_float((economics or {}).get("expected_net_edge_usd"))
    if projected_loss is not None and projected_loss < 0:
        projected_loss = abs(projected_loss)

    breached: list[str] = []
    near_limit: list[str] = []
    drivers: list[str] = []

    if current.get("state") == "AVAILABLE":
        conc = _optional_float(current.get("concentration_pct"))
        conc_limit = _limit(dims.get("concentration_pct"))
        if conc is not None and conc_limit is not None:
            projected_conc = _project_concentration(portfolio_context, opportunity_notional)
            if projected_conc is not None and projected_conc > conc_limit:
                breached.append("concentration_pct")
                drivers.append("post_trade_concentration_exceeds_limit")
            elif projected_conc is not None and projected_conc > conc_limit * 0.85:
                near_limit.append("concentration_pct")

        venue_pct = _optional_float(current.get("venue_exposure_pct"))
        venue_limit = _limit(dims.get("venue_exposure_pct"))
        venue = str(payload.get("buy_exchange") or payload.get("exchange") or "")
        if venue and venue_limit is not None and venue_pct is not None:
            projected_venue = _project_venue_exposure(portfolio_context, venue, opportunity_notional)
            if projected_venue is not None and projected_venue > venue_limit:
                breached.append("venue_exposure_pct")
                drivers.append(f"venue_exposure_{venue}")
            elif projected_venue is not None and projected_venue > venue_limit * 0.9:
                near_limit.append("venue_exposure_pct")

        loss_limit = _limit(dims.get("max_tolerated_loss_usd"))
        if loss_limit is not None and projected_loss is not None and projected_loss > loss_limit:
            breached.append("max_tolerated_loss_usd")
            drivers.append("projected_loss_exceeds_daily_limit")
    else:
        drivers.append("current_risk_use_unavailable")

    if venue_health and venue_health.get("decision_impact") in {"reject", "abstain"}:
        breached.append("venue_health")
        drivers.append("venue_health_" + str(venue_health.get("aggregate_health_state")))

    if depeg and depeg.get("decision_impact") in {"reject", "abstain"}:
        breached.append("depeg_risk")
        drivers.append("stablecoin_depeg_" + str(depeg.get("aggregate_risk_band")))

    material = bool(breached)
    decision_impact = "none"
    if "max_tolerated_loss_usd" in breached or "venue_health" in breached or depeg and depeg.get("decision_impact") == "reject":
        decision_impact = "reject"
    elif material:
        decision_impact = "abstain"
    elif near_limit:
        decision_impact = "degrade"

    surface = {
        "risk_before": current,
        "projected_risk_after": {
            "concentration_pct": _project_concentration(portfolio_context, opportunity_notional),
            "venue_exposure_pct": _project_venue_exposure(
                portfolio_context,
                str(payload.get("buy_exchange") or payload.get("exchange") or ""),
                opportunity_notional,
            ),
            "projected_loss_usd": projected_loss,
        },
        "violated_limits": breached,
        "approaching_limits": near_limit,
        "major_drivers": drivers,
        "decision_impact": decision_impact,
        "material": material,
        "why": [] if not material else [f"breach:{b}" for b in breached],
        "why_not": [] if not material else drivers,
    }

    return {
        "state": "AVAILABLE",
        "current_risk_use": current,
        "configured_limits": dims,
        "breached_dimensions": breached,
        "near_limit_dimensions": near_limit,
        "material_breach": material,
        "decision_impact": decision_impact,
        "portfolio_pre_impact": surface,
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
    }


def _unavailable_surface(reason: str) -> dict[str, Any]:
    return {
        "state": "UNAVAILABLE",
        "reason": reason,
        "risk_before": {"state": "UNAVAILABLE"},
        "projected_risk_after": {"state": "UNAVAILABLE"},
        "violated_limits": [],
        "approaching_limits": [],
        "major_drivers": [],
        "decision_impact": "none",
    }


def _limit(dim: dict[str, Any] | None) -> float | None:
    if not dim or dim.get("state") != "AVAILABLE":
        return None
    return _optional_float(dim.get("limit"))


def _project_concentration(portfolio_context: dict[str, Any], add_usd: float) -> float | None:
    holdings = portfolio_context.get("holdings") or []
    if not holdings:
        return None
    total = sum(float(h.get("value_usd") or 0) for h in holdings) + add_usd
    if total <= 0:
        return None
    max_pos = max(float(h.get("value_usd") or 0) for h in holdings) + add_usd
    return round(max_pos / total * 100.0, 4)


def _project_venue_exposure(portfolio_context: dict[str, Any], venue: str, add_usd: float) -> float | None:
    if not venue:
        return None
    holdings = portfolio_context.get("holdings") or []
    total = sum(float(h.get("value_usd") or 0) for h in holdings) + add_usd
    if total <= 0:
        return None
    venue_val = add_usd
    for h in holdings:
        if str(h.get("venue") or h.get("exchange") or "").lower() == venue.lower():
            venue_val += float(h.get("value_usd") or 0)
    return round(venue_val / total * 100.0, 4)
