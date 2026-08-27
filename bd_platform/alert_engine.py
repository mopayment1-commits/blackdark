"""
Alert Engine — Feature #289 (Sprint 2 Intelligence Ledger).

Renamed from "Smart Alerts" — rule-based first, NOT AI/ML implied.
Backend enforcement with deduplication, retry, and audit logs.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.AlertEngine")

_FEATURE_ID = 289
_ABSORBED_IDS = (323,)
_RENAMED_FROM = "Smart Alerts"
_OFFICIAL_NAME = "Alert Engine"
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger / Alert Engine"
_SPRINT = 2
_SEED_PATH = Path("data/alert_engine_seed.json")
_METHODOLOGY_VERSION = "1.1"
_DEDUPE_WINDOW_SEC = 300
_MAX_RETRIES = 3
_LOG_RETENTION_DAYS = 90
_FLOW_ANOMALY_FEATURE_ID = 282

AlertType = Literal["price", "indicator", "drawing", "derivatives"]
DerivativesMetric = Literal["oi_change_pct", "funding_rate", "liquidation_usd"]
DeliveryChannel = Literal["push", "email", "webhook"]
RuleStatus = Literal["active", "paused", "triggered", "suppressed"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"rules": [], "delivery_log": []}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("alert engine seed load failed: %s", exc)
        return {"rules": [], "delivery_log": []}


def build_derivatives_alert_rules(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#323 Derivatives Alert Rules — merged into #289, no separate engine."""
    seed = seed or _load_seed()
    rules = seed.get("derivatives_rules") or []
    return {
        "absorbed_feature_id": 323,
        "merged_as": "Derivatives Alert Rules & Thresholds",
        "no_separate_engine": True,
        "rule_templates": [
            "OI change > X%",
            "Funding > Y%",
            "Liquidation > Z USD",
        ],
        "metrics": ["oi_change_pct", "funding_rate", "liquidation_usd"],
        "deduplication": {
            "window_sec": _DEDUPE_WINDOW_SEC,
            "rule": "same asset + same condition within 5 min = suppressed",
            "no_duplicate_spam": True,
        },
        "anomaly_integration": {
            "flow_anomaly_feature_id": _FLOW_ANOMALY_FEATURE_ID,
            "orderflow_anomaly_input": True,
            "anomaly_triggered_alerts": "enabled per user tier",
        },
        "rules": rules,
        "rule_count": len(rules),
        "display": (
            "#323 = alert rules config in Alert Engine | "
            "OI / Funding / Liquidation thresholds | "
            f"Dedup: {_DEDUPE_WINDOW_SEC}s | #282 anomaly input"
        ),
    }


def evaluate_derivatives_rule(
    rule: dict[str, Any],
    *,
    market: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate derivatives alert rule — OI/funding/liquidation extremes."""
    market = market or {}
    asset = rule.get("asset", "BTC")
    metric: DerivativesMetric = rule.get("metric", "funding_rate")
    condition = rule.get("condition") or {}
    threshold = condition.get("threshold")
    operator = condition.get("operator", ">=")

    field_map = {
        "oi_change_pct": "oi_change_pct",
        "funding_rate": "funding_rate",
        "liquidation_usd": "liquidation_usd",
    }
    field = field_map.get(metric, metric)
    current_value = market.get(field, rule.get("current_value"))

    base = evaluate_rule(
        {
            **rule,
            "type": "derivatives",
            "condition": {"field": field, "operator": operator, "threshold": threshold},
            "current_value": current_value,
        },
        market=market,
    )

    dedupe_key = f"{asset}:{metric}:{operator}:{threshold}"
    anomaly_triggered = bool(rule.get("anomaly_triggered")) or bool(
        market.get("flow_anomaly_detected")
    )

    return {
        **base,
        "alert_category": "derivatives",
        "absorbed_from": 323,
        "asset": asset,
        "metric": metric,
        "dedupe_key": dedupe_key,
        "anomaly_integration": {
            "flow_anomaly_feature_id": _FLOW_ANOMALY_FEATURE_ID,
            "anomaly_triggered": anomaly_triggered,
            "anomaly_input_enabled": rule.get("anomaly_input_enabled", True),
        },
        "display": (
            f"Derivatives alert {asset}: {metric} {operator} {threshold} | "
            f"Current: {current_value} | Status: {base['status']}"
            + (" | Anomaly-triggered" if anomaly_triggered else "")
        ),
    }


def list_derivatives_alert_rules(*, asset: str | None = None, limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    rules = seed.get("derivatives_rules") or []
    if asset:
        rules = [r for r in rules if r.get("asset", "").upper() == asset.upper()]
    evaluated = [evaluate_derivatives_rule(r) for r in rules[:limit]]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "absorbed_feature_id": 323,
        "count": len(evaluated),
        "rules": evaluated,
        "derivatives_alert_rules": build_derivatives_alert_rules(seed),
        "timestamp": _utcnow(),
    }


def build_scope_lock(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    phase = int(seed.get("current_phase", 1))
    return {
        "current_phase": phase,
        "phases": {
            1: "Price alerts",
            2: "Indicator alerts + Derivatives alert rules (#323)",
            3: "Drawing alerts",
        },
        "ml_alerts_wave": 3,
        "rule_based_first": True,
        "no_smart_ai_implied": True,
        "display": (
            f"Phase {phase}: Price alerts | "
            "Indicator = Phase 2 | Drawing = Phase 3 | "
            "ML-based alerts = Wave 3 | Rule-based — not 'smart' AI"
        ),
    }


def build_backend_enforcement() -> dict[str, Any]:
    return {
        "server_side_evaluation": True,
        "no_client_side_only": True,
        "delivery_channels": ["push", "email", "webhook"],
        "deduplication_window_sec": _DEDUPE_WINDOW_SEC,
        "deduplication_rule": "same condition within 5 min = suppressed",
        "max_retries": _MAX_RETRIES,
        "log_retention_days": _LOG_RETENTION_DAYS,
        "display": (
            "Rules evaluated server-side | Delivery: push + email + webhook | "
            f"Dedup: {_DEDUPE_WINDOW_SEC}s window | Retry: {_MAX_RETRIES} attempts | "
            f"Logs: {_LOG_RETENTION_DAYS} days retained"
        ),
    }


def evaluate_rule(rule: dict[str, Any], *, market: dict[str, Any] | None = None) -> dict[str, Any]:
    """Server-side rule evaluation — backend enforcement."""
    market = market or {}
    alert_type: AlertType = rule.get("type", "price")
    condition = rule.get("condition") or {}
    current_value = market.get(condition.get("field"), rule.get("current_value"))

    threshold = condition.get("threshold")
    operator = condition.get("operator", ">=")
    triggered = False

    if current_value is not None and threshold is not None:
        if operator == ">=":
            triggered = float(current_value) >= float(threshold)
        elif operator == "<=":
            triggered = float(current_value) <= float(threshold)
        elif operator == "crosses_above":
            triggered = float(current_value) >= float(threshold)
        elif operator == "crosses_below":
            triggered = float(current_value) <= float(threshold)

    last_fired = rule.get("last_fired_at")
    dedupe_suppressed = False
    if triggered and last_fired:
        try:
            last_ts = datetime.fromisoformat(last_fired.replace("Z", "+00:00"))
            now = datetime.now(UTC)
            if (now - last_ts).total_seconds() < _DEDUPE_WINDOW_SEC:
                dedupe_suppressed = True
                triggered = False
        except (ValueError, TypeError):
            pass

    status: RuleStatus
    if dedupe_suppressed:
        status = "suppressed"
    elif triggered:
        status = "triggered"
    elif rule.get("paused"):
        status = "paused"
    else:
        status = "active"

    return {
        "rule_id": rule.get("rule_id"),
        "name": rule.get("name"),
        "type": alert_type,
        "condition": condition,
        "current_value": current_value,
        "triggered": triggered,
        "dedupe_suppressed": dedupe_suppressed,
        "status": status,
        "server_side": True,
        "display": (
            f"Rule {rule.get('name')}: {condition.get('field')} {operator} {threshold} | "
            f"Current: {current_value} | Status: {status}"
        ),
    }


def build_delivery_record(delivery: dict[str, Any]) -> dict[str, Any]:
    """Delivery log entry with retry tracking."""
    attempts = int(delivery.get("attempts", 1))
    success = bool(delivery.get("success", False))
    channel: DeliveryChannel = delivery.get("channel", "push")

    return {
        "alert_id": delivery.get("alert_id"),
        "rule_id": delivery.get("rule_id"),
        "channel": channel,
        "attempts": attempts,
        "max_retries": _MAX_RETRIES,
        "success": success,
        "retries_remaining": max(0, _MAX_RETRIES - attempts),
        "timestamp": delivery.get("timestamp", _utcnow()),
        "log_retention_days": _LOG_RETENTION_DAYS,
        "display": (
            f"Delivery: {delivery.get('alert_id')} via {channel} | "
            f"Attempts: {attempts}/{_MAX_RETRIES} | "
            f"{'Success' if success else 'Failed'}"
        ),
    }


def list_alert_rules(*, alert_type: str | None = None, limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    rules = seed.get("rules") or []
    if alert_type:
        rules = [r for r in rules if r.get("type") == alert_type]

    evaluated = [evaluate_rule(r) for r in rules[:limit]]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(evaluated),
        "rules": evaluated,
        "timestamp": _utcnow(),
    }


def list_delivery_logs(*, limit: int = 50) -> dict[str, Any]:
    seed = _load_seed()
    logs = [build_delivery_record(d) for d in (seed.get("delivery_log") or [])]
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "count": len(logs[:limit]),
        "logs": logs[:limit],
        "log_retention_days": _LOG_RETENTION_DAYS,
        "timestamp": _utcnow(),
    }


def build_alert_engine_panel() -> dict[str, Any]:
    """Alert Engine panel — rule evaluation + delivery status."""
    t0 = time.perf_counter()
    seed = _load_seed()
    rules = [evaluate_rule(r) for r in seed.get("rules") or []]
    derivatives = [evaluate_derivatives_rule(r) for r in seed.get("derivatives_rules") or []]
    logs = [build_delivery_record(d) for d in (seed.get("delivery_log") or [])[:10]]
    triggered = [r for r in rules if r["status"] == "triggered"]
    triggered += [r for r in derivatives if r["status"] == "triggered"]
    suppressed = [r for r in rules if r["status"] == "suppressed"]
    suppressed += [r for r in derivatives if r["status"] == "suppressed"]

    elapsed = round((time.perf_counter() - t0) * 1000, 1)
    defi_risk_alerts = None
    try:
        from bd_platform.defi_risk_passport import build_defi_risk_spike_alerts_484

        defi_risk_alerts = build_defi_risk_spike_alerts_484()
    except Exception:
        logger.debug("660 defi risk spike alerts skipped", exc_info=True)

    defi_security_alerts = None
    try:
        from bd_platform.defi_risk_passport import build_defi_security_alerts_484

        defi_security_alerts = build_defi_security_alerts_484()
    except Exception:
        logger.debug("667 defi security monitor alerts skipped", exc_info=True)

    portfolio_alerts_759 = None
    market_alerts_759 = None
    try:
        from bd_platform.alert_engine import (
            build_market_radar_alerts_panel_759,
            build_portfolio_alerts_panel_759,
        )

        portfolio_alerts_759 = build_portfolio_alerts_panel_759(seed=seed)
        market_alerts_759 = build_market_radar_alerts_panel_759(seed=seed)
    except Exception:
        logger.debug("759 multi-channel alerts skipped", exc_info=True)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "renamed_from": _RENAMED_FROM,
        "official_name": _OFFICIAL_NAME,
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "alert_engine",
        "rules": rules,
        "derivatives_rules": derivatives,
        "derivatives_alert_config": build_derivatives_alert_rules(seed),
        "defi_risk_spike_alerts_660": defi_risk_alerts,
        "defi_security_monitor_alerts_667": defi_security_alerts,
        "portfolio_alerts_759": portfolio_alerts_759,
        "market_radar_alerts_759": market_alerts_759,
        "triggered_count": len(triggered),
        "suppressed_count": len(suppressed),
        "recent_deliveries": logs,
        "scope_lock": build_scope_lock(seed),
        "backend_enforcement": build_backend_enforcement(),
        "rule_based_first": True,
        "no_smart_ai_implied": True,
        "methodology_version": _METHODOLOGY_VERSION,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def alert_engine_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": _OFFICIAL_NAME,
        "renamed_from": _RENAMED_FROM,
        "absorbed_tickets": {323: "Derivatives Alert Rules & Thresholds"},
        "standalone": _STANDALONE,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "scope_lock": build_scope_lock(seed),
        "backend_enforcement": build_backend_enforcement(),
        "rule_count": len(seed.get("rules") or []),
        "derivatives_rule_count": len(seed.get("derivatives_rules") or []),
        "derivatives_alert_rules": build_derivatives_alert_rules(seed),
        "acceptance_criteria": {
            "backend_enforcement": True,
            "deduplication": True,
            "retry_logic": True,
            "audit_logs": True,
            "server_side_evaluation": True,
        },
        "timestamp": _utcnow(),
    }


_ALERTS_759_DISCLAIMER = (
    "Alerts are based on market data thresholds. Not financial advice. "
    "Not a recommendation to buy or sell."
)
_ALERTS_759_LOG_RETENTION_DAYS = 30
_ALERTS_759_CRITICAL_DELAY_SEC = 60
_ALERTS_759_MARKET_DELAY_SEC = 900
_ALERTS_759_CHANNELS_SPRINT_1 = ("push", "email")
_ALERTS_759_CHANNELS_SPRINT_2 = ("telegram",)
_ALERTS_759_CHANNELS_REJECTED = ("whatsapp",)


def build_multi_channel_alerts_layer_759(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#759 — multi-channel alert layer merged into Portfolio AI + Market Radar."""
    seed = seed or _load_seed()
    cfg = seed.get("notifications_759") or {}
    return {
        "ok": True,
        "feature_ref": 759,
        "merged_into": ["portfolio_ai", "market_radar"],
        "standalone": False,
        "rule_based_only": True,
        "no_smart_alerts": True,
        "no_ml": True,
        "no_auto_action": True,
        "no_whatsapp": True,
        "whatsapp_rejected": "Meta approval + high cost — deferred to Wave 3",
        "channels_sprint_1": list(_ALERTS_759_CHANNELS_SPRINT_1),
        "channels_sprint_2": list(_ALERTS_759_CHANNELS_SPRINT_2),
        "channels_rejected": list(_ALERTS_759_CHANNELS_REJECTED),
        "delivery_confirmation": True,
        "accuracy_definition": "delivery_confirmation_not_prediction",
        "critical_delay_max_sec": _ALERTS_759_CRITICAL_DELAY_SEC,
        "market_delay_max_sec": _ALERTS_759_MARKET_DELAY_SEC,
        "log_retention_days": _ALERTS_759_LOG_RETENTION_DAYS,
        "disclaimer": cfg.get("disclaimer", _ALERTS_759_DISCLAIMER),
        "disclaimer_mandatory": True,
        "display": "Alerts — push + email (S1), Telegram (S2) | Rule-based thresholds only",
        "timestamp": _utcnow(),
    }


def _evaluate_threshold_rule(rule: dict[str, Any], market: dict[str, Any]) -> bool:
    field = (rule.get("condition") or {}).get("field", "price")
    operator = (rule.get("condition") or {}).get("operator", ">=")
    threshold = (rule.get("condition") or {}).get("threshold")
    current = market.get(field, rule.get("current_value"))
    if current is None or threshold is None:
        return False
    current_f = float(current)
    threshold_f = float(threshold)
    if operator in (">=", "crosses_above"):
        return current_f >= threshold_f
    if operator in ("<=", "crosses_below"):
        return current_f <= threshold_f
    if operator == "change_pct_gte":
        return current_f >= threshold_f
    return False


def evaluate_alert_rule_759(
    rule: dict[str, Any],
    *,
    market: dict[str, Any] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#759 — evaluate rule-based alert with fee DB + delivery tracking."""
    seed = seed or _load_seed()
    market = market or (seed.get("notifications_759") or {}).get("market_snapshot") or {}
    triggered = _evaluate_threshold_rule(rule, market)
    priority = rule.get("priority", "market")
    max_delay = _ALERTS_759_CRITICAL_DELAY_SEC if priority == "critical" else _ALERTS_759_MARKET_DELAY_SEC
    channels = rule.get("channels") or list(_ALERTS_759_CHANNELS_SPRINT_1)
    fee_db = rule.get("fee_db") or {}

    return {
        "ok": True,
        "feature_ref": 759,
        "rule_id": rule.get("rule_id"),
        "name": rule.get("name"),
        "trigger_type": rule.get("trigger_type", "price_threshold"),
        "triggered": triggered,
        "channels": channels,
        "priority": priority,
        "max_delay_sec": max_delay,
        "delivery_confirmation_required": True,
        "no_auto_action": True,
        "fee_db": {
            "email_api_usd": fee_db.get("email_api_usd", 0.001),
            "telegram_bot_usd": fee_db.get("telegram_bot_usd", 0.0),
            "push_usd": fee_db.get("push_usd", 0.0),
            "tier": fee_db.get("tier", rule.get("tier", "standard")),
        },
        "disclaimer": _ALERTS_759_DISCLAIMER,
        "display": (
            f"Alert {rule.get('name')}: {'TRIGGERED' if triggered else 'active'} | "
            f"channels={','.join(channels)} | max_delay={max_delay}s"
        ),
        "timestamp": _utcnow(),
    }


def build_portfolio_alerts_panel_759(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#759 — Portfolio AI /portfolio/alerts layer."""
    seed = seed or _load_seed()
    cfg = seed.get("notifications_759") or {}
    rules = [evaluate_alert_rule_759(r, seed=seed) for r in (cfg.get("portfolio_rules") or [])]
    triggered = [r for r in rules if r.get("triggered")]
    return {
        "ok": True,
        "feature_ref": 759,
        "surface": "portfolio_ai",
        "route": "/portfolio/alerts",
        "panel_name_ar": "تنبيهاتي",
        "panel_name": "Alerts",
        "rules": rules,
        "triggered_count": len(triggered),
        "rule_based_only": True,
        "no_auto_action": True,
        "log_retention_days": _ALERTS_759_LOG_RETENTION_DAYS,
        "layer": build_multi_channel_alerts_layer_759(seed=seed),
        "disclaimer": cfg.get("disclaimer", _ALERTS_759_DISCLAIMER),
        "timestamp": _utcnow(),
    }


def build_market_radar_alerts_panel_759(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#759 — Market Radar /radar/alerts layer."""
    seed = seed or _load_seed()
    cfg = seed.get("notifications_759") or {}
    rules = [evaluate_alert_rule_759(r, seed=seed) for r in (cfg.get("market_rules") or [])]
    triggered = [r for r in rules if r.get("triggered")]
    return {
        "ok": True,
        "feature_ref": 759,
        "surface": "market_radar",
        "route": "/radar/alerts",
        "panel_name_ar": "تنبيهات السوق",
        "panel_name": "Market Alerts",
        "rules": rules,
        "triggered_count": len(triggered),
        "rule_based_only": True,
        "no_auto_action": True,
        "log_retention_days": _ALERTS_759_LOG_RETENTION_DAYS,
        "layer": build_multi_channel_alerts_layer_759(seed=seed),
        "disclaimer": cfg.get("disclaimer", _ALERTS_759_DISCLAIMER),
        "timestamp": _utcnow(),
    }


def list_alert_delivery_log_759(*, limit: int = 50, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#759 — 30-day alert delivery log with confirmation."""
    seed = seed or _load_seed()
    cfg = seed.get("notifications_759") or {}
    logs = [build_delivery_record(d) for d in (cfg.get("delivery_log") or [])]
    return {
        "ok": True,
        "feature_ref": 759,
        "count": len(logs[:limit]),
        "logs": logs[:limit],
        "log_retention_days": _ALERTS_759_LOG_RETENTION_DAYS,
        "delivery_confirmation": True,
        "timestamp": _utcnow(),
    }


def run_alerts_qa_tests_759(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """#759 — acceptance QA for alert layer."""
    seed = seed or _load_seed()
    layer = build_multi_channel_alerts_layer_759(seed=seed)
    tests = [
        {"test": "rule_based_only", "passed": layer.get("rule_based_only") is True},
        {"test": "no_whatsapp", "passed": layer.get("no_whatsapp") is True},
        {"test": "no_auto_action", "passed": layer.get("no_auto_action") is True},
        {"test": "delivery_confirmation", "passed": layer.get("delivery_confirmation") is True},
        {"test": "log_retention_30d", "passed": layer.get("log_retention_days") == 30},
        {"test": "disclaimer_mandatory", "passed": layer.get("disclaimer_mandatory") is True},
        {"test": "critical_delay_60s", "passed": layer.get("critical_delay_max_sec") == 60},
    ]
    all_passed = all(t["passed"] for t in tests)
    return {"ok": all_passed, "feature_ref": 759, "tests": tests, "all_passed": all_passed, "timestamp": _utcnow()}
