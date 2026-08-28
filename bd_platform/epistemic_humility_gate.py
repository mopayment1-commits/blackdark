"""
Epistemic Humility Gate — merged into Intelligence Ledger (Sprint 2).

NOT a standalone service. Policy engine that blocks confident buy/sell outputs
when evidence conflicts, confidence is low, or sample size is insufficient.
Explicit "I DON'T KNOW" instead of false-confidence guesses.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.EpistemicGate")

_FEATURE_REF = "epistemic_humility_gate"
_MERGED_INTO = "Intelligence Ledger"
_STANDALONE = False
_SPRINT = 2
_SEED_PATH = Path("data/epistemic_humility_gate_seed.json")
_RUNBOOK = "docs/features/EPISTEMIC_HUMILITY_GATE.md"

_SIGNAL_ENGINE_REF = 11
_AI_PROVENANCE_REF = 921
_DECISION_INTEL_REF = 938
_ACCURACY_LEDGER_REF = 987
_PROVENANCE_REF = 945

_IDK_TOKEN = "I DON'T KNOW"
_REASON_CODES = frozenset({"CONFLICT", "LOW_CONFIDENCE", "INSUFFICIENT_DATA", "STALE_DATA"})

_gate_evaluations: list[dict[str, Any]] = []
_abstention_log: list[dict[str, Any]] = []


def reset_epistemic_gate_state() -> None:
    _gate_evaluations.clear()
    _abstention_log.clear()


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("epistemic gate seed load failed: %s", exc)
        return {}


def _cfg(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    return seed.get("epistemic_humility_gate") or {}


def epistemic_gate_status(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature": _FEATURE_REF,
        "standalone": _STANDALONE,
        "standalone_rejected": True,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "surface": "/intelligence/gate",
        "policy": {
            "rule_based_only": policy.get("rule_based_only", True),
            "no_ml_gate_logic": policy.get("no_ml_gate_logic", True),
            "confidence_min": policy.get("confidence_min", 5.0),
            "sample_size_min": policy.get("sample_size_min", 30),
            "conflict_threshold_pct": policy.get("conflict_threshold_pct", 15.0),
            "stale_data_hours": policy.get("stale_data_hours", 24),
            "reason_codes": sorted(_REASON_CODES),
            "idk_token": _IDK_TOKEN,
            "public_methodology": policy.get("public_methodology", True),
            "non_custodial": policy.get("non_custodial", True),
            "abstention_target_pct": policy.get("abstention_target_pct", {"min": 20, "max": 40}),
        },
        "integrations": {
            "signal_engine_ref": _SIGNAL_ENGINE_REF,
            "ai_provenance_ref": _AI_PROVENANCE_REF,
            "decision_intel_ref": _DECISION_INTEL_REF,
            "accuracy_ledger_ref": _ACCURACY_LEDGER_REF,
            "provenance_ref": _PROVENANCE_REF,
        },
        "runbook": _RUNBOOK,
        "fee_db": cfg.get("fee_db"),
        "timestamp": _utcnow(),
    }


def get_public_methodology(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Transparent gate rules — no black box."""
    seed = seed or _load_seed()
    methodology = seed.get("public_methodology") or {}
    return {
        "ok": True,
        "feature": _FEATURE_REF,
        "methodology": methodology,
        "triggers": methodology.get("triggers") or [
            {
                "code": "CONFLICT",
                "formula": "abs(fact_a - fact_b) / max(fact_a, fact_b) * 100 > conflict_threshold_pct",
                "threshold_pct": (_cfg(seed).get("policy") or {}).get("conflict_threshold_pct", 15.0),
            },
            {
                "code": "LOW_CONFIDENCE",
                "formula": "confidence_score < confidence_min",
                "threshold": (_cfg(seed).get("policy") or {}).get("confidence_min", 5.0),
            },
            {
                "code": "INSUFFICIENT_DATA",
                "formula": "sample_size < sample_size_min",
                "threshold": (_cfg(seed).get("policy") or {}).get("sample_size_min", 30),
            },
            {
                "code": "STALE_DATA",
                "formula": "data_age_hours > stale_data_hours",
                "threshold_hours": (_cfg(seed).get("policy") or {}).get("stale_data_hours", 24),
            },
        ],
        "timestamp": _utcnow(),
    }


def detect_evidence_conflict(
    fact_a: float,
    fact_b: float,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Deterministic conflict: quantifiable Fact A vs Fact B."""
    seed = seed or _load_seed()
    threshold = float((_cfg(seed).get("policy") or {}).get("conflict_threshold_pct", 15.0))
    denom = max(abs(fact_a), abs(fact_b), 1e-9)
    delta_pct = abs(fact_a - fact_b) / denom * 100.0
    conflict = delta_pct > threshold
    return {
        "ok": not conflict,
        "conflict": conflict,
        "fact_a": fact_a,
        "fact_b": fact_b,
        "delta_pct": round(delta_pct, 4),
        "threshold_pct": threshold,
        "reason_code": "CONFLICT" if conflict else None,
        "timestamp": _utcnow(),
    }


def check_confidence_threshold(
    confidence_score: float,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    minimum = float((_cfg(seed).get("policy") or {}).get("confidence_min", 5.0))
    low = confidence_score < minimum
    return {
        "ok": not low,
        "confidence_score": confidence_score,
        "minimum": minimum,
        "reason_code": "LOW_CONFIDENCE" if low else None,
        "timestamp": _utcnow(),
    }


def check_sample_size(
    sample_size: int,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    minimum = int((_cfg(seed).get("policy") or {}).get("sample_size_min", 30))
    insufficient = sample_size < minimum
    return {
        "ok": not insufficient,
        "sample_size": sample_size,
        "minimum": minimum,
        "reason_code": "INSUFFICIENT_DATA" if insufficient else None,
        "timestamp": _utcnow(),
    }


def check_stale_data(
    data_age_hours: float,
    *,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    seed = seed or _load_seed()
    max_age = float((_cfg(seed).get("policy") or {}).get("stale_data_hours", 24))
    stale = data_age_hours > max_age
    return {
        "ok": not stale,
        "data_age_hours": data_age_hours,
        "max_age_hours": max_age,
        "reason_code": "STALE_DATA" if stale else None,
        "timestamp": _utcnow(),
    }


def build_idk_output(
    *,
    reason_code: str,
    evidence_summary: list[dict[str, Any]] | None = None,
    missing_data: list[str] | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Explicit abstention output — no guess, no wrapped inference."""
    seed = seed or _load_seed()
    disclaimers = seed.get("disclaimers") or {}
    code = reason_code.upper()
    if code not in _REASON_CODES:
        code = "INSUFFICIENT_DATA"
    return {
        "ok": True,
        "output": _IDK_TOKEN,
        "abstained": True,
        "reason_code": code,
        "evidence_summary": evidence_summary or [],
        "missing_data": missing_data or [],
        "disclaimer_en": disclaimers.get(
            "en",
            "Insufficient data for reliable insight — not a prediction or confirmation.",
        ),
        "disclaimer_ar": disclaimers.get(
            "ar",
            "بيانات غير كافية لرؤى موثوقة — لا توقع ولا تأكيد.",
        ),
        "no_buy_sell": True,
        "timestamp": _utcnow(),
    }


def record_gate_evaluation_fee(
    *,
    user_tier: str = "free",
    evidence_count: int = 0,
    confidence_score: float = 0.0,
    abstained: bool = False,
    reason_code: str | None = None,
    analysis_cost_usd: float | None = None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Fee DB — every gate evaluation logged with cost + metadata."""
    seed = seed or _load_seed()
    fee_cfg = (_cfg(seed).get("fee_db") or {})
    cost = analysis_cost_usd
    if cost is None:
        base = float(fee_cfg.get("base_evaluation_usd", 0.0002))
        per_evidence = float(fee_cfg.get("per_evidence_usd", 0.00005))
        cost = round(base + per_evidence * evidence_count, 6)

    entry = {
        "evaluation_id": f"gate_{uuid.uuid4().hex[:10]}",
        "user_tier": user_tier,
        "evidence_count": evidence_count,
        "confidence_score": confidence_score,
        "abstained": abstained,
        "reason_code": reason_code,
        "analysis_cost_usd": cost,
        "fee_db_logged": True,
        "timestamp": _utcnow(),
    }
    _gate_evaluations.append(entry)
    return {"ok": True, "evaluation": entry, "timestamp": _utcnow()}


def log_abstention_to_accuracy_ledger(
    *,
    asset: str,
    reason_code: str,
    gate_evaluation_id: str,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#987 Public Accuracy Ledger — abstentions count as Unresolved/Abstained."""
    seed = seed or _load_seed()
    entry = {
        "ledger_ref": _ACCURACY_LEDGER_REF,
        "asset": asset.upper(),
        "status": "unresolved_abstained",
        "reason_code": reason_code,
        "gate_evaluation_id": gate_evaluation_id,
        "deleted": False,
        "prevents_win_rate_inflation": True,
        "timestamp": _utcnow(),
    }
    _abstention_log.append(entry)
    return {"ok": True, "accuracy_ledger_entry": entry, "timestamp": _utcnow()}


def _build_provenance_metadata(
    *,
    passed: bool,
    reason_code: str | None,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#921 AI Output Provenance — gate decision in footer metadata."""
    footer_note = "Passed epistemic gate" if passed else f"Blocked: insufficient evidence ({reason_code})"
    provenance = {
        "gate_passed": passed,
        "gate_reason_code": reason_code,
        "footer_note": footer_note,
        "integration_ref": _AI_PROVENANCE_REF,
        "visible_in_footer": True,
    }
    try:
        from bd_platform.legal_framework_cross_cutting import build_ai_output_footer_830

        footer = build_ai_output_footer_830(source="epistemic_gate", seed=seed)
        provenance["legal_footer"] = footer.get("footer")
    except ImportError:
        pass
    return provenance


def _build_signal_integration(
    *,
    passed: bool,
    signal_type: str = "opportunity",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#11 Signal Engine — disclaimer on every signal; block if gate fails."""
    result: dict[str, Any] = {
        "integration_ref": _SIGNAL_ENGINE_REF,
        "publish_allowed": passed,
        "rejected_logged": not passed,
    }
    try:
        from bd_platform.legal_framework_cross_cutting import build_signal_disclaimer_830

        disclaimer = build_signal_disclaimer_830(signal_type=signal_type, seed=seed)
        result["disclaimer"] = disclaimer.get("disclaimer")
    except ImportError:
        result["disclaimer"] = {
            "label": "Potential opportunity — not a prediction",
            "not_financial_advice": True,
        }
    return result


def _build_decision_intel_layer(
    *,
    layer: str,
    passed: bool,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#938 Decision Intelligence — Hypothesis without evidence = I DON'T KNOW."""
    effective_layer = "hypothesis" if not passed else layer
    result: dict[str, Any] = {
        "integration_ref": _DECISION_INTEL_REF,
        "layer": effective_layer,
        "unsupported_blocked": not passed and layer in ("inference", "hypothesis"),
    }
    try:
        from bd_platform.legal_framework_cross_cutting import build_decision_intel_disclaimer_830

        disclaimer = build_decision_intel_disclaimer_830(layer=effective_layer, seed=seed)
        result["disclaimer"] = disclaimer
    except ImportError:
        pass
    return result


def evaluate_epistemic_gate(
    *,
    asset: str = "BTC",
    confidence_score: float = 7.0,
    sample_size: int = 100,
    fact_a: float | None = None,
    fact_b: float | None = None,
    data_age_hours: float = 1.0,
    evidence: list[dict[str, Any]] | None = None,
    output_layer: str = "inference",
    user_tier: str = "free",
    signal_type: str = "oracle_direction",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Main gate evaluation — deterministic rule-based triggers only.
    Returns pass or explicit I DON'T KNOW with reason code.
    """
    seed = seed or _load_seed()
    evidence = evidence or []
    triggers: list[dict[str, Any]] = []
    reason_code: str | None = None
    missing_data: list[str] = []

    stale = check_stale_data(data_age_hours, seed=seed)
    if not stale["ok"]:
        reason_code = stale["reason_code"]
        triggers.append(stale)
        missing_data.append("fresh_market_data")

    sample = check_sample_size(sample_size, seed=seed)
    if not sample["ok"] and reason_code is None:
        reason_code = sample["reason_code"]
        triggers.append(sample)
        missing_data.append(f"sample_size>={sample['minimum']}")

    confidence = check_confidence_threshold(confidence_score, seed=seed)
    if not confidence["ok"] and reason_code is None:
        reason_code = confidence["reason_code"]
        triggers.append(confidence)
        missing_data.append(f"confidence>={confidence['minimum']}")

    if fact_a is not None and fact_b is not None:
        conflict = detect_evidence_conflict(fact_a, fact_b, seed=seed)
        if not conflict["ok"] and reason_code is None:
            reason_code = conflict["reason_code"]
            triggers.append(conflict)
            missing_data.append("reconciled_evidence")

    abstained = reason_code is not None
    passed = not abstained

    fee = record_gate_evaluation_fee(
        user_tier=user_tier,
        evidence_count=len(evidence),
        confidence_score=confidence_score,
        abstained=abstained,
        reason_code=reason_code,
        seed=seed,
    )

    accuracy_entry = None
    if abstained:
        accuracy_entry = log_abstention_to_accuracy_ledger(
            asset=asset,
            reason_code=reason_code or "INSUFFICIENT_DATA",
            gate_evaluation_id=fee["evaluation"]["evaluation_id"],
            seed=seed,
        )

    signal_integration = _build_signal_integration(passed=passed, signal_type=signal_type, seed=seed)
    decision_integration = _build_decision_intel_layer(
        layer=output_layer, passed=passed, seed=seed
    )
    provenance = _build_provenance_metadata(passed=passed, reason_code=reason_code, seed=seed)

    if abstained:
        output = build_idk_output(
            reason_code=reason_code or "INSUFFICIENT_DATA",
            evidence_summary=evidence,
            missing_data=missing_data,
            seed=seed,
        )
    else:
        output = {
            "ok": True,
            "output": "PASS",
            "abstained": False,
            "reason_code": None,
            "asset": asset.upper(),
            "confidence_score": confidence_score,
            "sample_size": sample_size,
        }

    return {
        "ok": passed,
        "feature": _FEATURE_REF,
        "merged_into": _MERGED_INTO,
        "surface": "/intelligence/gate",
        "asset": asset.upper(),
        "gate_passed": passed,
        "abstained": abstained,
        "result": output,
        "triggers": triggers,
        "fee_db": fee["evaluation"],
        "accuracy_ledger": accuracy_entry,
        "signal_engine": signal_integration,
        "decision_intelligence": decision_integration,
        "provenance": provenance,
        "timestamp": _utcnow(),
    }


def gate_signal_before_publish(
    *,
    asset: str,
    confidence_score: float,
    sample_size: int,
    fact_a: float | None = None,
    fact_b: float | None = None,
    data_age_hours: float = 1.0,
    evidence: list[dict[str, Any]] | None = None,
    signal_type: str = "oracle_direction",
    user_tier: str = "free",
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """#11 — every signal passes gate before publish; rejected logged to #987."""
    seed = seed or _load_seed()
    evaluation = evaluate_epistemic_gate(
        asset=asset,
        confidence_score=confidence_score,
        sample_size=sample_size,
        fact_a=fact_a,
        fact_b=fact_b,
        data_age_hours=data_age_hours,
        evidence=evidence,
        signal_type=signal_type,
        user_tier=user_tier,
        seed=seed,
    )

    signal_record = None
    if evaluation["gate_passed"]:
        try:
            from signal_registry import register_signal

            signal_record = register_signal(
                signal_type=signal_type,
                asset=asset,
                score=confidence_score,
                verdict="GATE_PASSED",
                features={"evidence_count": len(evidence or []), "gate": "epistemic"},
                provenance={
                    "gate_evaluation_id": evaluation["fee_db"]["evaluation_id"],
                    "integration_ref": _SIGNAL_ENGINE_REF,
                },
                label="pending",
                persist=True,
            )
        except Exception:
            logger.debug("signal registry publish skipped", exc_info=True)
    else:
        try:
            from signal_registry import register_signal

            signal_record = register_signal(
                signal_type="epistemic_abstain",
                asset=asset,
                score=confidence_score,
                verdict=_IDK_TOKEN,
                features={
                    "reason_code": evaluation["result"].get("reason_code"),
                    "gate": "epistemic",
                },
                provenance={
                    "gate_evaluation_id": evaluation["fee_db"]["evaluation_id"],
                    "accuracy_ledger_ref": _ACCURACY_LEDGER_REF,
                    "rejected": True,
                },
                label="abstained",
                persist=True,
            )
        except Exception:
            logger.debug("signal abstention registry skipped", exc_info=True)

    return {
        **evaluation,
        "publish_allowed": evaluation["gate_passed"],
        "signal_record": signal_record,
    }


def get_gate_hit_rate_panel(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Internal monitoring — daily abstention rate (target 20–40%)."""
    seed = seed or _load_seed()
    target = (_cfg(seed).get("policy") or {}).get("abstention_target_pct", {"min": 20, "max": 40})
    total = len(_gate_evaluations)
    abstained = sum(1 for e in _gate_evaluations if e.get("abstained"))
    rate = round(abstained / total * 100, 2) if total else 0.0
    healthy = target.get("min", 20) <= rate <= target.get("max", 40) if total else None

    by_reason: dict[str, int] = {}
    for e in _gate_evaluations:
        if e.get("abstained") and e.get("reason_code"):
            code = str(e["reason_code"])
            by_reason[code] = by_reason.get(code, 0) + 1

    return {
        "ok": True,
        "feature": _FEATURE_REF,
        "total_evaluations": total,
        "abstentions": abstained,
        "abstention_rate_pct": rate,
        "target_pct": target,
        "healthy_epistemic_humility": healthy,
        "by_reason_code": by_reason,
        "accuracy_ledger_abstentions": len(_abstention_log),
        "timestamp": _utcnow(),
    }


def run_epistemic_gate_e2e(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    checks: list[dict[str, Any]] = []

    status = epistemic_gate_status(seed=seed)
    checks.append({"id": "no_standalone", "passed": status["standalone_rejected"] is True})
    checks.append({"id": "sprint_2", "passed": status["sprint"] == 2})
    checks.append({"id": "rule_based_only", "passed": status["policy"]["rule_based_only"] is True})
    checks.append({"id": "no_ml_gate", "passed": status["policy"]["no_ml_gate_logic"] is True})

    methodology = get_public_methodology(seed=seed)
    checks.append({"id": "public_methodology", "passed": len(methodology.get("triggers") or []) >= 3})

    conflict = detect_evidence_conflict(100.0, 130.0, seed=seed)
    checks.append({"id": "conflict_detected", "passed": conflict["conflict"] is True})

    low_conf = check_confidence_threshold(3.5, seed=seed)
    checks.append({"id": "low_confidence", "passed": low_conf["reason_code"] == "LOW_CONFIDENCE"})

    small_n = check_sample_size(12, seed=seed)
    checks.append({"id": "insufficient_data", "passed": small_n["reason_code"] == "INSUFFICIENT_DATA"})

    stale = check_stale_data(48.0, seed=seed)
    checks.append({"id": "stale_data", "passed": stale["reason_code"] == "STALE_DATA"})

    idk = build_idk_output(reason_code="CONFLICT", seed=seed)
    checks.append({"id": "idk_output", "passed": idk["output"] == _IDK_TOKEN})
    checks.append({"id": "arabic_disclaimer", "passed": "بيانات غير كافية" in idk["disclaimer_ar"]})

    pass_eval = evaluate_epistemic_gate(
        asset="BTC",
        confidence_score=8.0,
        sample_size=120,
        fact_a=100.0,
        fact_b=102.0,
        seed=seed,
    )
    checks.append({"id": "gate_pass", "passed": pass_eval["gate_passed"] is True})
    checks.append({"id": "fee_db_on_pass", "passed": pass_eval["fee_db"].get("fee_db_logged") is True})

    abstain_eval = evaluate_epistemic_gate(
        asset="ETH",
        confidence_score=2.0,
        sample_size=10,
        fact_a=100.0,
        fact_b=150.0,
        seed=seed,
    )
    checks.append({"id": "gate_abstain", "passed": abstain_eval["abstained"] is True})
    checks.append({"id": "idk_on_abstain", "passed": abstain_eval["result"]["output"] == _IDK_TOKEN})
    checks.append({"id": "accuracy_ledger", "passed": abstain_eval.get("accuracy_ledger") is not None})
    checks.append({"id": "signal_blocked", "passed": abstain_eval["signal_engine"]["publish_allowed"] is False})
    checks.append({"id": "provenance_blocked", "passed": "Blocked" in abstain_eval["provenance"]["footer_note"]})

    panel = get_gate_hit_rate_panel(seed=seed)
    checks.append({"id": "hit_rate_panel", "passed": panel["total_evaluations"] >= 2})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
