"""
Falsifiability Policy — #1064 (Sprint 2 cross-cutting).

Scientific integrity: every insight carries explicit "this would be wrong if..." conditions.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.Falsifiability")

_FEATURE_REF = 1064
_STANDALONE = False
_CROSS_CUTTING = True
_SEED_PATH = Path("data/trust_core_seed.json")
_RUNBOOK = "docs/infrastructure/FALSIFIABILITY_POLICY.md"

ConditionType = Literal["price_based", "time_based", "metric_based"]
_REQUIRED_TYPES = ("price_based", "time_based", "metric_based")

_falsification_audit: list[dict[str, Any]] = []


def reset_falsifiability_state() -> None:
    _falsification_audit.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("falsifiability seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("falsifiability_policy_1064") or {}


def falsifiability_policy_status_1064(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "cross_cutting": _CROSS_CUTTING,
        "policy": {
            "falsification_mandatory": policy.get("falsification_mandatory", True),
            "rule_based_only_sprint_2": policy.get("rule_based_only_sprint_2", True),
            "three_condition_types_required": policy.get("three_condition_types_required", True),
            "public_methodology": policy.get("public_methodology", True),
            "ci_regression_required": policy.get("ci_regression_required", True),
            "legal_protection": policy.get("legal_protection", True),
        },
        "condition_types": cfg.get("condition_types") or list(_REQUIRED_TYPES),
        "integrations": cfg.get("integrations") or {},
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def build_falsification_conditions(
    *,
    asset: str = "BTC",
    price_invalidate_pct: float = 5.0,
    price_invalidate_days: int = 7,
    expiry_hours: int = 72,
    metric_name: str = "volume_24h",
    metric_invalidate_pct: float = 50.0,
    methodology_version: str = "1.0.0",
) -> dict[str, Any]:
    """Build rule-based falsification conditions — 3 types mandatory."""
    expiry = (datetime.now(UTC) + timedelta(hours=expiry_hours)).isoformat()
    return {
        "price_based": {
            "condition": f"This insight is wrong if {asset} price moves more than {price_invalidate_pct}% within {price_invalidate_days} days against the stated direction",
            "threshold_pct": price_invalidate_pct,
            "window_days": price_invalidate_days,
            "asset": asset,
            "rule_based": True,
        },
        "time_based": {
            "condition": f"This insight expires and is invalidated after {expiry_hours} hours without revalidation",
            "expires_at": expiry,
            "window_hours": expiry_hours,
            "rule_based": True,
        },
        "metric_based": {
            "condition": f"This insight is wrong if {metric_name} changes by more than {metric_invalidate_pct}% from baseline within the evaluation window",
            "metric": metric_name,
            "threshold_pct": metric_invalidate_pct,
            "rule_based": True,
        },
        "methodology_version": methodology_version,
        "public_methodology": True,
        "legal_disclaimer": "Explicit falsification conditions — not a guaranteed prediction",
    }


def evaluate_falsification_conditions(
    *,
    conditions: dict[str, Any],
    current_price: float | None = None,
    baseline_price: float | None = None,
    current_metric: float | None = None,
    baseline_metric: float | None = None,
    direction: str = "bullish",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Monitor conditions — trigger if any falsification condition met."""
    seed = seed or _load_seed()
    triggered: list[dict[str, Any]] = []

    price_cond = conditions.get("price_based") or {}
    if current_price and baseline_price and baseline_price > 0:
        move_pct = abs((current_price - baseline_price) / baseline_price) * 100
        threshold = float(price_cond.get("threshold_pct", 5.0))
        against = (
            (direction == "bullish" and current_price < baseline_price)
            or (direction == "bearish" and current_price > baseline_price)
        )
        if move_pct > threshold and against:
            triggered.append({"type": "price_based", "move_pct": move_pct, "threshold_pct": threshold})

    time_cond = conditions.get("time_based") or {}
    expires_at = time_cond.get("expires_at")
    if expires_at:
        try:
            exp = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
            if datetime.now(UTC) >= exp:
                triggered.append({"type": "time_based", "expires_at": expires_at})
        except (TypeError, ValueError):
            pass

    metric_cond = conditions.get("metric_based") or {}
    if current_metric is not None and baseline_metric and baseline_metric > 0:
        change_pct = abs((current_metric - baseline_metric) / baseline_metric) * 100
        threshold = float(metric_cond.get("threshold_pct", 50.0))
        if change_pct > threshold:
            triggered.append({"type": "metric_based", "change_pct": change_pct, "threshold_pct": threshold})

    met = len(triggered) > 0
    result = {
        "ok": not met,
        "falsification_met": met,
        "triggered_conditions": triggered,
        "reason_code": "FALSIFICATION_CONDITION_MET" if met else None,
        "timestamp": _utcnow(),
    }
    if met:
        _record_falsification_event(conditions=conditions, triggered=triggered, seed=seed)
        _trigger_epistemic_gate(result, seed=seed)
    return result


def _trigger_epistemic_gate(result: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    try:
        from bd_platform.epistemic_humility_gate import record_falsification_trigger_1021
        record_falsification_trigger_1021(result, seed=seed)
    except ImportError:
        logger.debug("epistemic humility bridge unavailable")


def _record_falsification_event(
    *, conditions: dict[str, Any], triggered: list[dict[str, Any]], seed: dict[str, Any] | None = None
) -> None:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    entry = {
        "event_id": f"fals_{uuid.uuid4().hex[:8]}",
        "conditions": conditions,
        "triggered": triggered,
        "fee_db": {
            "evaluation_usd": fee_cfg.get("evaluation_usd", 0.00002),
            "logged": True,
        },
        "timestamp": _utcnow(),
        "append_only": True,
    }
    _falsification_audit.append(entry)


def validate_falsification_present_1064(
    payload: dict[str, Any],
    *,
    output_type: str = "insight",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """CI regression target — every output must have falsification conditions."""
    seed = seed or _load_seed()
    fals = payload.get("falsification_conditions") or payload.get("falsification")
    errors: list[str] = []

    if not fals:
        errors.append("missing_falsification_conditions")
    elif isinstance(fals, dict):
        for ctype in _REQUIRED_TYPES:
            if ctype not in fals:
                errors.append(f"missing_{ctype}")
            elif not (fals[ctype].get("condition") or fals[ctype].get("rule_based")):
                errors.append(f"empty_{ctype}")

    expl = payload.get("explanation") or {}
    if expl and "falsification" not in str(expl).lower() and "wrong if" not in str(expl).lower():
        if "falsification_conditions" not in payload:
            errors.append("explanation_missing_when_wrong")

    valid = len(errors) == 0
    return {
        "ok": valid,
        "feature_ref": _FEATURE_REF,
        "output_type": output_type,
        "valid": valid,
        "errors": errors,
        "timestamp": _utcnow(),
    }


def enforce_falsification_on_output_1064(
    payload: dict[str, Any],
    *,
    output_type: str = "insight",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    validation = validate_falsification_present_1064(payload, output_type=output_type, seed=seed)
    policy = (_cfg(seed).get("policy") or {})
    if not validation["valid"] and policy.get("blocks_output_without_falsification", True):
        try:
            from bd_platform.explainability_policy import build_idont_know_explanation
            explanation = build_idont_know_explanation(
                reason_code="FALSIFICATION_CONDITIONS_MISSING",
                missing_data=validation["errors"],
                what_would_change="Provide price_based, time_based, and metric_based falsification conditions",
            )
        except ImportError:
            explanation = {"gate_blocked": True}
        return {
            "ok": False,
            "suppressed": True,
            "reason": "falsifiability_policy_violation",
            "errors": validation["errors"],
            "explanation": explanation,
        }
    return payload


def attach_falsification_to_explanation(
    explanation: dict[str, Any],
    falsification_conditions: dict[str, Any],
) -> dict[str, Any]:
    """#1063 integration — 'why' includes 'when would this be wrong'."""
    expl = dict(explanation)
    breakdown = dict(expl.get("detailed_breakdown") or {})
    breakdown["falsification_conditions"] = falsification_conditions
    breakdown["when_wrong"] = {
        "en": falsification_conditions.get("price_based", {}).get("condition", ""),
        "ar": "سيكون هذا القرار خاطئاً إذا تحققت الشروط المعلنة",
    }
    expl["detailed_breakdown"] = breakdown
    return expl


def run_falsifiability_e2e_1064(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_falsifiability_state()
    checks: list[dict[str, Any]] = []

    status = falsifiability_policy_status_1064(seed=seed)
    checks.append({"id": "cross_cutting", "passed": status["cross_cutting"] is True})
    checks.append({"id": "three_types", "passed": len(status["condition_types"]) >= 3})

    conditions = build_falsification_conditions(asset="BTC")
    checks.append({"id": "build_conditions", "passed": all(t in conditions for t in _REQUIRED_TYPES)})

    valid_payload = {"ok": True, "falsification_conditions": conditions}
    checks.append({
        "id": "validate_present",
        "passed": validate_falsification_present_1064(valid_payload, seed=seed)["valid"] is True,
    })

    blocked = enforce_falsification_on_output_1064({"ok": True}, seed=seed)
    checks.append({"id": "block_missing", "passed": blocked.get("suppressed") is True})

    eval_ok = evaluate_falsification_conditions(
        conditions=conditions,
        current_price=39000,
        baseline_price=42000,
        direction="bullish",
        seed=seed,
    )
    checks.append({"id": "price_trigger", "passed": eval_ok.get("falsification_met") is True})

    expl = attach_falsification_to_explanation({"one_line_summary": {"en": "test"}}, conditions)
    checks.append({"id": "explainability_integration", "passed": "falsification_conditions" in (expl.get("detailed_breakdown") or {})})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
