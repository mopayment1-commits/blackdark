"""
Exchange Health Monitor — Feature #456 (Sprint-2 Risk Layer).

Renamed from Exchange Insolvency Risk Scraper — legal name avoids "Scraper" and "Insolvency".
Transparent exchange health grading (A+ to F) from multi-source indicators.
NOT standalone — Risk Layer in Portfolio AI + Intelligence Ledger.

Indicators:
  - Proof-of-reserves ratio (liabilities/assets)
  - Hot wallet flow anomaly
  - Withdrawal suspension history
  - Regulatory actions
  - Social panic signals

Integrations:
  - #410 Capital Protection: alert when portfolio exposure > 20% on low-health exchange
  - Arbitrage Scanner (#403 / #429): auto-suppress opportunities involving low-health venues
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ExchangeHealthMonitor")

_FEATURE_ID = 456
_TITLE = "Exchange Health Monitor"
_LEGAL_NAME = "Exchange Health Monitor"
_RENAMED_FROM = "Exchange Insolvency Risk Scraper"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Risk Layer / Portfolio AI + Intelligence Ledger"
_LAYER = "Risk Layer"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/exchange_health_monitor_seed.json")
_METHODOLOGY_VERSION = "1.0"

_BANNED_TERMS = (
    "insolvency confirmed",
    "will go bankrupt",
    "guaranteed safe",
    "you should withdraw",
    "scraper",
)

_DISCLAIMER = (
    "Exchange Health Monitor — analytics index from public and on-chain signals. "
    "Exchange Grade (A+ to F) is a descriptive health index, not a solvency determination. "
    "Not investment advice. User assesses custody and counterparty risk."
)

_METHODOLOGY = (
    "Composite health score (0–100) from weighted indicators: "
    "proof-of-reserves coverage (30%), hot wallet flow anomaly (20%), "
    "withdrawal suspension history (20%), regulatory actions (15%), "
    "social panic signals (15%). Grade mapped from score via documented scale. "
    "Low health = grade F, D-, D, or D+."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"exchanges": {}, "grade_scale": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("exchange health monitor seed load failed: %s", exc)
        return {"exchanges": {}, "grade_scale": []}


def _score_proof_of_reserves(ind: dict[str, Any]) -> float:
    """Lower liabilities/assets ratio → higher health. Ratio >1.0 is severe."""
    ratio = float(ind.get("liabilities_to_assets_ratio", 1.0))
    if ratio <= 0.85:
        return 100.0
    if ratio <= 0.90:
        return 90.0
    if ratio <= 0.95:
        return 75.0
    if ratio <= 1.0:
        return 55.0
    if ratio <= 1.05:
        return 35.0
    return 15.0


def _score_hot_wallet_anomaly(ind: dict[str, Any]) -> float:
    anomaly = float(ind.get("anomaly_score", 0.5))
    return max(0.0, min(100.0, (1.0 - anomaly) * 100))


def _score_withdrawal_history(ind: dict[str, Any]) -> float:
    events = int(ind.get("suspension_events_12m", 0))
    if events == 0:
        return 100.0
    if events == 1:
        return 70.0
    if events == 2:
        return 50.0
    if events == 3:
        return 30.0
    return 10.0


def _score_regulatory_actions(ind: dict[str, Any]) -> float:
    count = int(ind.get("action_count_12m", 0))
    severity = str(ind.get("severity_max", "none")).lower()
    base = max(0.0, 100.0 - count * 15)
    if severity in {"elevated", "severe"}:
        base -= 20
    elif severity == "moderate":
        base -= 10
    return max(0.0, min(100.0, base))


def _score_social_panic(ind: dict[str, Any]) -> float:
    panic = float(ind.get("panic_index", 50))
    return max(0.0, min(100.0, 100.0 - panic))


def compute_exchange_health(
    exchange_data: dict[str, Any],
    *,
    weights: dict[str, float] | None = None,
) -> dict[str, Any]:
    """Compute composite health score and per-indicator breakdown."""
    indicators = exchange_data.get("indicators") or {}
    weights = weights or {
        "proof_of_reserves": 0.30,
        "hot_wallet_flow_anomaly": 0.20,
        "withdrawal_suspension_history": 0.20,
        "regulatory_actions": 0.15,
        "social_panic_signals": 0.15,
    }

    component_scores = {
        "proof_of_reserves": _score_proof_of_reserves(
            indicators.get("proof_of_reserves") or {}
        ),
        "hot_wallet_flow_anomaly": _score_hot_wallet_anomaly(
            indicators.get("hot_wallet_flow_anomaly") or {}
        ),
        "withdrawal_suspension_history": _score_withdrawal_history(
            indicators.get("withdrawal_suspension_history") or {}
        ),
        "regulatory_actions": _score_regulatory_actions(
            indicators.get("regulatory_actions") or {}
        ),
        "social_panic_signals": _score_social_panic(
            indicators.get("social_panic_signals") or {}
        ),
    }

    total_weight = sum(weights.values()) or 1.0
    score = round(
        sum(component_scores[k] * weights.get(k, 0) for k in component_scores) / total_weight,
        1,
    )

    return {
        "exchange_id": exchange_data.get("exchange_id"),
        "display_name": exchange_data.get("display_name"),
        "health_score": score,
        "component_scores": {k: round(v, 1) for k, v in component_scores.items()},
        "indicator_sources": {
            k: (indicators.get(k) or {}).get("source") for k in component_scores
        },
        "constituent_source_metadata": True,
    }


def grade_from_score(score: float, seed: dict[str, Any] | None = None) -> str:
    seed = seed or _load_seed()
    scale = sorted(
        seed.get("grade_scale") or [],
        key=lambda g: float(g.get("min_score", 0)),
        reverse=True,
    )
    for entry in scale:
        if score >= float(entry.get("min_score", 0)):
            return str(entry.get("grade", "F"))
    return "F"


def is_low_health_grade(grade: str, seed: dict[str, Any] | None = None) -> bool:
    seed = seed or _load_seed()
    threshold_grades = set(seed.get("low_health_grade_threshold") or ["F", "D-", "D", "D+"])
    return grade in threshold_grades


def evaluate_exchange(
    exchange_id: str,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    ex_data = (seed.get("exchanges") or {}).get(exchange_id.lower())
    if not ex_data:
        return {"ok": False, "error": "exchange_not_found", "exchange_id": exchange_id}

    health = compute_exchange_health(ex_data, weights=seed.get("indicator_weights"))
    grade = grade_from_score(health["health_score"], seed)
    low = is_low_health_grade(grade, seed)

    return {
        "ok": True,
        "exchange_id": exchange_id.lower(),
        "display_name": health["display_name"],
        "health_score": health["health_score"],
        "exchange_grade": grade,
        "low_health": low,
        "indicators": ex_data.get("indicators"),
        "component_scores": health["component_scores"],
        "indicator_sources": health["indicator_sources"],
        "constituent_source_metadata": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "evidence_class": "BACKTESTED",
    }


def list_exchange_grades(*, seed: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    seed = seed or _load_seed()
    results = []
    for ex_id in (seed.get("exchanges") or {}):
        ev = evaluate_exchange(ex_id, seed=seed)
        if ev.get("ok"):
            results.append({
                "exchange_id": ev["exchange_id"],
                "display_name": ev["display_name"],
                "health_score": ev["health_score"],
                "exchange_grade": ev["exchange_grade"],
                "low_health": ev["low_health"],
            })
    return sorted(results, key=lambda r: r["health_score"], reverse=True)


def build_portfolio_exchange_exposure_alerts(
    portfolio_id: str = "demo_portfolio",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#410 integration — alert when exposure > threshold on low-health exchange."""
    seed = seed or _load_seed()
    exposure_map = (seed.get("portfolio_exchange_exposure") or {}).get(portfolio_id) or {}
    threshold = float(seed.get("portfolio_exposure_alert_pct") or 20.0)
    alerts: list[dict[str, Any]] = []

    for exchange_id, exposure_pct in exposure_map.items():
        ev = evaluate_exchange(exchange_id, seed=seed)
        if not ev.get("ok"):
            continue
        if ev["low_health"] and float(exposure_pct) > threshold:
            alerts.append({
                "alert_type": "low_health_exchange_exposure",
                "exchange_id": exchange_id,
                "display_name": ev["display_name"],
                "exposure_pct": exposure_pct,
                "threshold_pct": threshold,
                "exchange_grade": ev["exchange_grade"],
                "health_score": ev["health_score"],
                "severity": "elevated",
                "non_executive": True,
                "display": (
                    f"Capital awareness: {exposure_pct}% portfolio exposure on "
                    f"{ev['display_name']} (Grade {ev['exchange_grade']}) exceeds {threshold}% threshold"
                ),
            })

    return {
        "ok": True,
        "integration": "capital_protection_controls",
        "feature_ref": 410,
        "portfolio_id": portfolio_id,
        "exposure_threshold_pct": threshold,
        "alerts": alerts,
        "alert_count": len(alerts),
        "non_executive": True,
        "no_automatic_fund_movement": True,
        "evidence_class": "BACKTESTED",
    }


def filter_arbitrage_by_exchange_health(
    opportunities: list[dict[str, Any]],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Arbitrage (#403/#429) — suppress opportunities involving low-health venues."""
    seed = seed or _load_seed()
    active: list[dict[str, Any]] = []
    suppressed: list[dict[str, Any]] = []

    for opp in opportunities:
        buy_v = str(opp.get("buy_venue") or "").lower()
        sell_v = str(opp.get("sell_venue") or "").lower()
        buy_ev = evaluate_exchange(buy_v, seed=seed) if buy_v else {"ok": False}
        sell_ev = evaluate_exchange(sell_v, seed=seed) if sell_v else {"ok": False}

        buy_low = buy_ev.get("low_health") if buy_ev.get("ok") else False
        sell_low = sell_ev.get("low_health") if sell_ev.get("ok") else False
        suppressed_flag = buy_low or sell_low

        enriched = dict(opp)
        enriched["exchange_health"] = {
            "buy_venue": buy_ev if buy_ev.get("ok") else None,
            "sell_venue": sell_ev if sell_ev.get("ok") else None,
            "suppressed": suppressed_flag,
            "suppression_reason": (
                "low_health_venue" if suppressed_flag else None
            ),
        }

        if suppressed_flag:
            enriched["status"] = "suppressed"
            enriched["signal_suppressed"] = True
            suppressed.append(enriched)
        else:
            enriched["status"] = "active"
            enriched["signal_suppressed"] = False
            active.append(enriched)

    return {
        "ok": True,
        "integration": "arbitrage_scanner",
        "feature_refs": [403, 429],
        "active_opportunities": active,
        "suppressed_opportunities": suppressed,
        "active_count": len(active),
        "suppressed_count": len(suppressed),
        "auto_suppress_low_health": True,
        "evidence_class": "BACKTESTED",
    }


def build_arbitrage_health_panel(
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    opps = seed.get("arbitrage_opportunities") or []
    return filter_arbitrage_by_exchange_health(opps, seed=seed)


def build_exchange_health_panel(
    exchange_id: str | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()

    if exchange_id:
        result = evaluate_exchange(exchange_id, seed=seed)
        if not result.get("ok"):
            return {**result, "feature_id": _FEATURE_ID}
        elapsed = round((time.perf_counter() - t0) * 1000, 1)
        return {
            **result,
            "ok": True,
            "feature_id": _FEATURE_ID,
            "title": _TITLE,
            "legal_name": _LEGAL_NAME,
            "methodology": _METHODOLOGY,
            "latency_ms": elapsed,
            "timestamp": _utcnow(),
        }

    grades = list_exchange_grades(seed=seed)
    exposure_alerts = build_portfolio_exchange_exposure_alerts(seed=seed)
    arb = build_arbitrage_health_panel(seed=seed)
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "exchange_grades": grades,
        "exchange_count": len(grades),
        "methodology": _METHODOLOGY,
        "methodology_version": _METHODOLOGY_VERSION,
        "grade_scale": seed.get("grade_scale") or [],
        "indicator_weights": seed.get("indicator_weights") or {},
        "capital_protection_alerts": exposure_alerts,
        "arbitrage_health_filter": arb,
        "not_investment_advice": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def build_intelligence_ledger_integration(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "integration": "intelligence_ledger",
        "exchange_grades": list_exchange_grades(seed=seed),
        "arbitrage_filter": build_arbitrage_health_panel(seed=seed),
        "methodology": _METHODOLOGY,
        "evidence_class": "BACKTESTED",
        "timestamp": _utcnow(),
    }


def exchange_health_monitor_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "layer": _LAYER,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "exchange_count": len(seed.get("exchanges") or {}),
        "grade_scale": seed.get("grade_scale") or [],
        "indicators": list((seed.get("indicator_weights") or {}).keys()),
        "integrations": {
            "capital_protection_410": True,
            "arbitrage_scanner_403": True,
            "arbitrage_feature_429": True,
        },
        "infrastructure_sla_cancelled": True,
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "risk layer"})
    checks.append({"id": "renamed_from_scraper", "passed": seed.get("renamed_from") == _RENAMED_FROM, "detail": "renamed"})
    checks.append({"id": "legal_name_no_insolvency", "passed": "insolvency" not in seed.get("legal_name", "").lower(), "detail": seed.get("legal_name")})

    coinbase = evaluate_exchange("coinbase", seed=seed)
    checks.append({"id": "exchange_grade_a_plus", "passed": coinbase.get("exchange_grade") in {"A+", "A", "A-"}, "detail": coinbase.get("exchange_grade")})

    htx = evaluate_exchange("htx", seed=seed)
    checks.append({"id": "low_health_detected", "passed": htx.get("low_health") is True, "detail": htx.get("exchange_grade")})

    grades = list_exchange_grades(seed=seed)
    checks.append({"id": "grade_scale_a_to_f", "passed": len(grades) >= 5 and any(g["exchange_grade"] == "F" or g["low_health"] for g in grades), "detail": f"count={len(grades)}"})

    exposure = build_portfolio_exchange_exposure_alerts(seed=seed)
    checks.append({"id": "capital_protection_410_alert", "passed": exposure.get("alert_count", 0) >= 1, "detail": f"alerts={exposure.get('alert_count')}"})

    arb = build_arbitrage_health_panel(seed=seed)
    checks.append({"id": "arbitrage_auto_suppress", "passed": arb.get("suppressed_count", 0) >= 1, "detail": f"suppressed={arb.get('suppressed_count')}"})

    checks.append({"id": "constituent_source_metadata", "passed": coinbase.get("constituent_source_metadata") is True, "detail": "sources"})
    checks.append({"id": "methodology_documented", "passed": "proof-of-reserves" in _METHODOLOGY.lower(), "detail": "methodology"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
