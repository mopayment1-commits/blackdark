"""Reverse Stress Testing (DTS-016)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p3-reverse-stress-1.0"

SCENARIO_FACTORS = (
    "price_shock",
    "depeg",
    "venue_failure",
    "liquidity_evaporation",
    "funding_spike",
    "correlation_convergence",
    "oracle_failure",
    "bridge_failure",
)


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def _optional_float(raw: Any) -> float | None:
    if raw is None:
        return None
    try:
        return float(raw)
    except (TypeError, ValueError):
        return None


def evaluate_reverse_stress(
    payload: dict[str, Any],
    *,
    envelope: dict[str, Any],
    portfolio_context: dict[str, Any],
) -> dict[str, Any]:
    """Identify scenarios that would breach configured limits."""
    current = envelope.get("current_use") or {}
    if current.get("state") != "AVAILABLE":
        return {
            "state": "UNAVAILABLE",
            "reason": "insufficient_portfolio_for_reverse_stress",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    dims = envelope.get("dimensions") or {}
    loss_limit = _limit_value(dims.get("max_tolerated_loss_usd"))
    dd_limit = _limit_value(dims.get("drawdown_pct"))
    conc_limit = _limit_value(dims.get("concentration_pct"))
    if loss_limit is None and dd_limit is None and conc_limit is None:
        return {
            "state": "UNAVAILABLE",
            "reason": "no_configured_limits_for_stress",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    total = float(current.get("total_value_usd") or 0)
    scenarios: list[dict[str, Any]] = []

    if loss_limit is not None and total > 0:
        shock_pct = (loss_limit / total) * 100.0
        scenarios.append(
            _scenario(
                factor="price_shock",
                breached_constraint="max_tolerated_loss_usd",
                threshold=loss_limit,
                scenario={"price_shock_pct": round(-shock_pct, 4)},
                severity="high" if shock_pct < 10 else "medium",
                assumptions=["linear_portfolio_loss_proxy", "no_hedge_offset_modeled"],
            )
        )

    if dd_limit is not None:
        scenarios.append(
            _scenario(
                factor="price_shock",
                breached_constraint="drawdown_pct",
                threshold=dd_limit,
                scenario={"drawdown_pct": dd_limit},
                severity="high",
                assumptions=["peak_to_trough_proxy"],
            )
        )

    conc = _optional_float(current.get("concentration_pct"))
    if conc_limit is not None and conc is not None and conc < conc_limit:
        gap = conc_limit - conc
        scenarios.append(
            _scenario(
                factor="correlation_convergence",
                breached_constraint="concentration_pct",
                threshold=conc_limit,
                scenario={"additional_concentration_pct": round(gap + 5, 4)},
                severity="medium",
                assumptions=["incremental_allocation_to_top_holding"],
            )
        )

    buy_ex = str(payload.get("buy_exchange") or payload.get("buy_venue") or "")
    if buy_ex:
        scenarios.append(
            _scenario(
                factor="venue_failure",
                breached_constraint="venue_exposure_pct",
                threshold=_limit_value(dims.get("venue_exposure_pct")),
                scenario={"venue": buy_ex.lower(), "withdrawal_blocked": True},
                severity="high",
                assumptions=["single_venue_exposure_at_risk"],
            )
        )

    symbol = str(payload.get("symbol") or payload.get("asset") or "")
    if any(stable in symbol.upper() for stable in ("USDT", "USDC", "DAI")):
        scenarios.append(
            _scenario(
                factor="depeg",
                breached_constraint="stablecoin_exposure_pct",
                threshold=_limit_value(dims.get("stablecoin_exposure_pct")),
                scenario={"stablecoin_deviation_pct": 2.0},
                severity="high",
                assumptions=["stablecoin_leg_in_opportunity"],
            )
        )

    if not scenarios:
        return {
            "state": "UNAVAILABLE",
            "reason": "no_defensible_reverse_stress_scenarios",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    return {
        "state": "AVAILABLE",
        "scenarios": scenarios,
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
        "uncertainty": {"state": "AVAILABLE", "confidence": "medium", "method": "limit_inversion_proxy"},
        "live_validation": "LIVE_VALIDATION_PENDING",
    }


def _limit_value(dim: dict[str, Any] | None) -> float | None:
    if not dim or dim.get("state") != "AVAILABLE":
        return None
    return _optional_float(dim.get("limit"))


def _scenario(
    *,
    factor: str,
    breached_constraint: str,
    threshold: float | None,
    scenario: dict[str, Any],
    severity: str,
    assumptions: list[str],
) -> dict[str, Any]:
    return {
        "factor": factor,
        "breached_constraint": breached_constraint,
        "threshold": threshold,
        "scenario": scenario,
        "severity": severity,
        "assumptions": assumptions,
    }
