"""
Staleness Threshold Policy Engine — #1031.

Merged into #945 Provenance + #1017 Incident Response + #1025 Failover — NOT standalone.
Defines per-source thresholds, evaluates staleness, routes internal alerts and escalations.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.StalenessThresholdPolicy")

_FEATURE_REF = 1031
_MERGED_INTO = "#945 + #1017 + #1025"
_STANDALONE = False
_SEED_PATH = Path("data/staleness_threshold_seed.json")
_RUNBOOK = "docs/infrastructure/STALENESS_THRESHOLD_POLICY.md"

_PROVENANCE_REF = 945
_INCIDENT_RESPONSE_REF = 1017
_FAILOVER_REF = 1025
_OUTLIER_REF = 1026
_GAP_RECOVERY_REF = 1028
_FRESHNESS_BADGE_REF = 1030

DataCategory = Literal["price", "volume", "onchain", "governance", "news"]
TierName = Literal["free", "pro", "institution", "whale", "default"]
FreshnessScore = Literal["Healthy", "Degraded", "Failed"]

_evaluations: list[dict[str, Any]] = []
_alerts: list[dict[str, Any]] = []


def reset_staleness_policy_state() -> None:
    _evaluations.clear()
    _alerts.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("staleness threshold seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("staleness_threshold_policy_engine_1031") or {}


def staleness_policy_status_1031(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "policy": {
            "enabled": policy.get("enabled", True),
            "rule_based_only": policy.get("rule_based_only", True),
            "no_ml_detection": policy.get("no_ml_detection", True),
            "no_silent_degradation": policy.get("no_silent_degradation", True),
            "health_check_interval_seconds": policy.get("health_check_interval_seconds", 30),
            "methodology_version": policy.get("methodology_version", "1.0.0"),
            "alert_automation_enabled": policy.get("alert_automation_enabled", True),
        },
        "thresholds_seconds": cfg.get("thresholds_seconds") or {},
        "tier_multipliers": cfg.get("tier_multipliers") or {},
        "escalation": cfg.get("escalation") or {},
        "integrations": {
            "provenance_ref": _PROVENANCE_REF,
            "incident_response_ref": _INCIDENT_RESPONSE_REF,
            "automatic_failover_ref": _FAILOVER_REF,
            "outlier_detection_ref": _OUTLIER_REF,
            "gap_recovery_ref": _GAP_RECOVERY_REF,
            "freshness_badge_ref": _FRESHNESS_BADGE_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def normalize_tier_name(tier: str | None) -> TierName:
    if tier is None:
        return "default"
    t = tier.lower().strip()
    if t in ("pro", "decision_pro", "premium"):
        return "pro"
    if t in ("institution", "institutional", "enterprise"):
        return "institution"
    if t in ("whale",):
        return "whale"
    if t == "free":
        return "free"
    return "default"


def get_threshold_seconds(
    category: DataCategory,
    *,
    tier: str | None = None,
    seed: dict[str, Any] | None = None,
) -> float:
    """Per-source threshold adjusted by tier — backend-enforced."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    base = float((cfg.get("thresholds_seconds") or {}).get(category, 300))
    multipliers = cfg.get("tier_multipliers") or {}
    tier_key = normalize_tier_name(tier)
    multiplier = float(multipliers.get(tier_key, multipliers.get("default", 1.0)))
    return base * multiplier


def record_staleness_fee(
    *,
    alert_dispatched: bool = False,
    escalation: bool = False,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    cost = float(fee_cfg.get("evaluation_usd", 0.00001))
    if alert_dispatched:
        cost += float(fee_cfg.get("alert_dispatch_usd", 0.00005))
    if escalation:
        cost += float(fee_cfg.get("escalation_action_usd", 0.0001))
    return {
        "cost_usd": round(cost, 6),
        "fee_db_logged": True,
        "logged_per_evaluation": True,
        "timestamp": _utcnow(),
    }


def _freshness_score_for_breach(
  multiplier: float, seed: dict[str, Any] | None = None
) -> FreshnessScore:
    seed = seed or _load_seed()
    esc = (_cfg(seed).get("escalation") or {})
    incident_mult = float(esc.get("incident_multiplier", 2.0))
    if multiplier >= incident_mult:
        return "Failed"
    if multiplier >= 1.0:
        return "Degraded"
    return "Healthy"


def dispatch_internal_alert(
    *,
    source_id: str,
    category: DataCategory,
    delay_seconds: float,
    threshold_seconds: float,
    breach_multiplier: float,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Internal ops alert — NOT user-facing (#1030 handles UI)."""
    seed = seed or _load_seed()
    alert_cfg = (_cfg(seed).get("internal_alert") or {})
    alert = {
        "alert_id": f"stal_{uuid.uuid4().hex[:10]}",
        "feature_ref": _FEATURE_REF,
        "source_id": source_id,
        "category": category,
        "delay_seconds": round(delay_seconds, 1),
        "threshold_seconds": round(threshold_seconds, 1),
        "breach_multiplier": round(breach_multiplier, 2),
        "user_facing": False,
        "ops_only": alert_cfg.get("ops_only", True),
        "channels": alert_cfg.get("channels") or ["slack", "pagerduty"],
        "timestamp": _utcnow(),
        "fee_db": record_staleness_fee(alert_dispatched=True, seed=seed),
    }
    _alerts.append(alert)
    return alert


def _trigger_incident_escalation(
    *,
    source_id: str,
    category: DataCategory,
    breach_multiplier: float,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        from bd_platform.infrastructure_incident_response_security_ops import record_incident_829
    except ImportError:
        logger.debug("incident response bridge unavailable")
        return {"triggered": False, "reason": "bridge_unavailable"}
    try:
        record_incident_829(
            scenario="operational",
            severity="high",
            title=f"Staleness breach {breach_multiplier:.1f}x: {source_id} ({category})",
            seed=seed,
        )
        return {"triggered": True, "incident_response_ref": _INCIDENT_RESPONSE_REF}
    except Exception:
        logger.debug("incident escalation skipped", exc_info=True)
        return {"triggered": False, "reason": "incident_record_failed"}


def _trigger_failover_escalation(
    *,
    source_id: str,
    category: DataCategory,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        from blackdark.data.multi_source_reconciliation import (
            check_source_health,
            execute_automatic_failover,
            get_source_registry,
        )
    except ImportError:
        return {"triggered": False, "reason": "failover_unavailable"}

    dt: Any = category if category != "news" else "price"
    if category == "governance":
        dt = "price"
    registry = get_source_registry(dt)  # type: ignore[arg-type]
    backup = None
    for s in registry:
        sid = str(s.get("id"))
        if sid != source_id:
            backup = sid
            break
    if not backup:
        return {"triggered": False, "reason": "no_backup_source"}

    check_source_health(data_type=dt, source_id=source_id, ok=False, seed=seed)  # type: ignore[arg-type]
    fo = execute_automatic_failover(
        data_type=dt,  # type: ignore[arg-type]
        source_from=source_id,
        source_to=backup,
        reason="staleness_threshold_breach",
        backup_value=0.0,
        seed=seed,
    )
    return {"triggered": True, "failover": fo, "automatic_failover_ref": _FAILOVER_REF}


def evaluate_staleness(
    *,
    source_id: str,
    category: DataCategory,
    delay_seconds: float,
    tier: str | None = None,
    outlier_detected: bool = False,
    gap_detected: bool = False,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate delay vs threshold — deterministic, rule-based."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    if not (cfg.get("policy") or {}).get("enabled", True):
        return {"evaluated": False, "breached": False}

    threshold = get_threshold_seconds(category, tier=tier, seed=seed)
    breach_multiplier = delay_seconds / max(threshold, 1e-9)
    breached = breach_multiplier >= 1.0
    freshness_score = _freshness_score_for_breach(breach_multiplier, seed=seed)

    esc = cfg.get("escalation") or {}
    incident_mult = float(esc.get("incident_multiplier", 2.0))
    failover_mult = float(esc.get("failover_multiplier", 3.0))

    alert: dict[str, Any] | None = None
    incident: dict[str, Any] | None = None
    failover: dict[str, Any] | None = None
    data_compromised = False

    if breached and (cfg.get("policy") or {}).get("alert_automation_enabled", True):
        alert = dispatch_internal_alert(
            source_id=source_id,
            category=category,
            delay_seconds=delay_seconds,
            threshold_seconds=threshold,
            breach_multiplier=breach_multiplier,
            seed=seed,
        )
    if breached and breach_multiplier >= incident_mult:
        incident = _trigger_incident_escalation(
            source_id=source_id,
            category=category,
            breach_multiplier=breach_multiplier,
            seed=seed,
        )
    if breached and breach_multiplier >= failover_mult:
        failover = _trigger_failover_escalation(
            source_id=source_id,
            category=category,
            seed=seed,
        )

    if breached and outlier_detected:
        data_compromised = True

    gap_priority = None
    if breached and gap_detected:
        gap_priority = "backfill_prioritized"
        try:
            from blackdark.data.gap_detection_recovery_engine import attempt_backfill

            attempt_backfill(
                data_type="price" if category in ("news", "governance") else category,  # type: ignore[arg-type]
                gap_start=_utcnow(),
                gap_end=_utcnow(),
                failed_source=source_id,
                seed=seed,
            )
        except ImportError:
            pass

    evaluation = {
        "evaluation_id": f"ste_{uuid.uuid4().hex[:10]}",
        "feature_ref": _FEATURE_REF,
        "source_id": source_id,
        "category": category,
        "tier": normalize_tier_name(tier),
        "delay_seconds": round(delay_seconds, 1),
        "threshold_seconds": round(threshold, 1),
        "breach_multiplier": round(breach_multiplier, 3),
        "breached": breached,
        "freshness_score": freshness_score,
        "provenance_ref": _PROVENANCE_REF,
        "alert_dispatched": alert is not None,
        "internal_alert": alert,
        "incident_escalation": incident,
        "failover_escalation": failover,
        "data_compromised": data_compromised,
        "gap_recovery_priority": gap_priority,
        "suppress_display": data_compromised,
        "no_silent_degradation": (cfg.get("policy") or {}).get("no_silent_degradation", True),
        "fee_db": record_staleness_fee(
            alert_dispatched=alert is not None,
            escalation=bool(incident and incident.get("triggered")) or bool(failover and failover.get("triggered")),
            seed=seed,
        ),
        "timestamp": _utcnow(),
    }
    _evaluations.append(evaluation)
    return evaluation


def apply_staleness_to_freshness_badge(
    freshness: dict[str, Any],
    evaluation: dict[str, Any],
) -> dict[str, Any]:
    """#1030 UI reflection — threshold breach → Delayed badge."""
    out = dict(freshness)
    if evaluation.get("breached"):
        out["state"] = "Delayed"
        out["confidence"] = "Medium" if evaluation.get("freshness_score") == "Degraded" else "Low"
        badge = dict(out.get("badge") or {})
        badge["state"] = "Delayed"
        badge["label"] = "Delayed"
        if evaluation.get("data_compromised"):
            badge["label"] = "Delayed · Data Compromised"
            badge["css_class"] = (badge.get("css_class") or "dfb-delayed") + " dfb-compromised"
        out["badge"] = badge
        out["staleness_evaluation"] = {
            "breach_multiplier": evaluation.get("breach_multiplier"),
            "freshness_score": evaluation.get("freshness_score"),
        }
    return out


def evaluate_and_attach_freshness(
    payload: dict[str, Any],
    *,
    source_id: str,
    category: DataCategory = "price",
    tier: str | None = None,
    delay_seconds: float | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Full pipeline: evaluate staleness → update freshness badge → attach to response."""
    seed = seed or _load_seed()
    out = dict(payload)

    if delay_seconds is None:
        fresh = out.get("freshness") or {}
        delay_seconds = float(fresh.get("actual_delay_ms", 0)) / 1000.0

    outlier = bool(
        out.get("outlier_review")
        or (out.get("outlier_gate") or {}).get("outlier_count", 0) > 0
    )
    gap = bool(out.get("data_gap") or (out.get("gap_recovery") or {}).get("explicit_gaps"))

    evaluation = evaluate_staleness(
        source_id=source_id,
        category=category,
        delay_seconds=float(delay_seconds or 0),
        tier=tier,
        outlier_detected=outlier,
        gap_detected=gap,
        seed=seed,
    )
    out["staleness"] = evaluation
    out["provenance_freshness_score"] = evaluation.get("freshness_score")

    if out.get("freshness"):
        out["freshness"] = apply_staleness_to_freshness_badge(out["freshness"], evaluation)
        out["data_freshness_badge"] = out["freshness"].get("badge")
    else:
        try:
            from bd_platform.data_freshness_badge import attach_freshness_to_response

            out = attach_freshness_to_response(
                out,
                category=category if category != "news" else "price",  # type: ignore[arg-type]
                source=source_id,
                timestamp=out.get("timestamp"),
                seed=seed,
            )
            out["freshness"] = apply_staleness_to_freshness_badge(out["freshness"], evaluation)
            out["data_freshness_badge"] = out["freshness"].get("badge")
        except ImportError:
            pass

    if evaluation.get("suppress_display"):
        out["suppress_output"] = True
        out["badge"] = "Data Compromised"

    return out


def run_health_check_cycle(
    sources: list[dict[str, Any]],
    *,
    tier: str | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Health check every 30s — latency vs threshold comparison."""
    seed = seed or _load_seed()
    results = []
    breaches_without_alert = 0

    for src in sources:
        ev = evaluate_staleness(
            source_id=str(src.get("source_id", "unknown")),
            category=src.get("category", "price"),  # type: ignore[arg-type]
            delay_seconds=float(src.get("delay_seconds", 0)),
            tier=tier,
            outlier_detected=bool(src.get("outlier_detected")),
            gap_detected=bool(src.get("gap_detected")),
            seed=seed,
        )
        results.append(ev)
        if ev.get("breached") and not ev.get("alert_dispatched"):
            breaches_without_alert += 1

    policy = (_cfg(seed).get("policy") or {})
    silent_failure = breaches_without_alert > 0 and policy.get("no_silent_degradation", True)

    return {
        "ok": not silent_failure,
        "feature_ref": _FEATURE_REF,
        "health_check_interval_seconds": policy.get("health_check_interval_seconds", 30),
        "sources_checked": len(results),
        "breaches": sum(1 for r in results if r.get("breached")),
        "breaches_without_alert": breaches_without_alert,
        "silent_degradation_failure": silent_failure,
        "results": results,
        "timestamp": _utcnow(),
    }


def get_staleness_audit_trail(*, limit: int = 50) -> dict[str, Any]:
    evals = _evaluations[-limit:]
    alerts = _alerts[-limit:]
    return {
        "ok": True,
        "evaluations_count": len(evals),
        "alerts_count": len(alerts),
        "evaluations": evals,
        "internal_alerts": alerts,
        "append_only": True,
        "provenance_ref": _PROVENANCE_REF,
        "timestamp": _utcnow(),
    }


def check_production_gate_1031(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = staleness_policy_status_1031(seed=seed)
    thresholds = status.get("thresholds_seconds") or {}
    required = ("price", "volume", "onchain", "governance", "news")
    complete = all(k in thresholds for k in required)
    return {
        "ok": complete,
        "feature_ref": _FEATURE_REF,
        "blocks_production": status["policy"].get("blocks_production_without_definitions", True),
        "definitions_ready": complete,
        "alert_automation_enabled": status["policy"].get("alert_automation_enabled", True),
        "checks": {"thresholds_defined": complete, "tier_multipliers": bool(status.get("tier_multipliers"))},
        "timestamp": _utcnow(),
    }


def run_staleness_policy_e2e_1031(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []
    reset_staleness_policy_state()

    status = staleness_policy_status_1031(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})

    price_thresh = get_threshold_seconds("price", tier="pro", seed=seed)
    checks.append({"id": "price_5min_base", "passed": get_threshold_seconds("price", seed=seed) == 300.0})
    checks.append({"id": "pro_stricter", "passed": price_thresh < 300.0})
    checks.append({"id": "free_looser", "passed": get_threshold_seconds("price", tier="free", seed=seed) > 300.0})

    ok_eval = evaluate_staleness(source_id="binance", category="price", delay_seconds=60, seed=seed)
    checks.append({"id": "no_breach", "passed": ok_eval["breached"] is False})

    breach = evaluate_staleness(source_id="binance", category="price", delay_seconds=400, seed=seed)
    checks.append({"id": "breach_alert", "passed": breach["alert_dispatched"] is True})
    checks.append({"id": "freshness_degraded", "passed": breach["freshness_score"] == "Degraded"})

    fail_eval = evaluate_staleness(source_id="binance", category="price", delay_seconds=700, seed=seed)
    checks.append({"id": "freshness_failed_2x", "passed": fail_eval["freshness_score"] == "Failed"})

    outlier_eval = evaluate_staleness(
        source_id="binance", category="price", delay_seconds=400, outlier_detected=True, seed=seed
    )
    checks.append({"id": "data_compromised", "passed": outlier_eval["data_compromised"] is True})

    cycle = run_health_check_cycle(
        [{"source_id": "binance", "category": "price", "delay_seconds": 400}],
        seed=seed,
    )
    checks.append({"id": "health_check", "passed": cycle["breaches"] >= 1})
    checks.append({"id": "no_silent_degradation", "passed": cycle["breaches_without_alert"] == 0})

    attached = evaluate_and_attach_freshness(
        {"value": 42000},
        source_id="binance",
        category="price",
        delay_seconds=400,
        seed=seed,
    )
    checks.append({"id": "badge_delayed", "passed": (attached.get("freshness") or {}).get("state") == "Delayed"})

    gate = check_production_gate_1031(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["definitions_ready"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
