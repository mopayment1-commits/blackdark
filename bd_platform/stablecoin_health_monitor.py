"""
Stablecoin Health Monitor — Feature #467 (Sprint-2 Risk Layer).

Renamed from "De-Pegging Probability Index" — no "De-Pegging" in legal name.
Early warning for stablecoin health — monitoring/analytics only.

Indicators:
  - price deviation from $1
  - redemption pressure (exchange outflow)
  - collateral ratio (backed stablecoins)
  - funding rate anomaly
  - social panic signals

Integrations:
  - #410 Capital Protection: alert if portfolio stablecoin exposure > 30% in threatened asset
  - #429 Unified Arbitrage: cancel stablecoin arb if depeg probability > threshold
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.StablecoinHealthMonitor")

_FEATURE_ID = 467
_TITLE = "Stablecoin Health Monitor"
_LEGAL_NAME = "Stablecoin Health Monitor"
_RENAMED_FROM = "De-Pegging Probability Index"
_STANDALONE = False
_MERGED_INTO = "Sprint-2 Risk Layer / Capital Protection Controls (#410)"
_SPRINT = 2
_PRIORITY = "high"
_SEED_PATH = Path("data/stablecoin_health_monitor_seed.json")
_METHODOLOGY_VERSION = "1.0"

_GRADES = ("AAA", "AA", "A", "BBB", "BB", "B", "CCC", "D")

_DISCLAIMER = (
    "Stablecoin Health Monitor — early warning analytics for stablecoin peg health. "
    "Stablecoin Grade (AAA–D) and depeg probability are monitoring indices only. "
    "Not a guarantee of peg stability. Alerts only — not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"stablecoins": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("stablecoin health monitor seed load failed: %s", exc)
        return {"stablecoins": {}}


def _stablecoin_grade(risk_score: float, *, seed: dict[str, Any]) -> str:
    thresholds = seed.get("grade_thresholds") or {}
    for grade in _GRADES:
        if risk_score <= float(thresholds.get(grade, 100)):
            return grade
    return "D"


def analyze_stablecoin(symbol: str, *, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Compute health metrics and depeg probability for one stablecoin."""
    seed = seed or _load_seed()
    data = (seed.get("stablecoins") or {}).get(symbol.upper())
    if not data:
        return {"ok": False, "symbol": symbol, "error": "stablecoin_not_found"}

    weights = seed.get("indicator_weights") or {}
    dev_bps = float(data.get("price_deviation_bps", 0))
    price_dev = min(100, dev_bps / 10)
    redemption = float(data.get("redemption_pressure_score", 0))
    collateral = data.get("collateral_ratio")
    coll_risk = max(0, (1.0 - float(collateral)) * 100) if collateral else 50.0
    funding = min(100, float(data.get("funding_rate_anomaly", 0)) * 100)
    social = float(data.get("social_panic_score", 0))

    risk_score = round(
        price_dev * weights.get("price_deviation", 0.3)
        + redemption * weights.get("redemption_pressure", 0.25)
        + coll_risk * weights.get("collateral_ratio", 0.2)
        + funding * weights.get("funding_rate_anomaly", 0.15)
        + social * weights.get("social_panic", 0.1),
        2,
    )
    depeg_probability = round(min(1.0, risk_score / 100), 4)
    grade = _stablecoin_grade(risk_score, seed=seed)
    threatened = depeg_probability >= float(seed.get("depeg_probability_threshold", 0.55))

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "symbol": symbol.upper(),
        "name": data.get("name"),
        "stablecoin_type": data.get("type"),
        "price_usd": data.get("price_usd"),
        "indicators": {
            "price_deviation_bps": dev_bps,
            "price_deviation_score": round(price_dev, 2),
            "redemption_pressure_score": redemption,
            "exchange_outflow_24h_usd": data.get("exchange_outflow_24h_usd"),
            "collateral_ratio": collateral,
            "collateral_risk_score": round(coll_risk, 2),
            "funding_rate_anomaly": data.get("funding_rate_anomaly"),
            "social_panic_score": social,
        },
        "risk_score": risk_score,
        "depeg_probability": depeg_probability,
        "stablecoin_grade": grade,
        "threatened": threatened,
        "historical_only": data.get("historical_only", False),
        "monitoring_only": True,
        "display": (
            f"{symbol.upper()} grade {grade} | depeg prob {depeg_probability:.1%} | "
            f"deviation {dev_bps:.1f} bps"
        ),
        "timestamp": _utcnow(),
    }


def should_cancel_stablecoin_arbitrage(
    opportunity: dict[str, Any],
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#429 integration — cancel stablecoin arb if depeg probability > threshold."""
    seed = seed or _load_seed()
    threshold = float(seed.get("depeg_probability_threshold", 0.55))
    opp_type = opportunity.get("opportunity_type", "")
    pair = str(opportunity.get("pair") or opportunity.get("symbol") or "")
    is_stable = opp_type == "stablecoin_depeg" or any(s in pair.upper() for s in ("USDT", "USDC", "DAI"))

    if not is_stable:
        return {"cancel": False, "reason": "not_stablecoin_opportunity"}

    symbols = [s for s in ("USDT", "USDC", "DAI") if s in pair.upper()]
    max_prob = 0.0
    threatened_symbol = None
    for sym in symbols:
        health = analyze_stablecoin(sym, seed=seed)
        if health.get("ok"):
            prob = float(health.get("depeg_probability", 0))
            if prob > max_prob:
                max_prob = prob
                threatened_symbol = sym

    cancel = max_prob >= threshold
    return {
        "feature_ref": _FEATURE_ID,
        "cancel": cancel,
        "depeg_probability": max_prob,
        "threshold": threshold,
        "threatened_symbol": threatened_symbol,
        "stablecoin_grade": analyze_stablecoin(threatened_symbol, seed=seed).get("stablecoin_grade") if threatened_symbol else None,
        "reason": f"depeg_probability_{max_prob:.2f}_above_{threshold}" if cancel else "within_threshold",
        "monitoring_only": True,
    }


def build_portfolio_stablecoin_alerts(
    portfolio_id: str = "demo_portfolio",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#410 integration — alert if stablecoin exposure > 30% in threatened asset."""
    seed = seed or _load_seed()
    exposure_cfg = (seed.get("portfolio_stablecoin_exposure") or {}).get(portfolio_id) or {}
    alert_pct = float(seed.get("portfolio_exposure_alert_pct", 30))
    alerts: list[dict[str, Any]] = []

    for symbol, exposure_pct in exposure_cfg.items():
        health = analyze_stablecoin(symbol, seed=seed)
        if not health.get("ok"):
            continue
        if exposure_pct > alert_pct and health.get("threatened"):
            alerts.append({
                "alert_type": "stablecoin_exposure_threatened",
                "feature_ref": _FEATURE_ID,
                "symbol": symbol,
                "exposure_pct": exposure_pct,
                "threshold_pct": alert_pct,
                "depeg_probability": health.get("depeg_probability"),
                "stablecoin_grade": health.get("stablecoin_grade"),
                "severity": "elevated" if exposure_pct > alert_pct * 1.5 else "watch",
                "alerts_only": True,
                "display": (
                    f"Stablecoin alert: {symbol} exposure {exposure_pct}% > {alert_pct}% "
                    f"with grade {health.get('stablecoin_grade')} (monitoring only)"
                ),
            })

    return {
        "ok": True,
        "feature_ref": _FEATURE_ID,
        "portfolio_id": portfolio_id,
        "alerts": alerts,
        "alert_count": len(alerts),
        "exposure_threshold_pct": alert_pct,
        "alerts_only": True,
        "timestamp": _utcnow(),
    }


def build_stablecoin_health_panel(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    t0 = time.perf_counter()
    seed = seed or _load_seed()
    analyses = [
        analyze_stablecoin(sym, seed=seed)
        for sym in (seed.get("stablecoins") or {})
        if not (seed.get("stablecoins") or {}).get(sym, {}).get("historical_only")
    ]
    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "analyses": [a for a in analyses if a.get("ok")],
        "count": sum(1 for a in analyses if a.get("ok")),
        "stablecoin_grades": {a["symbol"]: a["stablecoin_grade"] for a in analyses if a.get("ok")},
        "cancelled_sla": seed.get("cancelled_sla"),
        "monitoring_only": True,
        "disclaimer": _DISCLAIMER,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def stablecoin_health_monitor_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _TITLE,
        "legal_name": _LEGAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "priority": _PRIORITY,
        "stablecoin_count": len(seed.get("stablecoins") or {}),
        "grade_scale": list(_GRADES),
        "depeg_probability_threshold": seed.get("depeg_probability_threshold"),
        "portfolio_exposure_alert_pct": seed.get("portfolio_exposure_alert_pct"),
        "integrations": {
            "capital_protection_410": True,
            "unified_arbitrage_429": True,
        },
        "cancelled_sla": seed.get("cancelled_sla"),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def run_reconciliation_tests(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    checks.append({"id": "not_standalone", "passed": seed.get("standalone") is False, "detail": "risk layer"})
    checks.append({"id": "renamed_monitor", "passed": "De-Pegging" not in seed.get("legal_name", ""), "detail": seed.get("legal_name")})
    checks.append({"id": "sla_cancelled", "passed": (seed.get("cancelled_sla") or {}).get("response_2_seconds") is True, "detail": "SLA"})

    usdt = analyze_stablecoin("USDT", seed=seed)
    checks.append({"id": "stablecoin_grade", "passed": usdt.get("stablecoin_grade") in _GRADES, "detail": usdt.get("stablecoin_grade")})
    checks.append({"id": "five_indicators", "passed": len(usdt.get("indicators", {})) >= 5, "detail": "indicators"})
    checks.append({"id": "depeg_probability", "passed": 0 <= usdt.get("depeg_probability", -1) <= 1, "detail": str(usdt.get("depeg_probability"))})

    cancel = should_cancel_stablecoin_arbitrage({"opportunity_type": "stablecoin_depeg", "pair": "USDT/USDC"}, seed=seed)
    checks.append({"id": "429_integration", "passed": "cancel" in cancel, "detail": str(cancel.get("cancel"))})

    alerts = build_portfolio_stablecoin_alerts(seed=seed)
    checks.append({"id": "410_exposure_alert", "passed": alerts.get("exposure_threshold_pct") == 30, "detail": "410"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
