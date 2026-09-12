"""Evidence origin lineage — DSR-012, DSR-013, D-18."""

from __future__ import annotations

from typing import Any

from cap646.evidence_class import assert_promotion_allowed, infer_evidence_class

EVIDENCE_ORIGIN_LABELS = (
    "BACKTESTED",
    "SIMULATED",
    "FORWARD_SHADOW",
    "VERIFIED_PRODUCTION",
    "INDEPENDENT",
)

# Map cap646 classes to governing doc labels
_LABEL_MAP = {
    "BACKTESTED": "BACKTESTED",
    "SIMULATED": "SIMULATED",
    "SHADOW_LIVE_FORWARD": "FORWARD_SHADOW",
    "PRODUCTION_VERIFIED": "VERIFIED_PRODUCTION",
}


def inherit_evidence_origin(
    *,
    parent_origin: str | None = None,
    parent_class: str | None = None,
    source: str | None = None,
    transform: str | None = None,
) -> dict[str, Any]:
    """Propagate evidence origin across transformations — never upgrade via transform."""
    if parent_origin:
        origin = parent_origin
    elif parent_class:
        origin = _LABEL_MAP.get(parent_class, parent_class)
    else:
        cls = infer_evidence_class(source=source)
        origin = _LABEL_MAP.get(cls, cls)

    return {
        "evidence_origin": origin,
        "parent_origin": parent_origin or origin,
        "transform": transform,
        "inheritance_policy": "no_upgrade_via_transform",
        "source": source,
    }


def propagate_lineage(
    parent: dict[str, Any],
    child: dict[str, Any],
    *,
    transform: str,
) -> dict[str, Any]:
    """Attach inherited origin to child payload."""
    parent_origin = parent.get("evidence_origin") or parent.get("evidence_class")
    parent_class = parent.get("evidence_class")
    lineage = inherit_evidence_origin(
        parent_origin=parent_origin if isinstance(parent_origin, str) else None,
        parent_class=parent_class if isinstance(parent_class, str) else None,
        source=child.get("source"),
        transform=transform,
    )
    out = dict(child)
    out["lineage"] = {
        "parent_id": parent.get("signal_id") or parent.get("decision_id") or parent.get("event_id"),
        "transform": transform,
        **lineage,
    }
    out["evidence_origin"] = lineage["evidence_origin"]
    # Block semantic upgrade
    target = out.get("evidence_class")
    if target and parent_class:
        try:
            assert_promotion_allowed(parent_class, target)  # type: ignore[arg-type]
        except ValueError as exc:
            out["promotion_blocked"] = str(exc)
            out["evidence_class"] = parent_class
    return out
