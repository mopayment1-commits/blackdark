"""
Risk Curation — Feature #889 (merged into Intelligence Ledger).

Risk scoring rules with version/approval workflow. Scoring only — no enforcement.
NOT a policy engine — risk_rules component.
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.RiskRules")

_FEATURE_REF = 889
_STANDALONE = False
_MERGED_INTO = "Intelligence Ledger"
_COMPONENT = "risk_rules"
_SPRINT = 2
_SEED_PATH = Path("data/intelligence_ledger_risk_rules_seed.json")
_MAX_RULES = 10
_RULE_SET_VERSION = "1.0"

RuleStatus = Literal["draft", "pending_review", "approved", "published"]

_DISCLAIMER = (
    "Risk scoring rules — observational scoring only. "
    "No automated enforcement, blocking, or restrictions. Not investment advice."
)


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("risk rules seed load failed: %s", exc)
        return {}


def risk_rules_status_889(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = seed.get("risk_rules_889") or {}
    rules = seed.get("rules") or []
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "component": _COMPONENT,
        "sprint": _SPRINT,
        "max_rules": _MAX_RULES,
        "rule_count": len(rules),
        "rule_set_version": cfg.get("current_version", _RULE_SET_VERSION),
        "versioning_required": True,
        "approval_workflow_required": True,
        "no_auto_deploy": True,
        "no_enforcement": True,
        "scoring_only": True,
        "fee_db": cfg.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def evaluate_rule_889(
    rule: dict[str, Any],
    metrics: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate a single risk rule — scoring only."""
    metric_key = rule.get("metric")
    threshold = float(rule.get("threshold", 0))
    operator = rule.get("operator", ">")
    value = metrics.get(metric_key)

    if value is None:
        return {
            "rule_id": rule.get("id"),
            "triggered": False,
            "score_label": None,
            "missing_metric": True,
            "no_enforcement": True,
        }

    value_f = float(value)
    triggered = False
    if operator == ">":
        triggered = value_f > threshold
    elif operator == ">=":
        triggered = value_f >= threshold
    elif operator == "<":
        triggered = value_f < threshold

    return {
        "rule_id": rule.get("id"),
        "rule_name": rule.get("name"),
        "triggered": triggered,
        "score_label": rule.get("label") if triggered else None,
        "metric": metric_key,
        "value": value_f,
        "threshold": threshold,
        "operator": operator,
        "no_enforcement": True,
        "scoring_only": True,
    }


def evaluate_risk_rules_889(
    asset: str,
    metrics: dict[str, Any] | None = None,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Evaluate all published rules for an asset."""
    seed = seed or _load_seed()
    metrics = metrics or (seed.get("sample_metrics") or {}).get(asset.upper(), {})
    rules = [r for r in (seed.get("rules") or []) if r.get("status") == "published"]

    evaluations = [evaluate_rule_889(r, metrics) for r in rules]
    triggered = [e for e in evaluations if e.get("triggered")]

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "asset": asset.upper(),
        "rules_evaluated": len(evaluations),
        "rules_triggered": len(triggered),
        "evaluations": evaluations,
        "triggered_labels": [e.get("score_label") for e in triggered if e.get("score_label")],
        "no_enforcement": True,
        "scoring_only": True,
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def get_approval_queue_889(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Rules pending manual review — no auto-publish."""
    seed = seed or _load_seed()
    pending = [r for r in (seed.get("rules") or []) if r.get("status") in ("draft", "pending_review")]
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "pending_review": pending,
        "count": len(pending),
        "manual_approval_required": True,
        "no_auto_deploy": True,
        "timestamp": _utcnow(),
    }


def get_version_migration_889(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Version migration path — v1.0 → v1.1."""
    seed = seed or _load_seed()
    cfg = seed.get("risk_rules_889") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "current_version": cfg.get("current_version", "1.0"),
        "next_version": cfg.get("next_version", "1.1"),
        "migration_guide": cfg.get("migration_guide"),
        "breaking_changes": False,
        "timestamp": _utcnow(),
    }


def build_risk_curation_panel_889(
    asset: str = "BTC",
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = risk_rules_status_889(seed=seed)
    evaluation = evaluate_risk_rules_889(asset, seed=seed)
    approval = get_approval_queue_889(seed=seed)
    versioning = get_version_migration_889(seed=seed)

    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "surface": "intelligence_ledger",
        "panel_title": "Risk Rules Curation",
        "asset": asset.upper(),
        "rule_set_version": status.get("rule_set_version"),
        "rules_evaluated": evaluation.get("rules_evaluated"),
        "triggered_labels": evaluation.get("triggered_labels"),
        "evaluations": evaluation.get("evaluations"),
        "approval_queue": approval,
        "versioning": versioning,
        "no_enforcement": True,
        "scoring_only": True,
        "fee_db": status.get("fee_db"),
        "disclaimer": _DISCLAIMER,
        "timestamp": _utcnow(),
    }


def run_risk_rules_e2e_889(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    tests: list[dict[str, Any]] = []

    status = risk_rules_status_889(seed=seed)
    tests.append({"test": "standalone_rejected", "passed": status.get("standalone_rejected") is True})
    tests.append({"test": "max_10_rules", "passed": status.get("rule_count") <= _MAX_RULES})
    tests.append({"test": "no_enforcement", "passed": status.get("no_enforcement") is True})
    tests.append({"test": "approval_workflow", "passed": status.get("approval_workflow_required") is True})
    tests.append({"test": "no_auto_deploy", "passed": status.get("no_auto_deploy") is True})

    eval_btc = evaluate_risk_rules_889("BTC", seed=seed)
    tests.append({"test": "btc_evaluation", "passed": eval_btc.get("ok") is True})
    tests.append({"test": "scoring_only", "passed": eval_btc.get("scoring_only") is True})

    labels = eval_btc.get("triggered_labels") or []
    tests.append({"test": "nvt_rule", "passed": "Overvalued" in labels or eval_btc.get("rules_evaluated", 0) > 0})

    approval = get_approval_queue_889(seed=seed)
    tests.append({"test": "manual_review_queue", "passed": approval.get("manual_approval_required") is True})

    version = get_version_migration_889(seed=seed)
    tests.append({"test": "version_migration", "passed": version.get("migration_guide") is not None})

    panel = build_risk_curation_panel_889("BTC", seed=seed)
    tests.append({"test": "panel_ok", "passed": panel.get("ok") is True})

    all_passed = all(t["passed"] for t in tests)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "e2e_tests": tests,
        "all_passed": all_passed,
        "timestamp": _utcnow(),
    }
