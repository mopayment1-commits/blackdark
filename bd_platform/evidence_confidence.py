"""
Evidence Confidence Framework — Feature #284 (Sprint 2 Intelligence Ledger).

Cross-cutting evidence-quality scoring for research outputs.
NOT probability of price move — measures evidence strength only.
"""

from __future__ import annotations

import json
import logging
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Literal

logger = logging.getLogger("BLACKDARK.EvidenceConfidence")

_FEATURE_ID = 284
_STANDALONE = False
_CROSS_CUTTING = True
_MERGED_INTO = "Intelligence Ledger / Evidence Confidence Framework"
_SPRINT = 2
_SEED_PATH = Path("data/evidence_confidence_seed.json")
_METHODOLOGY_VERSION = "1.0"
_FORMULA_VERSION = "1.0"

_WEIGHTS = {
    "source_quality": 0.30,
    "recency": 0.20,
    "agreement": 0.20,
    "methodology": 0.15,
    "completeness": 0.15,
}

_DISCLAIMER = (
    "This score measures confidence in evidence quality — not investment outcome. "
    "Not probability of profit. Not likelihood of price move. "
    "Past calibration does not guarantee future accuracy."
)

ResolutionMethod = Literal["majority", "expert_weighted"]


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def _load_seed() -> dict[str, Any]:
    if not _SEED_PATH.is_file():
        return {"assessments": {}, "calibration": {}}
    try:
        return json.loads(_SEED_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("evidence confidence seed load failed: %s", exc)
        return {"assessments": {}, "calibration": {}}


def build_formula_documentation() -> dict[str, Any]:
    """Public, versioned scoring formula — no black-box."""
    return {
        "formula_version": _FORMULA_VERSION,
        "methodology_version": _METHODOLOGY_VERSION,
        "weights": _WEIGHTS,
        "formula": (
            "confidence = (source_quality×0.30 + recency×0.20 + agreement×0.20 "
            "+ methodology×0.15 + completeness×0.15) × (1 - contradiction_penalty)"
        ),
        "output_range": "0–100",
        "not_probability_of_price_move": True,
        "not_profit_probability": True,
        "reproducible": True,
        "black_box": False,
        "display": (
            "Weights: source_quality (30%), recency (20%), agreement (20%), "
            "methodology (15%), completeness (15%) | Formula = public | Versioned"
        ),
    }


def compute_contradiction_penalty(
    sources: list[dict[str, Any]],
    *,
    resolution: ResolutionMethod = "expert_weighted",
) -> dict[str, Any]:
    """Contradiction penalty when sources conflict — documented resolution."""
    if len(sources) < 2:
        return {
            "contradiction_detected": False,
            "contradiction_penalty": 0.0,
            "resolution_method": resolution,
            "conflicting_sources": [],
        }

    conclusions = [s.get("conclusion") for s in sources if s.get("conclusion")]
    unique = set(conclusions)
    if len(unique) <= 1:
        return {
            "contradiction_detected": False,
            "contradiction_penalty": 0.0,
            "resolution_method": resolution,
            "conflicting_sources": [],
        }

    conflicting = [s.get("source_id") for s in sources if s.get("conclusion") != conclusions[0]]
    if resolution == "majority":
        from collections import Counter
        counts = Counter(conclusions)
        majority = counts.most_common(1)[0][1]
        penalty = round(1 - majority / len(conclusions), 3)
    else:
        expert_sources = [s for s in sources if s.get("expert_weight", 0) > 0.5]
        if expert_sources:
            expert_conclusion = expert_sources[0].get("conclusion")
            disagreeing = sum(1 for s in sources if s.get("conclusion") != expert_conclusion)
            penalty = round(disagreeing / len(sources) * 0.5, 3)
        else:
            penalty = 0.25

    return {
        "contradiction_detected": True,
        "contradiction_penalty": min(penalty, 0.5),
        "resolution_method": resolution,
        "conflicting_sources": conflicting,
        "display": (
            f"Contradiction: {len(unique)} distinct conclusions | "
            f"Penalty: {min(penalty, 0.5):.1%} | Resolution: {resolution}"
        ),
    }


def compute_evidence_confidence(evidence: dict[str, Any]) -> dict[str, Any]:
    """Reproducible evidence confidence score 0–100."""
    components = {
        "source_quality": float(evidence.get("source_quality", 0)),
        "recency": float(evidence.get("recency", 0)),
        "agreement": float(evidence.get("agreement", 0)),
        "methodology": float(evidence.get("methodology", 0)),
        "completeness": float(evidence.get("completeness", 0)),
    }

    raw_score = sum(components[k] * _WEIGHTS[k] for k in _WEIGHTS)
    sources = evidence.get("sources") or []
    contradiction = compute_contradiction_penalty(
        sources,
        resolution=evidence.get("resolution_method", "expert_weighted"),
    )
    penalty = float(contradiction.get("contradiction_penalty", 0))
    final_score = round(raw_score * (1 - penalty) * 100, 1)

    breakdown = {
        k: round(v * _WEIGHTS[k] * 100, 1) for k, v in components.items()
    }

    return {
        "confidence_score": final_score,
        "raw_score_before_penalty": round(raw_score * 100, 1),
        "components": components,
        "weighted_breakdown": breakdown,
        "weights": _WEIGHTS,
        "contradiction": contradiction,
        "source_count": len(sources),
        "formula_version": _FORMULA_VERSION,
        "reproducible": True,
        "not_probability_of_price_move": True,
        "confidence_in_evidence_quality": True,
        "display": (
            f"Evidence confidence: {final_score}/100 | "
            f"Sources: {len(sources)} | "
            f"Contradiction penalty: {penalty:.1%} | "
            "Measures evidence strength — not investment outcome"
        ),
        "disclaimer": _DISCLAIMER,
    }


def build_calibration_report(seed: dict[str, Any] | None = None) -> dict[str, Any]:
    """Monthly calibration against ground truth — bias tracking."""
    seed = seed or _load_seed()
    cal = seed.get("calibration") or {}
    return {
        "calibration_frequency": "monthly",
        "last_calibration": cal.get("last_calibration"),
        "ground_truth_samples": cal.get("ground_truth_samples", 0),
        "false_positive_rate_pct": cal.get("false_positive_rate_pct"),
        "false_negative_rate_pct": cal.get("false_negative_rate_pct"),
        "bias_detected": cal.get("bias_detected", False),
        "score_adjustment_applied": cal.get("score_adjustment_applied", 0),
        "calibrated": cal.get("calibrated", False),
        "display": (
            f"Calibration: {cal.get('last_calibration', 'pending')} | "
            f"Samples: {cal.get('ground_truth_samples', 0)} | "
            f"FP: {cal.get('false_positive_rate_pct', 'N/A')}% | "
            f"FN: {cal.get('false_negative_rate_pct', 'N/A')}% | "
            f"Bias: {'yes' if cal.get('bias_detected') else 'no'}"
        ),
    }


def build_confidence_assessment(assessment_id: str) -> dict[str, Any]:
    """Full confidence assessment with evidence breakdown."""
    t0 = time.perf_counter()
    seed = _load_seed()
    assessment = (seed.get("assessments") or {}).get(assessment_id)

    if not assessment:
        return {
            "ok": False,
            "feature_id": _FEATURE_ID,
            "error": "assessment_not_found",
            "assessment_id": assessment_id,
        }

    confidence = compute_evidence_confidence(assessment.get("evidence") or {})
    elapsed = round((time.perf_counter() - t0) * 1000, 1)

    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "cross_cutting": _CROSS_CUTTING,
        "surface": "evidence_confidence",
        "assessment_id": assessment_id,
        "title": assessment.get("title"),
        "conclusion": assessment.get("conclusion"),
        "confidence": confidence,
        "formula": build_formula_documentation(),
        "calibration": build_calibration_report(seed),
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "ui_label": "Confidence in evidence quality",
        "not_profit_probability": True,
        "latency_ms": elapsed,
        "timestamp": _utcnow(),
    }


def evidence_confidence_status() -> dict[str, Any]:
    seed = _load_seed()
    return {
        "ok": True,
        "feature_id": _FEATURE_ID,
        "title": "Evidence Confidence Framework",
        "standalone": _STANDALONE,
        "cross_cutting": _CROSS_CUTTING,
        "merged_into": _MERGED_INTO,
        "sprint": _SPRINT,
        "formula": build_formula_documentation(),
        "calibration": build_calibration_report(seed),
        "assessment_count": len(seed.get("assessments") or {}),
        "acceptance_criteria": {
            "formula_documented": True,
            "not_probability_of_price_move": True,
            "contradiction_penalty_documented": True,
            "calibration_tracked": True,
            "reproducible_scoring": True,
        },
        "disclaimer": _DISCLAIMER,
        "disclaimer_hideable": False,
        "timestamp": _utcnow(),
    }
