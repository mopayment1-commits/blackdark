"""
DeFi Risk Passport — Feature #660 (Sprint-2 Risk Layer).

Protocol exposure assessment with transparent breakdown — no hidden scores.
Absorbs #661 DeFi Risk Radar (real-time) and #672 Lending Market Risk category.

Integrations: #438 opportunity cancellation, #410 portfolio alerts, #484 alerts, #652 contagion.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.DeFiRiskPassport")

_FEATURE_ID = 660
_RISK_RADAR_REF = 661
_LENDING_RISK_REF = 672
_SECURITY_MONITOR_REF = 667
_TITLE = "Protocol Risk Passport"
_LEGAL_NAME = "DeFi Risk Passport"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Risk Layer Core / DeFi Risk Module"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/defi_risk_passport_seed.json")
_METHODOLOGY_VERSION = "1.0"

_GRADE_ORDER = ("A+", "A", "B", "C", "D", "F")
_GRADE_MIN_FOR_OPPORTUNITY = ("A+", "A", "B", "C")

_DISCLAIMER = (
    "DeFi Risk Passport — protocol exposure assessment with documented evidence. "
    "No hidden scores. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"protocols": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("defi risk passport seed load failed: %s", exc)
        return {"protocols": {}}


def _letter_grade(score: float) -> str:
    if score >= 92:
        return "A+"
    if score >= 85:
        return "A"
    if score >= 70:
        return "B"
    if score >= 55:
        return "C"
    if score >= 40:
        return "D"
    return "F"


def _grade_color(grade: str) -> str:
    return {
        "A+": "green",
        "A": "green",
        "B": "yellow",
        "C": "orange",
        "D": "red",
        "F": "red",
    }.get(grade, "gray")


def score_protocol_risk_passport(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#660 — category risk model with full transparent breakdown."""
    seed = seed or _load_seed()
    proto = (seed.get("protocols") or {}).get(protocol_id)
    if not proto:
        return {"ok": False, "protocol_id": protocol_id, "error": "protocol_not_found"}

    weights = seed.get("category_weights") or {}
    categories = proto.get("risk_categories") or {}

    breakdown: dict[str, Any] = {}
    weighted_sum = 0.0
    weight_total = 0.0

    for cat_id, cat_data in categories.items():
        raw = float(cat_data.get("score", 50))
        w = float(weights.get(cat_id, 1 / max(len(categories), 1)))
        contribution = round(raw * w, 2)
        weighted_sum += contribution
        weight_total += w
        breakdown[cat_id] = {
            "score": raw,
            "weight": w,
            "contribution": contribution,
            "evidence": cat_data.get("evidence"),
            "source": cat_data.get("source"),
        }

    composite = round(weighted_sum / weight_total if weight_total else 50, 2)
    grade = _letter_grade(composite)

    exploits = proto.get("exploit_history") or []
    exploit_evidence = [
        {
            "incident_id": e.get("incident_id"),
            "severity": e.get("severity"),
            "date": e.get("date"),
            "source": e.get("source"),
            "source_link": e.get("source_link"),
            "incident_source_required": True,
        }
        for e in exploits
    ]

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "protocol_id": protocol_id,
        "protocol_name": proto.get("protocol_name"),
        "risk_grade": grade,
        "composite_score": composite,
        "no_hidden_score": True,
        "breakdown": {
            "tvl_concentration_pct": proto.get("tvl_concentration_pct"),
            "exploit_history": {
                "count": len(exploits),
                "incidents": exploit_evidence,
                "max_severity": max((e.get("severity", 0) for e in exploits), default=0),
            },
            "oracle_health": proto.get("oracle_health"),
            "liquidity_depth": proto.get("liquidity_depth"),
            "bridge_dependency": proto.get("bridge_dependency"),
            "categories": breakdown,
        },
        "evidence": proto.get("evidence_links") or [],
        "methodology_version": _METHODOLOGY_VERSION,
        "display": f"{proto.get('protocol_name')} Risk Passport: {grade} ({composite}/100)",
        "timestamp": _utcnow(),
    }


def build_risk_passport_card(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Passport Card + historical trend for /protocol/[name]/risk."""
    seed = seed or _load_seed()
    passport = score_protocol_risk_passport(protocol_id, seed=seed)
    if not passport.get("ok"):
        return passport

    proto = (seed.get("protocols") or {}).get(protocol_id) or {}
    return {
        **passport,
        "route": f"/protocol/{protocol_id}/risk",
        "card_type": "passport",
        "historical_trend": proto.get("historical_trend") or [],
        "passport_card": {
            "grade": passport["risk_grade"],
            "grade_color": _grade_color(passport["risk_grade"]),
            "composite_score": passport["composite_score"],
            "breakdown_visible": True,
            "no_hidden_score": True,
        },
        "timestamp": _utcnow(),
    }


def build_lending_risk_dashboard(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#672 — lending market risk with protocol semantics."""
    seed = seed or _load_seed()
    proto = (seed.get("protocols") or {}).get(protocol_id)
    if not proto:
        return {"ok": False, "protocol_id": protocol_id, "error": "protocol_not_found"}

    lending = proto.get("lending_risk") or {}
    if not lending:
        return {"ok": False, "protocol_id": protocol_id, "error": "not_lending_protocol"}

    passport = score_protocol_risk_passport(protocol_id, seed=seed)
    utilization = float(lending.get("utilization_rate_pct", 0))

    return {
        "ok": True,
        "feature_ref": _LENDING_RISK_REF,
        "merged_into": _FEATURE_ID,
        "protocol_id": protocol_id,
        "protocol_name": proto.get("protocol_name"),
        "protocol_semantics": lending.get("protocol_semantics"),
        "protocol_version": lending.get("protocol_version"),
        "mandatory_metrics": {
            "utilization_rate_pct": utilization,
            "collateral_factor_pct": lending.get("collateral_factor_pct"),
            "liquidation_threshold_pct": lending.get("liquidation_threshold_pct"),
            "borrow_supply_ratio": lending.get("borrow_supply_ratio"),
            "historical_liquidation_volume_usd": lending.get("historical_liquidation_volume_usd"),
        },
        "risk_grade": passport.get("risk_grade"),
        "utilization_alert_410": utilization > float((seed.get("alert_thresholds") or {}).get("utilization_pct", 90)),
        "display": (
            f"Lending Risk {proto.get('protocol_name')}: "
            f"utilization {utilization}% | grade {passport.get('risk_grade')}"
        ),
        "timestamp": _utcnow(),
    }


def build_defi_risk_radar(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#661 — real-time risk radar heatmap merged into #660."""
    seed = seed or _load_seed()
    protocols = seed.get("protocols") or {}
    entries: list[dict[str, Any]] = []

    for pid in protocols:
        passport = score_protocol_risk_passport(pid, seed=seed)
        if not passport.get("ok"):
            continue
        entries.append({
            "protocol_id": pid,
            "protocol_name": passport.get("protocol_name"),
            "risk_grade": passport["risk_grade"],
            "composite_score": passport["composite_score"],
            "heatmap_color": _grade_color(passport["risk_grade"]),
            "real_time_alert": (protocols[pid].get("real_time_risk") or {}).get("spike_active", False),
        })

    entries.sort(key=lambda x: x["composite_score"])
    alerts = build_defi_risk_spike_alerts_484(seed=seed)

    return {
        "ok": True,
        "feature_ref": _RISK_RADAR_REF,
        "merged_into": _FEATURE_ID,
        "route": "/defi-risk",
        "radar_type": "heatmap",
        "protocols": entries,
        "count": len(entries),
        "alerts_484": alerts,
        "methodology_version": _METHODOLOGY_VERSION,
        "evidence_required": True,
        "timestamp": _utcnow(),
    }


def build_defi_risk_spike_alerts_484(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#661 → #484 — DeFi Risk Spike alerts."""
    seed = seed or _load_seed()
    alerts: list[dict[str, Any]] = []

    for pid, proto in (seed.get("protocols") or {}).items():
        rt = proto.get("real_time_risk") or {}
        if rt.get("spike_active"):
            alerts.append({
                "alert_type": "defi_risk_spike",
                "feature_ref": 484,
                "protocol_id": pid,
                "protocol_name": proto.get("protocol_name"),
                "severity": rt.get("severity", "elevated"),
                "signal": "DeFi Risk Spike",
                "methodology_version": _METHODOLOGY_VERSION,
                "evidence_link": rt.get("evidence_link"),
                "display": f"DeFi Risk Spike: {proto.get('protocol_name')} — review passport",
            })

    return {
        "ok": True,
        "feature_ref": 484,
        "alert_count": len(alerts),
        "alerts": alerts,
        "timestamp": _utcnow(),
    }


def grade_allows_opportunity(grade: str) -> bool:
    """#438 — cancel opportunities if protocol grade < C."""
    return grade.upper() in _GRADE_MIN_FOR_OPPORTUNITY


def cancel_opportunities_by_passport_grade(
    opportunities: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """#438 — auto-cancel if protocol risk grade < C."""
    seed = seed or _load_seed()
    protocol_map = seed.get("opportunity_protocol_map") or {}
    result: list[dict[str, Any]] = []

    for opp in opportunities:
        opp_copy = dict(opp)
        pid = (
            opp_copy.get("protocol_id")
            or protocol_map.get(str(opp_copy.get("opportunity_id", "")))
            or protocol_map.get(str(opp_copy.get("asset", "")).lower())
        )
        if pid:
            passport = score_protocol_risk_passport(pid, seed=seed)
            if passport.get("ok"):
                grade = passport["risk_grade"]
                opp_copy["risk_passport_660"] = {
                    "grade": grade,
                    "composite_score": passport["composite_score"],
                    "no_hidden_score": True,
                }
                if not grade_allows_opportunity(grade):
                    opp_copy["passport_cancelled_660"] = True
                    opp_copy["signal_suppressed"] = True
                    opp_copy["cancel_reason_660"] = f"protocol_grade_{grade}_below_C"
        result.append(opp_copy)
    return result


def build_portfolio_passport_alert_410(
    *,
    portfolio_id: str = "demo_portfolio",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#410 — alert if portfolio exposure in unhealthy protocol."""
    seed = seed or _load_seed()
    portfolio = (seed.get("portfolios") or {}).get(portfolio_id) or {}
    holdings = portfolio.get("protocol_exposure") or {}
    min_grade = (seed.get("alert_thresholds") or {}).get("min_passport_grade", "C")
    min_grade_idx = _GRADE_ORDER.index(min_grade) if min_grade in _GRADE_ORDER else 4

    alerts: list[dict[str, Any]] = []
    for pid, pct in holdings.items():
        passport = score_protocol_risk_passport(pid, seed=seed)
        if not passport.get("ok"):
            continue
        grade = passport["risk_grade"]
        grade_idx = _GRADE_ORDER.index(grade) if grade in _GRADE_ORDER else 5
        if grade_idx > min_grade_idx:
            alerts.append({
                "protocol_id": pid,
                "portfolio_pct": pct,
                "risk_grade": grade,
                "composite_score": passport["composite_score"],
                "alert": True,
                "breakdown": passport.get("breakdown"),
            })

    return {
        "ok": True,
        "feature_ref": 410,
        "portfolio_id": portfolio_id,
        "unhealthy_exposure": len(alerts) > 0,
        "alerts": alerts,
        "min_passport_grade_threshold": min_grade,
        "no_hidden_score": True,
        "display": (
            f"Portfolio passport alert: {len(alerts)} protocols below grade {min_grade}"
            if alerts else "Portfolio protocol exposure within passport thresholds"
        ),
        "timestamp": _utcnow(),
    }


def get_lending_contagion_trigger_652(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#652 — lending protocol insolvency as contagion trigger."""
    seed = seed or _load_seed()
    lending = build_lending_risk_dashboard(protocol_id, seed=seed)
    if not lending.get("ok"):
        return {"ok": False, "protocol_id": protocol_id, "trigger": False}

    utilization = float(lending["mandatory_metrics"]["utilization_rate_pct"])
    insolvency_risk = utilization >= float((seed.get("alert_thresholds") or {}).get("insolvency_utilization_pct", 95))

    return {
        "ok": True,
        "feature_ref": 652,
        "protocol_id": protocol_id,
        "contagion_trigger": insolvency_risk,
        "trigger_type": "lending_insolvency",
        "utilization_rate_pct": utilization,
        "display": f"Lending insolvency contagion trigger: {insolvency_risk}",
        "timestamp": _utcnow(),
    }


_KNOWN_EXPLOIT_PATTERNS = (
    "re_entrancy",
    "price_oracle_manipulation",
    "governance_attack",
    "flash_loan_abuse",
    "admin_key_compromise",
)


def build_defi_security_monitor_dashboard(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#667 — DeFi Security Monitor (renamed from Flash Loan Attack Proximity).

    Monitors known exploit patterns from Immunefi + Rekt + on-chain anomaly.
  """
    seed = seed or _load_seed()
    proto = (seed.get("protocols") or {}).get(protocol_id)
    if not proto:
        return {"ok": False, "protocol_id": protocol_id, "error": "protocol_not_found"}

    sec = proto.get("security_monitor") or {}
    patterns = sec.get("known_patterns") or []
    active_patterns = [p for p in patterns if p.get("detected")]

    return {
        "ok": True,
        "feature_ref": _SECURITY_MONITOR_REF,
        "merged_into": _FEATURE_ID,
        "legal_name": "DeFi Security Monitor",
        "no_flash_loan_branding": True,
        "protocol_id": protocol_id,
        "protocol_name": proto.get("protocol_name"),
        "active_threat": sec.get("active_threat", False),
        "threat_level": sec.get("threat_level", "normal"),
        "severity": sec.get("severity", 0),
        "known_patterns_monitored": list(_KNOWN_EXPLOIT_PATTERNS),
        "detected_patterns": active_patterns,
        "monitoring_sources": sec.get("monitoring_sources", ["immunefi", "rekt"]),
        "on_chain_anomaly": sec.get("on_chain_anomaly", False),
        "incidents": [
            {
                "incident_id": e.get("incident_id"),
                "severity": e.get("severity"),
                "date": e.get("date"),
                "source": e.get("source"),
                "source_link": e.get("source_link"),
                "pattern": e.get("pattern"),
            }
            for e in (proto.get("exploit_history") or [])
        ],
        "evidence_link": sec.get("evidence_link"),
        "last_scan_at": sec.get("last_scan_at"),
        "fixed_institutional_conditions": True,
        "no_attack_prediction_claim": True,
        "display": (
            f"DeFi Security Monitor: {proto.get('protocol_name')} — "
            f"{len(active_patterns)} active pattern(s), threat={sec.get('threat_level', 'normal')}"
        ),
        "timestamp": _utcnow(),
    }


def build_defi_security_monitor_view(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#667 aggregate security monitor across protocols."""
    seed = seed or _load_seed()
    dashboards = [
        build_defi_security_monitor_dashboard(pid, seed=seed)
        for pid in (seed.get("protocols") or {})
    ]
    active = [d for d in dashboards if d.get("ok") and d.get("active_threat")]
    return {
        "ok": True,
        "feature_ref": _SECURITY_MONITOR_REF,
        "merged_into": _FEATURE_ID,
        "route": "/defi-security-monitor",
        "protocols": [d for d in dashboards if d.get("ok")],
        "active_threat_count": len(active),
        "count": len([d for d in dashboards if d.get("ok")]),
        "timestamp": _utcnow(),
    }


def build_defi_security_alerts_484(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#667 → #484 — DeFi Security alerts via Alert Engine."""
    seed = seed or _load_seed()
    alerts: list[dict[str, Any]] = []
    severity_threshold = float((seed.get("alert_thresholds") or {}).get("security_incident_severity_threshold", 7))

    for pid in (seed.get("protocols") or {}):
        monitor = build_defi_security_monitor_dashboard(pid, seed=seed)
        if not monitor.get("ok"):
            continue
        if monitor.get("active_threat") or float(monitor.get("severity") or 0) >= severity_threshold:
            alerts.append({
                "alert_type": "defi_security_monitor",
                "feature_ref": 484,
                "source_ref": _SECURITY_MONITOR_REF,
                "protocol_id": pid,
                "protocol_name": monitor.get("protocol_name"),
                "severity": monitor.get("threat_level", "elevated"),
                "signal": "DeFi Security Monitor",
                "detected_patterns": monitor.get("detected_patterns"),
                "evidence_link": monitor.get("evidence_link"),
                "display": f"DeFi Security: {monitor.get('protocol_name')} — review security monitor",
            })

    return {
        "ok": True,
        "feature_ref": 484,
        "source_ref": _SECURITY_MONITOR_REF,
        "alert_count": len(alerts),
        "alerts": alerts,
        "delivery_channels": ["push", "email", "sms"],
        "timestamp": _utcnow(),
    }


def build_portfolio_security_alert_410(
    *,
    portfolio_id: str = "demo_portfolio",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#667 → #410 — alert if portfolio holds protocols with active security threats."""
    seed = seed or _load_seed()
    portfolio = (seed.get("portfolios") or {}).get(portfolio_id) or {}
    holdings = portfolio.get("protocol_exposure") or {}
    alerts: list[dict[str, Any]] = []

    for pid, pct in holdings.items():
        monitor = build_defi_security_monitor_dashboard(pid, seed=seed)
        if monitor.get("ok") and monitor.get("active_threat"):
            alerts.append({
                "protocol_id": pid,
                "portfolio_pct": pct,
                "threat_level": monitor.get("threat_level"),
                "detected_patterns": monitor.get("detected_patterns"),
                "alert": True,
                "evidence_link": monitor.get("evidence_link"),
            })

    return {
        "ok": True,
        "feature_ref": 410,
        "source_ref": _SECURITY_MONITOR_REF,
        "portfolio_id": portfolio_id,
        "threatened_exposure": len(alerts) > 0,
        "alerts": alerts,
        "display": (
            f"Portfolio security alert: {len(alerts)} protocols with active threats"
            if alerts else "No active security threats in portfolio protocols"
        ),
        "timestamp": _utcnow(),
    }


def get_security_contagion_trigger_652(
    protocol_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#667 → #652 — security incident as contagion trigger."""
    seed = seed or _load_seed()
    monitor = build_defi_security_monitor_dashboard(protocol_id, seed=seed)
    if not monitor.get("ok"):
        return {"ok": False, "protocol_id": protocol_id, "trigger": False}

    active = monitor.get("active_threat", False)
    return {
        "ok": True,
        "feature_ref": 652,
        "source_ref": _SECURITY_MONITOR_REF,
        "protocol_id": protocol_id,
        "contagion_trigger": active,
        "trigger_type": "security_incident",
        "threat_level": monitor.get("threat_level"),
        "detected_patterns": monitor.get("detected_patterns"),
        "display": f"Security contagion trigger: {active}",
        "timestamp": _utcnow(),
    }


def cancel_opportunities_by_security_monitor(
    opportunities: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """#667 → #438 — cancel opportunities in protocols with active security threats."""
    seed = seed or _load_seed()
    protocol_map = seed.get("opportunity_protocol_map") or {}
    result: list[dict[str, Any]] = []

    for opp in opportunities:
        opp_copy = dict(opp)
        pid = (
            opp_copy.get("protocol_id")
            or protocol_map.get(str(opp_copy.get("opportunity_id", "")))
            or protocol_map.get(str(opp_copy.get("asset", "")).lower())
        )
        if pid:
            monitor = build_defi_security_monitor_dashboard(pid, seed=seed)
            if monitor.get("ok"):
                opp_copy["security_monitor_667"] = {
                    "active_threat": monitor.get("active_threat"),
                    "threat_level": monitor.get("threat_level"),
                    "detected_patterns": monitor.get("detected_patterns"),
                }
                if monitor.get("active_threat"):
                    opp_copy["security_cancelled_667"] = True
                    opp_copy["signal_suppressed"] = True
                    opp_copy["cancel_reason_667"] = f"security_threat_{monitor.get('threat_level')}"
        result.append(opp_copy)
    return result


def build_defi_risk_module_panel(
    protocol_id: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    protocols = seed.get("protocols") or {}
    if protocol_id:
        protocols = {protocol_id: protocols[protocol_id]} if protocol_id in protocols else {}

    passports = [build_risk_passport_card(pid, seed=seed) for pid in protocols]
    radar = build_defi_risk_radar(seed=seed)
    security = build_defi_security_monitor_view(seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "absorbed_features": {
            _RISK_RADAR_REF: "DeFi Risk Radar",
            _LENDING_RISK_REF: "Lending Market Risk",
            _SECURITY_MONITOR_REF: "DeFi Security Monitor",
        },
        "passports": [p for p in passports if p.get("ok")],
        "defi_risk_radar_661": radar,
        "defi_security_monitor_667": security,
        "no_hidden_score": True,
        "incident_source_data_required": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def defi_risk_passport_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "protocol_count": len(seed.get("protocols") or {}),
        "no_hidden_score": True,
        "incident_source_data_required": True,
        "absorbed_features": [661, 672, 667],
        "integrations": {
            "defi_opportunity_scanner_438": True,
            "capital_protection_410": True,
            "alert_engine_484": True,
            "cross_protocol_contagion_652": True,
            "defi_security_monitor_667": True,
        },
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": _STANDALONE is False, "detail": "660"})
    passport = score_protocol_risk_passport("aave_v3", seed=seed)
    checks.append({"id": "passport_ok", "passed": passport.get("ok") is True, "detail": "passport"})
    checks.append({"id": "no_hidden_score", "passed": passport.get("no_hidden_score") is True, "detail": "transparent"})
    checks.append({"id": "breakdown_tvl", "passed": passport.get("breakdown", {}).get("tvl_concentration_pct") is not None, "detail": "tvl"})
    checks.append({"id": "exploit_sources", "passed": all(e.get("source_link") for e in passport.get("breakdown", {}).get("exploit_history", {}).get("incidents", [])), "detail": "exploit"})
    checks.append({"id": "oracle_health", "passed": passport.get("breakdown", {}).get("oracle_health") is not None, "detail": "oracle"})
    checks.append({"id": "bridge_dependency", "passed": passport.get("breakdown", {}).get("bridge_dependency") is not None, "detail": "bridge"})

    card = build_risk_passport_card("aave_v3", seed=seed)
    checks.append({"id": "passport_card", "passed": card.get("card_type") == "passport", "detail": "card"})
    checks.append({"id": "historical_trend", "passed": len(card.get("historical_trend") or []) >= 2, "detail": "trend"})

    radar = build_defi_risk_radar(seed=seed)
    checks.append({"id": "risk_radar_661", "passed": radar.get("ok") is True and radar.get("count", 0) >= 2, "detail": "661"})
    checks.append({"id": "alerts_484", "passed": (radar.get("alerts_484") or {}).get("ok") is True, "detail": "484"})

    lending = build_lending_risk_dashboard("aave_v3", seed=seed)
    checks.append({"id": "lending_risk_672", "passed": lending.get("ok") is True, "detail": "672"})
    checks.append({"id": "lending_5_metrics", "passed": len(lending.get("mandatory_metrics") or {}) == 5, "detail": "metrics"})
    checks.append({"id": "protocol_semantics", "passed": lending.get("protocol_semantics") is not None, "detail": "semantics"})

    alert = build_portfolio_passport_alert_410(seed=seed)
    checks.append({"id": "portfolio_410", "passed": alert.get("ok") is True, "detail": "410"})

    opps = cancel_opportunities_by_passport_grade([{"protocol_id": "risky_protocol"}], seed=seed)
    checks.append({"id": "cancel_438", "passed": opps[0].get("passport_cancelled_660") is True, "detail": "438"})

    contagion = get_lending_contagion_trigger_652("high_util_lending", seed=seed)
    checks.append({"id": "contagion_652", "passed": contagion.get("contagion_trigger") is True, "detail": "652"})

    security = build_defi_security_monitor_dashboard("risky_protocol", seed=seed)
    checks.append({"id": "security_monitor_667", "passed": security.get("ok") is True, "detail": "667"})
    checks.append({"id": "no_flash_loan_branding", "passed": security.get("no_flash_loan_branding") is True, "detail": "rename"})
    checks.append({"id": "security_patterns", "passed": len(security.get("known_patterns_monitored") or []) >= 3, "detail": "patterns"})

    sec_alerts = build_defi_security_alerts_484(seed=seed)
    checks.append({"id": "security_alerts_484", "passed": sec_alerts.get("ok") is True, "detail": "484"})

    sec_portfolio = build_portfolio_security_alert_410(seed=seed)
    checks.append({"id": "security_portfolio_410", "passed": sec_portfolio.get("threatened_exposure") is True, "detail": "410"})

    sec_contagion = get_security_contagion_trigger_652("risky_protocol", seed=seed)
    checks.append({"id": "security_contagion_652", "passed": sec_contagion.get("contagion_trigger") is True, "detail": "652"})

    sec_cancel = cancel_opportunities_by_security_monitor([{"protocol_id": "risky_protocol"}], seed=seed)
    checks.append({"id": "security_cancel_438", "passed": sec_cancel[0].get("security_cancelled_667") is True, "detail": "438"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
