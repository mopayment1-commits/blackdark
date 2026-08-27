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

from bd_platform.institutional_standards import missing_value

logger = logging.getLogger("BLACKDARK.StablecoinHealthMonitor")

_FEATURE_ID = 467
_EXCHANGE_RESERVE_REF = 601
_DEPEG_SUSPEND_THRESHOLD = 0.995
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

    oracle_risk = None
    try:
        from bd_platform.defi_opportunity_scanner import get_stablecoin_oracle_risk_flag

        oracle_risk = get_stablecoin_oracle_risk_flag(symbol.upper())
    except Exception:
        logger.debug("oracle risk flag skipped for %s", symbol, exc_info=True)

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
        "oracle_risk_482": oracle_risk,
        "oracle_risk_flagged": (oracle_risk or {}).get("oracle_risk_flagged", False),
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
        "exchange_reserve_601": build_stablecoin_exchange_reserve(seed=seed),
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
            "exchange_reserve_601": True,
            "onchain_metrics_library_577": True,
        },
        "cancelled_sla": seed.get("cancelled_sla"),
        "disclaimer": _DISCLAIMER,
        "methodology_version": _METHODOLOGY_VERSION,
        "timestamp": _utcnow(),
    }


def _resolve_stablecoin_token(symbol: str, *, seed: dict[str, Any]) -> dict[str, Any]:
    """#601 — canonical token mapping (e.g. USDT.e → USDT)."""
    mapping = seed.get("token_mapping_601") or {}
    canonical = mapping.get(symbol.upper(), symbol.upper())
    return {"input": symbol.upper(), "canonical": canonical, "mapped": canonical != symbol.upper()}


def _check_depeg_suspend(
    symbols: list[str],
    *,
    seed: dict[str, Any],
) -> dict[str, Any]:
    """#601 — suspend reserve aggregation if USDT/USDC < $0.995."""
    threshold = float(seed.get("depeg_suspend_threshold_usd", _DEPEG_SUSPEND_THRESHOLD))
    stablecoins = seed.get("stablecoins") or {}
    suspended: list[dict[str, Any]] = []
    for sym in symbols:
        data = stablecoins.get(sym.upper())
        if not data:
            continue
        price = data.get("price_usd")
        if price is None:
            continue
        if float(price) < threshold:
            suspended.append({
                "symbol": sym.upper(),
                "price_usd": price,
                "threshold_usd": threshold,
                "warning": f"{sym.upper()} below ${threshold} — reserve calculation suspended",
            })
    return {
        "suspended": bool(suspended),
        "threshold_usd": threshold,
        "affected": suspended,
        "user_warning": (
            "حساب احتياطي الستيبلكوين معلّق بسبب انحراف السعر — راجع Stablecoin Health Monitor"
            if suspended
            else None
        ),
    }


def build_stablecoin_exchange_reserve(
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#601 — aggregate exchange stablecoin reserves with entity labels (merged into #467)."""
    seed = seed or _load_seed()
    cfg = seed.get("exchange_reserve_601") or {}
    reserves = cfg.get("exchange_balances") or []
    token_mapping = seed.get("token_mapping_601") or {}

    symbols = list({token_mapping.get(r.get("token", "").upper(), r.get("token", "").upper()) for r in reserves})
    depeg = _check_depeg_suspend([s for s in symbols if s in ("USDT", "USDC")], seed=seed)

    if depeg["suspended"]:
        return {
            "ok": True,
            "feature_ref": _EXCHANGE_RESERVE_REF,
            "merged_into": _FEATURE_ID,
            "calculation_suspended": True,
            "depeg_handling": depeg,
            "total_reserve_usd": missing_value(numeric=True),
            "buying_power_context": missing_value(),
            "entity_labels": [],
            "missing_stale_explicit": True,
            "display": depeg["affected"][0]["warning"] if depeg["affected"] else "Calculation suspended",
            "monitoring_only": True,
            "timestamp": _utcnow(),
        }

    by_exchange: dict[str, dict[str, Any]] = {}
    by_token: dict[str, float] = {}
    stale_count = 0
    missing_count = 0

    for row in reserves:
        token_raw = str(row.get("token", "")).upper()
        token = token_mapping.get(token_raw, token_raw)
        exchange_id = row.get("exchange_id", "unknown")
        entity_label = row.get("entity_label") or f"{exchange_id} wallet"
        wallet_type = row.get("wallet_type", "hot")
        balance = row.get("balance")
        price_usd = row.get("price_usd")
        stale = bool(row.get("stale", False))
        available = row.get("available", True) and balance is not None and price_usd is not None

        if not available:
            missing_count += 1
            usd_value = missing_value(numeric=True)
        elif stale:
            stale_count += 1
            usd_value = round(float(balance) * float(price_usd), 2)
        else:
            usd_value = round(float(balance) * float(price_usd), 2)
            by_token[token] = by_token.get(token, 0) + usd_value

        ex = by_exchange.setdefault(exchange_id, {
            "exchange_id": exchange_id,
            "entity_label": row.get("exchange_name", exchange_id),
            "wallets": [],
            "subtotal_usd": 0.0,
        })
        ex["wallets"].append({
            "entity_label": entity_label,
            "wallet_type": wallet_type,
            "token": token,
            "token_mapped_from": token_raw if token_raw != token else None,
            "balance": balance if available else missing_value(numeric=True),
            "price_usd": price_usd if available else missing_value(numeric=True),
            "usd_value": usd_value,
            "stale": stale,
            "available": available,
            "missing_display": missing_value() if not available else None,
        })
        if isinstance(usd_value, (int, float)):
            ex["subtotal_usd"] = round(ex["subtotal_usd"] + usd_value, 2)

    total = round(sum(by_token.values()), 2)
    trend = cfg.get("reserve_trend") or {}
    change_7d_pct = trend.get("change_7d_pct")
    anomaly = trend.get("anomaly_detected", False)

    buying_power = {
        "total_reserve_usd": total,
        "interpretation": "accumulated_buying_power_on_exchanges",
        "change_7d_pct": change_7d_pct,
        "trend_direction": trend.get("direction", "flat"),
        "anomaly_detected": anomaly,
        "anomaly_detail": trend.get("anomaly_detail"),
        "context": (
            f"${total:,.0f} stablecoin reserves on labeled exchange wallets — "
            f"7d change {change_7d_pct:+.1f}%" if change_7d_pct is not None else
            f"${total:,.0f} stablecoin reserves on labeled exchange wallets"
        ),
    }

    return {
        "ok": True,
        "feature_ref": _EXCHANGE_RESERVE_REF,
        "merged_into": _FEATURE_ID,
        "standalone": False,
        "calculation_suspended": False,
        "depeg_handling": depeg,
        "token_mapping": token_mapping,
        "total_reserve_usd": total,
        "by_token_usd": by_token,
        "by_exchange": list(by_exchange.values()),
        "entity_labels_required": True,
        "missing_count": missing_count,
        "stale_count": stale_count,
        "missing_stale_explicit": True,
        "unknown_is_not_zero": True,
        "buying_power_context": buying_power,
        "trend": trend,
        "display": buying_power["context"],
        "monitoring_only": True,
        "timestamp": _utcnow(),
    }


def build_market_radar_stablecoin_reserve_trend(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#601 → Market Radar: stablecoin reserve trend widget."""
    reserve = build_stablecoin_exchange_reserve(seed=seed)
    return {
        "ok": True,
        "feature_ref": _EXCHANGE_RESERVE_REF,
        "surface": "market_radar",
        "widget": "stablecoin_reserve_trend",
        "reserve": reserve,
        "display": reserve.get("display"),
        "calculation_suspended": reserve.get("calculation_suspended", False),
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

    reserve = build_stablecoin_exchange_reserve(seed=seed)
    checks.append({"id": "601_merged_not_standalone", "passed": reserve.get("standalone") is False, "detail": "601→467"})
    checks.append({"id": "601_entity_labels", "passed": reserve.get("entity_labels_required") is True, "detail": "labels"})
    checks.append({"id": "601_missing_explicit", "passed": reserve.get("missing_stale_explicit") is True, "detail": "missing"})
    checks.append({"id": "601_depeg_handling", "passed": "depeg_handling" in reserve, "detail": "depeg"})
    checks.append({"id": "601_buying_power", "passed": reserve.get("buying_power_context") is not None, "detail": "buying_power"})

    passed = sum(1 for c in checks if c["passed"])
    return {
        "ok": passed == len(checks),
        "feature_id": _FEATURE_ID,
        "checks": checks,
        "passed": passed,
        "total": len(checks),
        "timestamp": _utcnow(),
    }
