"""
Explainability Policy — #1063 (Sprint 2 cross-cutting).

NOT standalone — backend-enforced contract on every recommendation, alert, signal, insight.
Every output MUST include "why" with 3 explanation levels.
"""

from __future__ import annotations

import json
import logging
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.ExplainabilityPolicy")

_FEATURE_REF = 1063
_STANDALONE = False
_CROSS_CUTTING = True
_SEED_PATH = Path("data/infrastructure_ops_foundation_seed.json")
_RUNBOOK = "docs/infrastructure/EXPLAINABILITY_POLICY.md"

_REQUIRED_LEVELS = ("one_line_summary", "detailed_breakdown", "audit_trail_link")
_FORBIDDEN_PHRASES = (
    "the ai model believes",
    "the model thinks",
    "black box",
    "نموذج الذكاء الاصطناعي يعتقد",
)

_explanation_audit: list[dict[str, Any]] = []


def reset_explainability_state() -> None:
    _explanation_audit.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("explainability seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("explainability_policy_1063") or {}


def explainability_policy_status_1063(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
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
            "why_mandatory": policy.get("why_mandatory", True),
            "rule_based_only_sprint_2": policy.get("rule_based_only_sprint_2", True),
            "no_black_box": policy.get("no_black_box", True),
            "explanation_levels": cfg.get("explanation_levels") or list(_REQUIRED_LEVELS),
            "multilingual": policy.get("multilingual", ["en", "ar"]),
            "ci_regression_required": policy.get("ci_regression_required", True),
            "blocks_output_without_explanation": policy.get("blocks_output_without_explanation", True),
        },
        "integrations": cfg.get("integrations") or {},
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def build_rule_based_explanation(
    *,
    summary_en: str,
    summary_ar: str = "",
    reasons: list[dict[str, Any]] | None = None,
    confidence: float = 0.0,
    source_count: int = 0,
    methodology_version: str = "1.0.0",
    provenance_refs: list[str] | None = None,
    audit_trail_url: str = "",
    freshness_minutes: int | None = None,
    data_source: str = "",
) -> dict[str, Any]:
    """Build 3-level explanation object — rule-based Sprint 2."""
    reasons = reasons or []
    return {
        "one_line_summary": {
            "en": summary_en,
            "ar": summary_ar or summary_en,
        },
        "detailed_breakdown": {
            "reasons": reasons,
            "rule_based_only": True,
            "methodology_version": methodology_version,
            "confidence": {
                "score": round(confidence, 2),
                "scale": "0-10",
                "based_on_sources": source_count,
                "last_updated": _utcnow(),
            },
            "freshness": {
                "minutes_ago": freshness_minutes,
                "source": data_source,
            } if freshness_minutes is not None else None,
        },
        "audit_trail_link": audit_trail_url or "/api/provenance/audit",
        "provenance_refs": provenance_refs or [],
        "no_black_box": True,
    }


def build_idont_know_explanation(
    *,
    reason_code: str,
    missing_data: list[str],
    what_would_change: str,
    language: str = "en",
) -> dict[str, Any]:
    """I DON'T KNOW gate explanation — no silence."""
    return {
        "one_line_summary": {
            "en": f"Insufficient data to provide insight ({reason_code})",
            "ar": f"بيانات غير كافية لتقديم رؤية ({reason_code})",
        },
        "detailed_breakdown": {
            "gate_blocked": True,
            "reason_code": reason_code,
            "missing_data": missing_data,
            "what_would_change_conclusion": what_would_change,
            "rule_based_only": True,
        },
        "audit_trail_link": "/api/epistemic/gate-audit",
        "output_suppressed": True,
    }


def validate_explanation_present_1063(
    payload: dict[str, Any],
    *,
    output_type: str = "insight",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate every API output has required explanation — CI regression target."""
    seed = seed or _load_seed()
    explanation = payload.get("explanation") or payload.get("why")
    errors: list[str] = []

    if not explanation:
        errors.append("missing_explanation")
    elif isinstance(explanation, dict):
        for level in _REQUIRED_LEVELS:
            if level not in explanation:
                errors.append(f"missing_level_{level}")
        text_blob = json.dumps(explanation, ensure_ascii=False).lower()
        for phrase in _FORBIDDEN_PHRASES:
            if phrase in text_blob:
                errors.append(f"forbidden_phrase:{phrase}")

    risk = payload.get("risk_score") or payload.get("risk")
    if risk is not None and isinstance(explanation, dict):
        breakdown = explanation.get("detailed_breakdown") or {}
        reasons = breakdown.get("reasons") or []
        if isinstance(risk, (int, float)) and len(reasons) < 3:
            errors.append("risk_score_needs_3_indicators")

    valid = len(errors) == 0
    result = {
        "ok": valid,
        "feature_ref": _FEATURE_REF,
        "output_type": output_type,
        "valid": valid,
        "errors": errors,
        "timestamp": _utcnow(),
    }
    if valid:
        _record_explanation_fee(output_type=output_type, seed=seed)
    return result


def enforce_explanation_on_output_1063(
    payload: dict[str, Any],
    *,
    output_type: str = "insight",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Backend enforcement — block output without explanation if policy requires."""
    seed = seed or _load_seed()
    validation = validate_explanation_present_1063(payload, output_type=output_type, seed=seed)
    policy = (_cfg(seed).get("policy") or {})
    if not validation["valid"] and policy.get("blocks_output_without_explanation", True):
        return {
            "ok": False,
            "suppressed": True,
            "reason": "explainability_policy_violation",
            "errors": validation["errors"],
            "explanation": build_idont_know_explanation(
                reason_code="EXPLAINABILITY_MISSING",
                missing_data=validation["errors"],
                what_would_change="Provide explanation object with all 3 levels",
            ),
        }
    return payload


def _record_explanation_fee(*, output_type: str, seed: dict[str, Any] | None = None) -> None:
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    entry = {
        "explanation_id": f"exp_{uuid.uuid4().hex[:8]}",
        "output_type": output_type,
        "cost_usd": fee_cfg.get("compute_per_explanation_usd", 0.00005),
        "timestamp": _utcnow(),
        "timestamp_epoch": time.time(),
    }
    _explanation_audit.append(entry)


def check_production_gate_1063(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    status = explainability_policy_status_1063(seed=seed)
    policy = status["policy"]
    checks = {
        "why_mandatory": policy["why_mandatory"] is True,
        "rule_based_sprint_2": policy["rule_based_only_sprint_2"] is True,
        "three_levels": len(policy["explanation_levels"]) >= 3,
        "no_black_box": policy["no_black_box"] is True,
        "ci_regression": policy["ci_regression_required"] is True,
        "multilingual": "ar" in policy["multilingual"] and "en" in policy["multilingual"],
    }
    return {
        "ok": all(checks.values()),
        "feature_ref": _FEATURE_REF,
        "checks": checks,
        "timestamp": _utcnow(),
    }


def run_explainability_e2e_1063(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_explainability_state()
    checks: list[dict[str, Any]] = []

    status = explainability_policy_status_1063(seed=seed)
    checks.append({"id": "cross_cutting", "passed": status["cross_cutting"] is True})
    checks.append({"id": "why_mandatory", "passed": status["policy"]["why_mandatory"] is True})

    explanation = build_rule_based_explanation(
        summary_en="BTC price exceeded 5% above 24h median",
        summary_ar="سعر BTC تجاوز 5% فوق متوسط 24 ساعة",
        reasons=[
            {"indicator": "price_vs_median", "value": "+5.2%", "weight": 0.4},
            {"indicator": "volume_zscore", "value": "2.1σ", "weight": 0.35},
            {"indicator": "onchain_activity", "value": "+12%", "weight": 0.25},
        ],
        confidence=7.5,
        source_count=3,
        freshness_minutes=2,
        data_source="binance+coingecko",
    )
    valid_payload = {"ok": True, "risk_score": 6, "explanation": explanation}
    validation = validate_explanation_present_1063(valid_payload, seed=seed)
    checks.append({"id": "valid_explanation", "passed": validation["valid"] is True})

    invalid = enforce_explanation_on_output_1063({"ok": True, "value": 42}, seed=seed)
    checks.append({"id": "block_without_why", "passed": invalid.get("suppressed") is True})

    idk = build_idont_know_explanation(
        reason_code="INSUFFICIENT_SOURCES",
        missing_data=["on_chain_volume"],
        what_would_change="Adding on-chain volume would enable confidence ≥6",
    )
    checks.append({"id": "idont_know_explanation", "passed": idk.get("output_suppressed") is True})

    gate = check_production_gate_1063(seed=seed)
    checks.append({"id": "production_gate", "passed": gate["ok"] is True})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
