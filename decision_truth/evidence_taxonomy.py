"""Canonical evidence class adapter (DTS-043) — no parallel taxonomy."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import EVIDENCE_CLASSES, assert_promotion_allowed, infer_evidence_class


def resolve_evidence_class(payload: dict[str, Any]) -> dict[str, Any]:
    """Resolve and validate evidence class using canonical cap646 owner."""
    explicit = payload.get("evidence_class")
    inferred = infer_evidence_class(
        source=str(payload.get("source") or ""),
        explicit=explicit if explicit else None,
    )
    promotion_target = payload.get("evidence_class_promotion_target")
    promotion_allowed = True
    promotion_reason = None
    if promotion_target and promotion_target != inferred:
        try:
            assert_promotion_allowed(inferred, promotion_target)  # type: ignore[arg-type]
        except ValueError as exc:
            promotion_allowed = False
            promotion_reason = str(exc)

    return {
        "evidence_class": inferred,
        "canonical_owner": "cap646/evidence_class.py",
        "taxonomy": list(EVIDENCE_CLASSES),
        "inferred_from": "explicit" if explicit else "source_hints",
        "promotion_allowed": promotion_allowed,
        "promotion_reason": promotion_reason,
        "automatic_promotion_blocked": not promotion_allowed,
        "methodology_version": "cap646-evidence-class-1.0",
    }
