"""Exchange / venue health decision integration (DTS-029)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

METHODOLOGY_VERSION = "dts-p3-venue-health-1.0"


def _utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def evaluate_venue_health_decision(payload: dict[str, Any]) -> dict[str, Any]:
    """Bind canonical venue health signals to decision impact."""
    venues = []
    for key in ("buy_exchange", "sell_exchange", "exchange", "buy_venue", "sell_venue"):
        val = payload.get(key)
        if val:
            venues.append(str(val).lower())
    venues = list(dict.fromkeys(venues))
    if not venues:
        return {
            "state": "NOT_APPLICABLE",
            "reason": "no_venue_in_opportunity",
            "methodology_version": METHODOLOGY_VERSION,
            "timestamp_utc": _utc_now(),
        }

    explicit = payload.get("venue_health")
    evaluated: list[dict[str, Any]] = []
    for venue in venues:
        if isinstance(explicit, dict) and explicit.get("venue") == venue:
            evaluated.append(_normalize_health(venue, explicit))
            continue
        try:
            from bd_platform.whales_institutional_layer import build_exchange_health_80

            raw = build_exchange_health_80(exchange=venue)
            evaluated.append(_normalize_health(venue, raw))
        except Exception as exc:
            evaluated.append(
                {
                    "venue": venue,
                    "health_state": "UNAVAILABLE",
                    "health_score": None,
                    "reason_codes": ["health_module_error", str(exc)],
                    "freshness": {"state": "UNAVAILABLE"},
                    "decision_impact": "abstain",
                }
            )

    worst = _worst_impact(evaluated)
    return {
        "state": "AVAILABLE",
        "venues": evaluated,
        "aggregate_health_state": worst["health_state"],
        "decision_impact": worst["decision_impact"],
        "reason_codes": worst.get("reason_codes") or [],
        "methodology_version": METHODOLOGY_VERSION,
        "timestamp_utc": _utc_now(),
        "live_validation": "LIVE_VALIDATION_PENDING",
    }


def _normalize_health(venue: str, raw: dict[str, Any]) -> dict[str, Any]:
    score = raw.get("health_score")
    if score is None:
        return {
            "venue": venue,
            "health_state": "UNAVAILABLE",
            "health_score": None,
            "reason_codes": ["missing_health_score"],
            "freshness": {"state": "UNKNOWN", "source": raw.get("source")},
            "decision_impact": "abstain",
        }
    try:
        score_f = float(score)
    except (TypeError, ValueError):
        return {
            "venue": venue,
            "health_state": "UNAVAILABLE",
            "health_score": None,
            "reason_codes": ["invalid_health_score"],
            "freshness": {"state": "UNKNOWN"},
            "decision_impact": "abstain",
        }

    if venue == "ftx" or score_f < 35:
        impact = "reject"
        state = "critical"
        codes = ["critical_venue_health"]
    elif score_f < 55:
        impact = "abstain"
        state = "degraded"
        codes = ["degraded_venue_health"]
    elif score_f < 70:
        impact = "degrade"
        state = "warning"
        codes = ["elevated_venue_risk"]
    else:
        impact = "contextual_warning" if score_f < 80 else "none"
        state = "healthy"
        codes = []

    withdrawal = ((raw.get("indicators") or {}).get("withdrawal_velocity") or {}).get("value")
    if withdrawal == "elevated":
        codes.append("elevated_withdrawal_velocity")
        if impact == "none":
            impact = "degrade"
            state = "warning"

    return {
        "venue": venue,
        "health_state": state,
        "health_score": score_f,
        "reason_codes": codes,
        "freshness": {"state": "AVAILABLE", "source": "build_exchange_health_80"},
        "current_exposure": raw.get("current_exposure"),
        "decision_impact": impact,
        "indicators": raw.get("indicators"),
    }


def _worst_impact(venues: list[dict[str, Any]]) -> dict[str, Any]:
    order = {"reject": 4, "abstain": 3, "degrade": 2, "contextual_warning": 1, "none": 0}
    worst = venues[0] if venues else {"health_state": "UNAVAILABLE", "decision_impact": "abstain", "reason_codes": []}
    for row in venues[1:]:
        if order.get(row.get("decision_impact"), 0) > order.get(worst.get("decision_impact"), 0):
            worst = row
    return worst
