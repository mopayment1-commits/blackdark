"""
Epistemic Humility Gate — #1021 (+ #1067 merged).

I DON'T KNOW when evidence conflicts, confidence is low, or data is insufficient.
Anti-fabrication: no inflated confidence scores.
"""

from __future__ import annotations

import json
import logging
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger("BLACKDARK.EpistemicHumility")

_FEATURE_REF = 1021
_MERGED_REF = 1067
_STANDALONE = False
_SEED_PATH = Path("data/trust_core_seed.json")
_RUNBOOK = "docs/infrastructure/EPISTEMIC_HUMILITY_GATE.md"

_gate_log: list[dict[str, Any]] = []


def reset_epistemic_gate_state() -> None:
    _gate_log.clear()


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
    return seed.get("epistemic_humility_gate_1021") or {}


def epistemic_humility_status_1021(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    policy = cfg.get("policy") or {}
    return {
        "ok": True,
        "feature_ref": _FEATURE_REF,
        "merged_feature_ref": _MERGED_REF,
        "standalone": False,
        "standalone_rejected": True,
        "merged_into": "Intelligence Ledger /intelligence/gate",
        "policy": {
            "anti_fabrication": policy.get("anti_fabrication", True),
            "rule_based_only_sprint_2": policy.get("rule_based_only_sprint_2", True),
            "no_ml_confidence_fabrication": policy.get("no_ml_confidence_fabrication", True),
            "no_override": policy.get("no_override", True),
            "public_methodology": policy.get("public_methodology", True),
        },
        "triggers": cfg.get("triggers") or {},
        "reason_codes": cfg.get("reason_codes") or [],
        "integrations": cfg.get("integrations") or {},
        "runbook": _RUNBOOK,
        "timestamp": _utcnow(),
    }


def evaluate_epistemic_gate_1021(
    *,
    facts: list[dict[str, Any]] | None = None,
    confidence_score: float = 7.0,
    sample_size: int = 50,
    falsification_met: bool = False,
    seed: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based gate — CONFLICT / LOW_CONFIDENCE / INSUFFICIENT_DATA / FALSIFICATION."""
    seed = seed or _load_seed()
    cfg = _cfg(seed)
    triggers = cfg.get("triggers") or {}
    conflict_threshold = float(triggers.get("conflict_threshold_pct", 15.0))
    min_confidence = float(triggers.get("min_confidence_score", 5.0))
    min_sample = int(triggers.get("min_sample_size", 30))

    reason_code: str | None = None
    evidence_summary: dict[str, Any] = {}

    if falsification_met:
        reason_code = "FALSIFICATION_CONDITION_MET"
    elif sample_size < min_sample:
        reason_code = "INSUFFICIENT_DATA"
        evidence_summary["sample_size"] = sample_size
        evidence_summary["minimum_required"] = min_sample
    elif confidence_score < min_confidence:
        reason_code = "LOW_CONFIDENCE"
        evidence_summary["confidence_score"] = confidence_score
        evidence_summary["minimum_required"] = min_confidence
    elif facts and len(facts) >= 2:
        vals = [float(f.get("value", 0)) for f in facts if f.get("value") is not None]
        if len(vals) >= 2 and vals[0] != 0:
            divergence = abs((vals[1] - vals[0]) / vals[0]) * 100
            if divergence > conflict_threshold:
                reason_code = "CONFLICT"
                evidence_summary["divergence_pct"] = round(divergence, 2)
                evidence_summary["threshold_pct"] = conflict_threshold

    blocked = reason_code is not None
    result = {
        "ok": not blocked,
        "blocked": blocked,
        "gate_passed": not blocked,
        "reason_code": reason_code,
        "output": "I DON'T KNOW" if blocked else "PROCEED",
        "evidence_summary": evidence_summary,
        "missing_data": evidence_summary if blocked else [],
        "legal_disclaimer": (
            "بيانات غير كافية لرؤى موثوقة — ليس توصية مالية"
            if blocked
            else None
        ),
        "no_guaranteed_prediction": True,
        "timestamp": _utcnow(),
    }
    if blocked:
        _log_gate_decision(result, seed=seed)
        _publish_abstention_to_ledger(result, seed=seed)
    return result


def record_falsification_trigger_1021(result: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    evaluate_epistemic_gate_1021(falsification_met=True, seed=seed)


def _log_gate_decision(result: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    entry = {
        "gate_id": f"eph_{uuid.uuid4().hex[:8]}",
        **result,
        "append_only": True,
    }
    _gate_log.append(entry)


def _publish_abstention_to_ledger(result: dict[str, Any], *, seed: dict[str, Any] | None = None) -> None:
    try:
        from bd_platform.public_accuracy_ledger import publish_ledger_entry_1065
        publish_ledger_entry_1065(
            prediction_id=f"abstain_{uuid.uuid4().hex[:8]}",
            asset="MULTI",
            signal_type="gate_abstention",
            outcome="abstained",
            confidence=0.0,
            seed=seed,
        )
    except ImportError:
        logger.debug("public ledger bridge unavailable for abstention")


def run_epistemic_gate_e2e_1021(*, seed: dict[str, Any] | None = None) -> dict[str, Any]:
    seed = seed or _load_seed()
    reset_epistemic_gate_state()
    checks: list[dict[str, Any]] = []

    status = epistemic_humility_status_1021(seed=seed)
    checks.append({"id": "merged_1067", "passed": status["merged_feature_ref"] == 1067})
    checks.append({"id": "anti_fabrication", "passed": status["policy"]["anti_fabrication"] is True})

    low = evaluate_epistemic_gate_1021(confidence_score=3.0, sample_size=50, seed=seed)
    checks.append({"id": "low_confidence_block", "passed": low["blocked"] is True})
    checks.append({"id": "idont_know_output", "passed": low["output"] == "I DON'T KNOW"})

    conflict = evaluate_epistemic_gate_1021(
        facts=[{"value": 100}, {"value": 130}],
        confidence_score=7.0,
        sample_size=50,
        seed=seed,
    )
    checks.append({"id": "conflict_block", "passed": conflict["reason_code"] == "CONFLICT"})

    insufficient = evaluate_epistemic_gate_1021(confidence_score=7.0, sample_size=10, seed=seed)
    checks.append({"id": "insufficient_data", "passed": insufficient["reason_code"] == "INSUFFICIENT_DATA"})

    ok = evaluate_epistemic_gate_1021(confidence_score=7.0, sample_size=50, seed=seed)
    checks.append({"id": "pass_when_ok", "passed": ok["gate_passed"] is True})

    fals = evaluate_epistemic_gate_1021(falsification_met=True, seed=seed)
    checks.append({"id": "falsification_trigger", "passed": fals["reason_code"] == "FALSIFICATION_CONDITION_MET"})

    all_passed = all(c["passed"] for c in checks)
    return {
        "ok": all_passed,
        "feature_ref": _FEATURE_REF,
        "all_passed": all_passed,
        "checks": checks,
        "timestamp": _utcnow(),
    }
