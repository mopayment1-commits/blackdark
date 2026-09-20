"""
Launch-57 canonical #6 evidence-class owner (LIVE / DELAYED / SIM).

Zero legacy/PARKED runtime dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Literal

CanonicalEvidenceClass = Literal[
    "BACKTESTED",
    "SIMULATED",
    "SHADOW_LIVE_FORWARD",
    "PRODUCTION_VERIFIED",
]

EVIDENCE_CLASSES: tuple[str, ...] = (
    "BACKTESTED",
    "SIMULATED",
    "SHADOW_LIVE_FORWARD",
    "PRODUCTION_VERIFIED",
)

_USER_LABELS: dict[str, str] = {
    "PRODUCTION_VERIFIED": "LIVE",
    "SHADOW_LIVE_FORWARD": "LIVE",
    "BACKTESTED": "DELAYED",
    "SIMULATED": "SIM",
}

_USER_DESCRIPTIONS: dict[str, str] = {
    "LIVE": "Production or shadow-live forward evidence — not replay.",
    "DELAYED": "Historical or backtested evidence — not presented as live performance.",
    "SIM": "Simulated or synthetic — never promoted to live metrics.",
}

_SOURCE_HINTS: dict[str, str] = {
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

_STALE_FRESHNESS_STATES = frozenset({"STALE", "UNKNOWN"})

_TRUST_RANK: dict[str, int] = {
    "SIMULATED": 0,
    "BACKTESTED": 1,
    "SHADOW_LIVE_FORWARD": 2,
    "PRODUCTION_VERIFIED": 3,
}


class UserEvidenceLabel(str, Enum):
    LIVE = "LIVE"
    DELAYED = "DELAYED"
    SIM = "SIM"


@dataclass(frozen=True)
class EvidenceClassAssessment:
    canonical_evidence_class: str
    user_facing_label: str
    user_facing_description: str
    visible: bool
    promotion_policy: str
    methodology_version: str
    owner: str
    display_timezone_invariant: bool
    freshness_downgrade_applied: bool

    def to_payload(self) -> dict[str, Any]:
        return {
            "launch_item_id": 6,
            "canonical_evidence_class": self.canonical_evidence_class,
            "user_facing_label": self.user_facing_label,
            "user_facing_description": self.user_facing_description,
            "taxonomy": list(EVIDENCE_CLASSES),
            "visible": self.visible,
            "promotion_policy": self.promotion_policy,
            "methodology_version": self.methodology_version,
            "owner": self.owner,
            "display_timezone_invariant": self.display_timezone_invariant,
            "freshness_downgrade_applied": self.freshness_downgrade_applied,
        }


def _infer_from_source_context(
    *,
    source: str | None = None,
    env_production: bool | None = None,
) -> str:
    src = (source or "").lower()
    for hint, cls in _SOURCE_HINTS.items():
        if hint in src:
            if cls == "SHADOW_LIVE_FORWARD" and env_production is True:
                return "PRODUCTION_VERIFIED"
            return cls
    if env_production is True:
        return "PRODUCTION_VERIFIED"
    return "SHADOW_LIVE_FORWARD"


def infer_canonical_evidence_class(
    *,
    source: str | None = None,
    explicit: str | None = None,
    env_production: bool | None = None,
) -> str:
    """Source-derived context governs; caller explicit may agree but cannot escalate trust."""
    source_derived = _infer_from_source_context(source=source, env_production=env_production)
    if not explicit or explicit not in EVIDENCE_CLASSES:
        return source_derived
    explicit_rank = _TRUST_RANK.get(explicit, 0)
    source_rank = _TRUST_RANK.get(source_derived, 0)
    if explicit_rank > source_rank:
        return source_derived
    if explicit != source_derived:
        return source_derived
    return explicit


def assess_user_evidence_class(
    payload: dict[str, Any],
    *,
    freshness_state: str | None = None,
    display_timezone: str | None = None,
) -> EvidenceClassAssessment:
    """Launch #6 — user-visible evidence class; display timezone cannot alter label."""
    import os

    env_prod = os.getenv("BLACKDARK_PRODUCTION", "").lower() in {"1", "true", "yes"}
    explicit = payload.get("evidence_class") or payload.get("canonical_evidence_class")
    canonical = infer_canonical_evidence_class(
        source=str(payload.get("source") or ""),
        explicit=str(explicit) if explicit else None,
        env_production=env_prod,
    )
    user_label = _USER_LABELS.get(canonical, UserEvidenceLabel.DELAYED.value)
    freshness = (freshness_state or payload.get("freshness_state") or "").upper()
    downgrade = False
    if user_label == UserEvidenceLabel.LIVE.value and freshness in _STALE_FRESHNESS_STATES:
        user_label = UserEvidenceLabel.DELAYED.value
        downgrade = True
    # display_timezone is accepted for contract completeness only — must not change label.
    _ = display_timezone
    return EvidenceClassAssessment(
        canonical_evidence_class=canonical,
        user_facing_label=user_label,
        user_facing_description=_USER_DESCRIPTIONS.get(user_label, ""),
        visible=True,
        promotion_policy="replay_and_simulation_never_become_production_metrics",
        methodology_version="launch57-evidence-class-common-1.1",
        owner="launch57.evidence_class_common",
        display_timezone_invariant=True,
        freshness_downgrade_applied=downgrade,
    )


def attach_evidence_class_metadata(body: dict[str, Any], *, display_timezone: str | None = None) -> dict[str, Any]:
    assessment = assess_user_evidence_class(body, display_timezone=display_timezone)
    out = dict(body)
    out["evidence_class"] = assessment.canonical_evidence_class
    out["evidence_display"] = assessment.to_payload()
    out["evidence_class_visible"] = True
    out["evidence_class_owner"] = "launch57.evidence_class_common"
    return out
