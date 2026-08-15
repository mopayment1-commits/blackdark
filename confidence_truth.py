"""Confidence truth — never present heuristics as empirical probabilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

ConfidenceType = Literal[
    "empirical_probability",
    "calibrated_probability",
    "model_score",
    "heuristic_score",
    "ranking",
    "insufficient_evidence",
]


@dataclass(frozen=True)
class ConfidenceClaim:
    value: float | None
    confidence_type: ConfidenceType
    sample_size: int = 0
    brier_score: float | None = None
    label: str = ""
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        display = "I_DONT_KNOW"
        if self.confidence_type == "insufficient_evidence" or self.value is None:
            display = "I_DONT_KNOW"
        elif self.confidence_type in {"empirical_probability", "calibrated_probability"}:
            display = f"{float(self.value):.4f}"
        else:
            display = f"{float(self.value):.4f} ({self.confidence_type})"
        return {
            "value": self.value,
            "confidence_type": self.confidence_type,
            "sample_size": self.sample_size,
            "brier_score": self.brier_score,
            "label": self.label,
            "notes": self.notes,
            "display": display,
            "is_probability": self.confidence_type
            in {"empirical_probability", "calibrated_probability"},
        }


def claim_heuristic(score: float, *, label: str = "", notes: str = "") -> ConfidenceClaim:
    return ConfidenceClaim(
        value=max(0.0, min(1.0, float(score))),
        confidence_type="heuristic_score",
        label=label,
        notes=notes or "Not an empirical probability.",
    )


def claim_insufficient(*, label: str = "", notes: str = "") -> ConfidenceClaim:
    return ConfidenceClaim(
        value=None,
        confidence_type="insufficient_evidence",
        label=label,
        notes=notes or "I DON'T KNOW / INSUFFICIENT EVIDENCE",
    )


def claim_calibrated_probability(
    p: float,
    *,
    sample_size: int,
    brier_score: float | None = None,
    min_samples: int = 30,
    label: str = "",
) -> ConfidenceClaim:
    if sample_size < min_samples:
        return claim_insufficient(
            label=label,
            notes=f"sample_size={sample_size} < min_samples={min_samples}",
        )
    return ConfidenceClaim(
        value=max(0.0, min(1.0, float(p))),
        confidence_type="calibrated_probability",
        sample_size=sample_size,
        brier_score=brier_score,
        label=label,
    )


def sanitize_confidence_field(raw: Any) -> dict[str, Any]:
    """Convert ambiguous confidence numbers into typed claims."""
    if raw is None:
        return claim_insufficient().to_dict()
    if isinstance(raw, dict) and "confidence_type" in raw:
        return dict(raw)
    try:
        score = float(raw)
    except (TypeError, ValueError):
        return claim_insufficient(notes="unparseable_confidence").to_dict()
    return claim_heuristic(score).to_dict()
