"""
Unified evidence classes — governing reference mandate.

BACKTESTED | SIMULATED | SHADOW_LIVE_FORWARD | PRODUCTION_VERIFIED
Never promote replay/simulation to production metrics.

CAP646 product facade — taxonomy rules delegated to blackdark.evidence_taxonomy.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Literal

from blackdark.evidence_taxonomy import (
    CAP646_EVIDENCE_CLASSES,
    assert_cap646_promotion_allowed,
    can_promote_cap646_evidence_class,
    map_cap646_to_temporal,
    map_temporal_to_cap646,
    validate_cap646_evidence_class,
)

EvidenceClass = Literal[
    "BACKTESTED",
    "SIMULATED",
    "SHADOW_LIVE_FORWARD",
    "PRODUCTION_VERIFIED",
]

EVIDENCE_CLASSES: tuple[str, ...] = CAP646_EVIDENCE_CLASSES

_SOURCE_HINTS: dict[str, EvidenceClass] = {
    "market_replay_v1": "BACKTESTED",
    "historical_seed": "BACKTESTED",
    "replay": "BACKTESTED",
    "simulated": "SIMULATED",
    "synthetic": "SIMULATED",
    "paper": "SIMULATED",
    "trade_simulator": "SIMULATED",
    "shadow": "SHADOW_LIVE_FORWARD",
    "oracle": "SHADOW_LIVE_FORWARD",
    "arb_unified_v1": "SHADOW_LIVE_FORWARD",
    "production": "PRODUCTION_VERIFIED",
    "live": "SHADOW_LIVE_FORWARD",
}


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def infer_evidence_class(
    *,
    source: str | None = None,
    env_production: bool | None = None,
    explicit: str | None = None,
) -> EvidenceClass:
    if explicit and explicit in EVIDENCE_CLASSES:
        return explicit  # type: ignore[return-value]
    src = (source or "").lower()
    for hint, cls in _SOURCE_HINTS.items():
        if hint in src:
            if cls == "SHADOW_LIVE_FORWARD" and env_production is True:
                return "PRODUCTION_VERIFIED"
            return cls
    if env_production is True:
        return "PRODUCTION_VERIFIED"
    return "SHADOW_LIVE_FORWARD"


def assert_promotion_allowed(current: EvidenceClass, target: EvidenceClass) -> None:
    assert_cap646_promotion_allowed(current, target)


def to_temporal_evidence_class(
    value: EvidenceClass,
    *,
    source: str | None = None,
) -> str:
    """Cross-domain conversion via canonical adapter (deterministic, fail-closed)."""
    replay_hint = bool(source and "replay" in source.lower())
    return map_cap646_to_temporal(value, replay_hint=replay_hint)


def from_temporal_evidence_class(value: str) -> EvidenceClass:
    """Project temporal class to CAP646 surface via canonical adapter."""
    return map_temporal_to_cap646(value)  # type: ignore[return-value]


def attach_evidence_metadata(payload: dict[str, Any], *, source: str | None = None) -> dict[str, Any]:
    import os

    out = dict(payload)
    env_prod = os.getenv("BLACKDARK_PRODUCTION", "").lower() in {"1", "true", "yes"}
    explicit = out.get("evidence_class")
    cls = infer_evidence_class(source=source or out.get("source"), env_production=env_prod, explicit=explicit)
    validate_cap646_evidence_class(cls)
    out["evidence_class"] = cls
    out["evidence_metadata"] = {
        "class": cls,
        "source": source or out.get("source"),
        "attached_at": _utcnow(),
        "promotion_policy": "replay_and_simulation_never_become_production_metrics",
        "temporal_projection": to_temporal_evidence_class(cls, source=source or out.get("source")),
        "taxonomy_version": "1.0.0",
    }
    return out


def ai_compliance_footer(payload: dict[str, Any]) -> dict[str, Any]:
    """ID642 — AI Output Provenance / Compliance Footer on every AI/data/financial output."""
    out = attach_evidence_metadata(payload)
    prov = out.get("data_provenance") or {}
    fresh = out.get("data_freshness") or {}
    cls = out.get("evidence_class", "SHADOW_LIVE_FORWARD")
    out["compliance_footer"] = {
        "evidence_class": cls,
        "provenance_score": prov.get("score") if isinstance(prov, dict) else out.get("provenance_score"),
        "provenance_band": prov.get("band") if isinstance(prov, dict) else out.get("provenance_band"),
        "freshness_state": fresh.get("state") if isinstance(fresh, dict) else None,
        "sources": out.get("sources") or prov.get("components", {}).get("source_diversity", {}).get("categories"),
        "confidence": out.get("confidence") or out.get("truth_score"),
        "unknown_is_not_zero": True,
        "stale_rejected": fresh.get("state") == "stale" if isinstance(fresh, dict) else False,
        "legal": (
            "Decision evidence only. Not financial advice. "
            f"Evidence class={cls}. Stale/untrusted inputs must not pass as success."
        ),
    }
    return out


def reject_if_stale(payload: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
    fresh = payload.get("data_freshness") or {}
    if isinstance(fresh, dict) and fresh.get("state") == "stale":
        return False, {
            **payload,
            "success": False,
            "error": "stale_data_rejected",
            "compliance_footer": ai_compliance_footer(payload).get("compliance_footer"),
        }
    prov_band = payload.get("provenance_band") or (payload.get("data_provenance") or {}).get("band")
    if prov_band == "insufficient":
        return False, {
            **payload,
            "success": False,
            "error": "insufficient_provenance_quarantine",
            "compliance_footer": ai_compliance_footer(payload).get("compliance_footer"),
        }
    return True, payload


__all__ = [
    "EvidenceClass",
    "EVIDENCE_CLASSES",
    "assert_promotion_allowed",
    "attach_evidence_metadata",
    "ai_compliance_footer",
    "can_promote_cap646_evidence_class",
    "from_temporal_evidence_class",
    "infer_evidence_class",
    "reject_if_stale",
    "to_temporal_evidence_class",
]
