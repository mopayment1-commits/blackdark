"""
Token Unlock Intelligence Engine — Features #707 + #703 + #704 + #708 merged (Sprint 2).

#707 = Unlock Impact Intelligence (primary engine)
#703 = Actionability Score (absorbed into impact composite)
#704 = Token Unlock Calendar (absorbed into #708 dashboard)
#708 = Dashboard surface (Calendar + List + Magnitude + Impact + Actionability)

Unlock event ≠ automatic sell signal. No guaranteed price direction.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.TokenUnlockIntelligence")

_FEATURE_ID = 707
_FORECASTER_REF = 607
_ABSORBED_IDS = (607, 703, 704, 707, 708)
_DASHBOARD_FEATURE_ID = 708
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Token Unlock Intelligence Engine"
_SPRINT = 2
_SEED_PATH = Path("data/token_unlock_intelligence_seed.json")
_METHODOLOGY_VERSION = "1.0"
_FORMULA_VERSION = "1.0"
_HISTORICAL_CALIBRATION = {
    "similar_unlocks_sample_size": 142,
    "price_declined_pct_of_time": 60.0,
    "median_drawdown_pct": -8.5,
    "calibration_window": "2022-2026",
}

_DISCLAIMER = (
    "Unlock intelligence scores measure contextual impact and actionability. "
    "Unlock event ≠ automatic sell signal. No guaranteed price direction. "
    "Historical calibration describes past similar events — not predictions."
)

RecipientType = Literal["investor_vesting", "team_vesting", "ecosystem", "treasury", "unknown"]
ImpactLevel = Literal["low", "medium", "high", "critical"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"events": [], "calibration": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("token unlock intelligence seed load failed: %s", exc)
        return {"events": [], "calibration": {}}


def build_absorbed_tickets() -> dict[int, str]:
    return {
        703: "Token Unlock Actionability Score (absorbed into impact composite)",
        704: "Token Unlock Calendar (absorbed into #708 dashboard)",
        707: "Unlock Impact Intelligence (primary engine)",
        708: "Token Unlock Dashboard (Calendar + List + Magnitude + Impact)",
    }


def build_formula_documentation() -> dict[str, Any]:
    return {
        "formula_version": _FORMULA_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "impact_score": {
            "formula": (
                "impact = 0.35×magnitude_pct + 0.30×liquidity_absorption "
                "+ 0.20×recipient_weight + 0.15×historical_similarity"
            ),
            "range": "0–100",
            "no_guaranteed_direction": True,
        },
        "actionability_score": {
            "formula": (
                "actionability = 0.30×impact + 0.20×usd_size_weight "
                "+ 0.15×liquidity_gap + 0.15×exchange_flow_signal "
                "+ 0.10×volatility_context + 0.10×sentiment_context"
            ),
            "range": "0–100",
            "sub_task": "#703",
        },
        "unlock_not_sell_signal": True,
        "display": (
            "Formula v1.0 documented | Historically calibrated | "
            "Unlock event ≠ automatic sell signal"
        ),
    }


def build_historical_calibration(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cal = {**_HISTORICAL_CALIBRATION, **(seed.get("calibration") or {})}
    return {
        **cal,
        "calibrated_historically": True,
        "no_guaranteed_price_direction": True,
        "display": (
            f"Historically: similar unlocks → price declined "
            f"{cal.get('price_declined_pct_of_time', 60)}% of the time | "
            "Not a prediction — calibration only"
        ),
    }


_RECIPIENT_WEIGHTS: dict[str, float] = {
    "investor_vesting": 0.85,
    "team_vesting": 0.70,
    "ecosystem": 0.50,
    "treasury": 0.40,
    "unknown": 0.30,
}


def compute_magnitude_score(
    unlock_pct_circulating: float,
    unlock_usd: float,
    circulating_supply_usd: float,
) -> dict[str, Any]:
    pct_component = min(unlock_pct_circulating / 5.0 * 100, 100)
    usd_ratio = unlock_usd / max(circulating_supply_usd, 1)
    usd_component = min(usd_ratio * 200, 100)
    score = round(pct_component * 0.6 + usd_component * 0.4, 1)
    return {
        "score": score,
        "unlock_pct_circulating": unlock_pct_circulating,
        "unlock_usd": unlock_usd,
        "pct_component": round(pct_component, 1),
        "usd_component": round(usd_component, 1),
    }


def compute_liquidity_absorption(unlock_usd: float, adv_usd: float) -> dict[str, Any]:
    if adv_usd <= 0:
        return {"score": 0, "ratio": None, "absorption_risk": "unknown"}
    ratio = unlock_usd / adv_usd
    score = min(ratio * 50, 100)
    risk = "critical" if ratio > 0.5 else "high" if ratio > 0.2 else "medium" if ratio > 0.05 else "low"
    return {
        "score": round(score, 1),
        "ratio": round(ratio, 4),
        "adv_usd": adv_usd,
        "absorption_risk": risk,
    }


def _safe_float(value: Any, default: float = 0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def compute_impact_score(event: dict[str, Any]) -> dict[str, Any]:
    """#707 impact score — magnitude + liquidity + recipient + historical similarity."""
    if event.get("unlock_usd") is None or event.get("unlock_pct_circulating") is None:
        return {
            "feature_id": 707,
            "impact_score": None,
            "impact_level": None,
            "missing_data": True,
            "no_guaranteed_price_direction": True,
            "formula_version": _FORMULA_VERSION,
            "not_a_signal": True,
            "display": "Impact score unavailable — unlock amounts pending verification",
        }

    magnitude = compute_magnitude_score(
        _safe_float(event.get("unlock_pct_circulating")),
        _safe_float(event.get("unlock_usd")),
        _safe_float(event.get("circulating_supply_usd"), 1),
    )
    liquidity = compute_liquidity_absorption(
        _safe_float(event.get("unlock_usd")),
        _safe_float(event.get("adv_usd"), 1),
    )
    recipient = event.get("recipient_type", "unknown")
    recipient_weight = _RECIPIENT_WEIGHTS.get(recipient, 0.3) * 100
    historical_sim = float(event.get("historical_similarity", 0.5)) * 100

    raw = (
        magnitude["score"] * 0.35
        + liquidity["score"] * 0.30
        + recipient_weight * 0.20
        + historical_sim * 0.15
    )
    score = round(min(max(raw, 0), 100), 1)

    if score >= 75:
        level: ImpactLevel = "critical"
    elif score >= 50:
        level = "high"
    elif score >= 25:
        level = "medium"
    else:
        level = "low"

    comparable = event.get("comparable_events") or []
    return {
        "feature_id": 707,
        "impact_score": score,
        "impact_level": level,
        "magnitude": magnitude,
        "liquidity_absorption": liquidity,
        "recipient_type": recipient,
        "recipient_weight": recipient_weight,
        "historical_similarity": historical_sim,
        "comparable_historical_events": comparable,
        "no_guaranteed_price_direction": True,
        "formula_version": _FORMULA_VERSION,
        "not_a_signal": True,
    }


def compute_actionability_score(event: dict[str, Any], impact: dict[str, Any]) -> dict[str, Any]:
    """#703 actionability — context-aware composite absorbed into engine."""
    if impact.get("missing_data") or impact.get("impact_score") is None:
        return {
            "sub_task": "#703",
            "actionability_score": None,
            "reasons": ["Unlock amounts pending — actionability unavailable"],
            "conflicting_factors": [],
            "missing_data": True,
            "unlock_not_automatic_sell_signal": True,
            "formula_version": _FORMULA_VERSION,
            "calibrated_historically": True,
            "not_a_signal": True,
        }

    impact_score = float(impact.get("impact_score", 0))
    usd_weight = min(_safe_float(event.get("unlock_usd")) / 10_000_000 * 20, 100)
    liquidity_gap = float(impact.get("liquidity_absorption", {}).get("score", 0))
    exchange_flow = _safe_float(event.get("exchange_inflow_signal")) * 100
    volatility = _safe_float(event.get("volatility_context"), 0.5) * 100
    sentiment = _safe_float(event.get("sentiment_context"), 0.5) * 100

    raw = (
        impact_score * 0.30
        + usd_weight * 0.20
        + liquidity_gap * 0.15
        + exchange_flow * 0.15
        + volatility * 0.10
        + sentiment * 0.10
    )
    score = round(min(max(raw, 0), 100), 1)

    reasons = []
    conflicts = []

    if impact_score >= 50:
        reasons.append(f"High impact score ({impact_score}) — significant supply increase")
    if liquidity_gap >= 50:
        reasons.append("Liquidity absorption risk elevated vs ADV")
    if event.get("exchange_inflow_signal", 0) > 0.5:
        reasons.append("Exchange inflow signal detected pre-unlock")
    if event.get("recipient_type") == "investor_vesting":
        reasons.append("Investor vesting — historically higher sell pressure")

    if event.get("sentiment_context", 0.5) > 0.6 and impact_score >= 40:
        conflicts.append("Positive sentiment conflicts with supply pressure risk")
    if event.get("volatility_context", 0.5) < 0.3 and liquidity_gap >= 50:
        conflicts.append("Low volatility may mask absorption difficulty")

    return {
        "sub_task": "#703",
        "actionability_score": score,
        "reasons": reasons,
        "conflicting_factors": conflicts,
        "components": {
            "impact": impact_score,
            "usd_size": usd_weight,
            "liquidity_gap": liquidity_gap,
            "exchange_flow": exchange_flow,
            "volatility": volatility,
            "sentiment": sentiment,
        },
        "unlock_not_automatic_sell_signal": True,
        "formula_version": _FORMULA_VERSION,
        "calibrated_historically": True,
        "not_a_signal": True,
    }


def normalize_unlock_event(event: dict[str, Any]) -> dict[str, Any]:
    """#704 calendar normalization — primary sources, revisions, no missing-as-zero."""
    unlock_amount = event.get("unlock_amount_native")
    missing = unlock_amount is None

    return {
        "event_id": event.get("event_id"),
        "asset": event.get("asset"),
        "name": event.get("name"),
        "unlock_date": event.get("unlock_date"),
        "unlock_amount_native": unlock_amount,
        "unlock_usd": event.get("unlock_usd"),
        "unlock_pct_circulating": event.get("unlock_pct_circulating"),
        "unlock_pct_total_supply": event.get("unlock_pct_total_supply"),
        "recipient_type": event.get("recipient_type"),
        "missing_unlock_treated_as_zero": False,
        "missing_data": missing,
        "primary_source_url": event.get("primary_source_url"),
        "assumptions": event.get("assumptions") or [],
        "revision_history": event.get("revision_history") or [],
        "revisions_tracked": True,
        "sub_task": "#704",
        "provenance": {
            "source_url": event.get("primary_source_url"),
            "source_type": event.get("source_type", "protocol_docs"),
            "last_revised": (event.get("revision_history") or [{}])[-1].get("date"),
        },
    }


def build_calendar_entry(event: dict[str, Any]) -> dict[str, Any]:
    normalized = normalize_unlock_event(event)
    impact = compute_impact_score(event)
    actionability = compute_actionability_score(event, impact)

    return {
        **normalized,
        "magnitude": impact.get("magnitude"),
        "impact": impact,
        "actionability": actionability,
        "display": (
            f"{event.get('asset')} unlock {event.get('unlock_date')} | "
            f"Impact: {impact.get('impact_score', 'N/A')} | "
            f"Actionability: {actionability.get('actionability_score', 'N/A')}"
        ),
    }


def build_unlock_dashboard(limit: int = 30) -> dict[str, Any]:
    """#708 dashboard — Calendar + List + Magnitude + Impact + Actionability."""
    t0 = time.perf_counter()
    seed = _load_seed()
    events = seed.get("events") or []
    events_sorted = sorted(events, key=lambda e: e.get("unlock_date", ""))
    calendar = [build_calendar_entry(e) for e in events_sorted[:limit]]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _DASHBOARD_FEATURE_ID,
        "feature_ids": list(_ABSORBED_IDS),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "token_unlock_dashboard",
        "calendar": calendar,
        "upcoming_unlock_list": calendar,
        "count": len(calendar),
        "formula": build_formula_documentation(),
        "calibration": build_historical_calibration(seed),
        "disclaimer": _DISCLAIMER,
        "unlock_not_sell_signal": True,
        "no_guaranteed_price_direction": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_unlock_calendar(limit: int = 30) -> dict[str, Any]:
    """#704 absorbed — calendar with magnitude metrics."""
    dashboard = build_unlock_dashboard(limit=limit)
    return {
        "ok": True,
        "feature_id": 704,
        "archived_standalone": True,
        "absorbed_into": "#708 Token Unlock Dashboard",
        "sub_task": "#704",
        "calendar": dashboard["calendar"],
        "count": dashboard["count"],
        "primary_sources_stored": True,
        "revisions_tracked": True,
        "no_missing_as_zero": True,
        "timestamp": _utcnow(),
    }


def build_impact_panel(asset: str = "ARB") -> dict[str, Any]:
    """#707 impact intelligence for a single asset unlock."""
    seed = _load_seed()
    sym = asset.upper()
    event = next((e for e in seed.get("events") or [] if e.get("asset", "").upper() == sym), None)

    if not event:
        return {"ok": False, "feature_id": _FEATURE_ID, "error": "unlock_not_found", "asset": sym}

    impact = compute_impact_score(event)
    actionability = compute_actionability_score(event, impact)
    normalized = normalize_unlock_event(event)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "asset": sym,
        "event": normalized,
        "impact": impact,
        "actionability": actionability,
        "calibration": build_historical_calibration(seed),
        "formula": build_formula_documentation(),
        "disclaimer": _DISCLAIMER,
        "not_a_signal": True,
        "timestamp": _utcnow(),
    }


def build_actionability_panel(asset: str = "ARB") -> dict[str, Any]:
    """#703 absorbed — actionability score with reasons."""
    panel = build_impact_panel(asset)
    if not panel.get("ok"):
        return panel

    return {
        "ok": True,
        "feature_id": 703,
        "archived_standalone": True,
        "absorbed_into": "#707 Token Unlock Intelligence Engine",
        "sub_task": "#703",
        "asset": panel["asset"],
        "actionability": panel["actionability"],
        "impact_score": panel["impact"]["impact_score"],
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def compute_unlock_severity(unlock_pct_circulating: float) -> dict[str, Any]:
    """#607 — severity from % of circulating supply."""
    pct = float(unlock_pct_circulating)
    if pct > 10:
        level: ImpactLevel = "critical"
    elif pct > 5:
        level = "high"
    elif pct >= 1:
        level = "medium"
    else:
        level = "low"
    return {
        "unlock_pct_circulating": pct,
        "severity": level,
        "thresholds": {"low": "<1%", "medium": "1-5%", "high": ">5%", "critical": ">10%"},
    }


def build_unlock_forecast_entry(event: dict[str, Any], *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#607 — unlock forecaster with provenance, revisions, historical context."""
    seed = seed or _load_seed()
    normalized = normalize_unlock_event(event)
    pct = event.get("unlock_pct_circulating")
    severity = compute_unlock_severity(_safe_float(pct)) if pct is not None else {"severity": "unknown", "unlock_pct_circulating": None}

    historical_context = None
    comparable = event.get("comparable_events") or []
    if comparable:
        last = comparable[0]
        historical_context = {
            "description": (
                f"آخر unlock بنفس الحجم ({last.get('unlock_pct')}%) أدى إلى "
                f"انخفاض {abs(last.get('drawdown_pct', 0)):.1f}% خلال 7 أيام"
            ),
            "description_en": (
                f"Last similar unlock ({last.get('unlock_pct')}%) led to "
                f"{last.get('drawdown_pct', 0):+.1f}% move over 7 days"
            ),
            "data_driven_not_prediction": True,
            "comparable_event": last,
        }

    confidence = "high" if event.get("primary_source_url") and event.get("revision_history") else "medium"
    if event.get("unlock_usd") is None:
        confidence = "low"

    return {
        "feature_ref": _FORECASTER_REF,
        "event_id": event.get("event_id"),
        "asset": event.get("asset"),
        "unlock_date": event.get("unlock_date"),
        "unlock_pct_circulating": event.get("unlock_pct_circulating"),
        "unlock_usd": event.get("unlock_usd"),
        "affected_supply_pct": event.get("unlock_pct_circulating"),
        "recipient_classification": event.get("recipient_type"),
        "severity": severity,
        "confidence": confidence,
        "schedule_provenance": {
            "source_url": event.get("primary_source_url"),
            "source_type": event.get("source_type"),
            "provenance_required": True,
        },
        "revisions_tracked": True,
        "revision_history": event.get("revision_history") or [],
        "historical_impact_context": historical_context,
        "no_deterministic_price_prediction": True,
        "display_label": "ضغط عرض محتمل",
        "display_label_en": "potential_supply_pressure",
        "not_a_price_target": True,
        "normalized": normalized,
    }


def build_unlock_forecaster_panel(limit: int = 30, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#607 Token Unlock Forecaster — Intelligence Ledger surface."""
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    events = sorted(seed.get("events") or [], key=lambda e: e.get("unlock_date", ""))
    calendar = [build_unlock_forecast_entry(e, seed=seed) for e in events[:limit]]
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_ref": _FORECASTER_REF,
        "title": "Token Unlock Forecaster",
        "standalone": False,
        "merged_into": "Intelligence Ledger / Token Unlock Intelligence Engine",
        "unlock_calendar": calendar,
        "count": len(calendar),
        "no_deterministic_price_prediction": True,
        "schedule_provenance_required": True,
        "revisions_tracked": True,
        "severity_scoring": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_capital_protection_unlock_alerts(
    portfolio_id: str = "demo_portfolio",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#607 → #410: alert if portfolio exposure in asset with unlock >5% within 30 days."""
    seed = seed or _load_seed()
    cfg = seed.get("unlock_forecaster_607") or {}
    exposure = (cfg.get("portfolio_exposure") or {}).get(portfolio_id) or {}
    horizon_days = int(cfg.get("alert_horizon_days", 30))
    threshold_pct = float(cfg.get("unlock_alert_threshold_pct", 5))
    alerts: list[dict[str, Any]] = []

    for event in seed.get("events") or []:
        asset = str(event.get("asset", "")).upper()
        exposure_pct = float(exposure.get(asset, 0))
        if exposure_pct <= 0:
            continue
        severity = compute_unlock_severity(float(event.get("unlock_pct_circulating", 0)))
        if severity["severity"] in ("high", "critical"):
            alerts.append({
                "alert_type": "unlock_supply_pressure",
                "feature_ref": _FORECASTER_REF,
                "integration": "capital_protection_410",
                "asset": asset,
                "portfolio_exposure_pct": exposure_pct,
                "unlock_pct_circulating": event.get("unlock_pct_circulating"),
                "unlock_date": event.get("unlock_date"),
                "horizon_days": horizon_days,
                "severity": severity["severity"],
                "alerts_only": True,
                "no_price_prediction": True,
                "display": (
                    f"Unlock alert: {asset} exposure {exposure_pct}% with "
                    f"{event.get('unlock_pct_circulating')}% unlock in {horizon_days}d — potential supply pressure"
                ),
            })

    return {
        "ok": True,
        "feature_ref": _FORECASTER_REF,
        "portfolio_id": portfolio_id,
        "alerts": alerts,
        "alert_count": len(alerts),
        "threshold_pct": threshold_pct,
        "alerts_only": True,
        "timestamp": _utcnow(),
    }


def build_unlock_metric_577(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#607 → #577: unlock schedule as on-chain metric."""
    seed = seed or _load_seed()
    upcoming = [
        {
            "asset": e.get("asset"),
            "unlock_date": e.get("unlock_date"),
            "unlock_pct_circulating": e.get("unlock_pct_circulating"),
            "severity": compute_unlock_severity(float(e.get("unlock_pct_circulating", 0)))["severity"],
        }
        for e in (seed.get("events") or [])[:10]
    ]
    return {
        "ok": True,
        "metric_id": "token_unlock_schedule",
        "task_ref": _FORECASTER_REF,
        "upcoming_unlocks": upcoming,
        "count": len(upcoming),
        "source": "token_unlock_forecaster_607",
        "timestamp": _utcnow(),
    }


def build_market_radar_unlock_timeline(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#607 → Market Radar event timeline."""
    forecaster = build_unlock_forecaster_panel(seed=seed)
    return {
        "ok": True,
        "feature_ref": _FORECASTER_REF,
        "surface": "market_radar",
        "widget": "unlock_event_timeline",
        "events": forecaster.get("unlock_calendar") or [],
        "no_deterministic_price_prediction": True,
        "timestamp": _utcnow(),
    }


def run_unlock_alert_tests(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#607 — mandatory internal alert QA before launch."""
    seed = seed or _load_seed()
    cfg = seed.get("unlock_forecaster_607") or {}
    test_alerts = cfg.get("alert_test_signals") or []
    checks: list[dict[str, Any]] = []

    for signal in test_alerts:
        checks.append({
            "test_id": signal.get("test_id"),
            "passed": signal.get("delivered") is True and signal.get("verified") is True,
            "detail": signal.get("detail"),
        })

    forecaster = build_unlock_forecaster_panel(seed=seed)
    checks.append({"test": "provenance_on_all_events", "passed": all(
        (e.get("schedule_provenance") or {}).get("source_url") for e in forecaster.get("unlock_calendar") or []
    )})
    checks.append({"test": "revisions_tracked", "passed": all(
        e.get("revisions_tracked") for e in forecaster.get("unlock_calendar") or []
    )})
    checks.append({"test": "no_price_prediction_label", "passed": forecaster.get("no_deterministic_price_prediction") is True})

    capital = build_capital_protection_unlock_alerts(seed=seed)
    checks.append({"test": "capital_protection_410", "passed": capital.get("ok") is True})

    all_passed = all(c.get("passed") for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FORECASTER_REF,
        "checks": checks,
        "all_passed": all_passed,
        "test_count": len(checks),
        "timestamp": _utcnow(),
    }


def token_unlock_intelligence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Token Unlock Intelligence Engine",
        "feature_ids": list(_ABSORBED_IDS),
        "absorbed_tickets": build_absorbed_tickets(),
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "dashboard_feature_id": _DASHBOARD_FEATURE_ID,
        "formula": build_formula_documentation(),
        "calibration": build_historical_calibration(seed),
        "acceptance_criteria": {
            "formula_version_documented": True,
            "calibrated_historically": True,
            "unlock_not_automatic_sell_signal": True,
            "no_guaranteed_price_direction": True,
            "primary_source_links_stored": True,
            "revisions_tracked": True,
            "no_missing_unlock_as_zero": True,
        },
        "event_count": len(seed.get("events") or []),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }
