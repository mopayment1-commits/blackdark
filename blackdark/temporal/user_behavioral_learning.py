"""User behavioral learning governance (P5 / TEMP-AR-0352..0360)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any, Mapping, Sequence

USER_BEHAVIORAL_LEARNING_CONTRACT_VERSION = "p5.user_behavioral_learning.1.0"
USER_BEHAVIOR_NOT_FINANCIAL_TRUTH = True
USER_ACTION_NOT_OUTCOME_PROOF = True


class BehavioralLearningPurpose(str, Enum):
    PERSONALIZATION = "personalization"
    DISCIPLINE_COACHING = "discipline_coaching"
    UX_ADAPTATION = "ux_adaptation"


@dataclass(frozen=True, slots=True)
class BehavioralConsentRecord:
    user_key: str
    purpose: BehavioralLearningPurpose
    legal_basis: str
    consented_at: datetime
    minimized_fields: tuple[str, ...]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "user_key": self.user_key,
            "purpose": self.purpose.value,
            "legal_basis": self.legal_basis,
            "consented_at": self.consented_at.isoformat(),
            "minimized_fields": list(self.minimized_fields),
        }


@dataclass(frozen=True, slots=True)
class BehavioralSignal:
    signal_id: str
    user_key: str
    action_type: str
    asset: str | None
    followed_system: bool | None
    recorded_at: datetime
    is_outcome_truth: bool = False
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "user_key": self.user_key,
            "action_type": self.action_type,
            "asset": self.asset,
            "followed_system": self.followed_system,
            "recorded_at": self.recorded_at.isoformat(),
            "is_outcome_truth": self.is_outcome_truth,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True, slots=True)
class UserBehavioralLearningState:
    """Authoritative user_behavioral_learning_state."""

    user_key: str
    purpose: BehavioralLearningPurpose
    consent: BehavioralConsentRecord | None
    signals: tuple[BehavioralSignal, ...]
    retention_days: int
    separated_from_objective_outcomes: bool
    anti_manipulation_enabled: bool
    deletion_rights_supported: bool
    eligible_for_adaptation: bool
    abstention_reason: str | None

    def to_metadata(self) -> dict[str, Any]:
        return {
            "user_key": self.user_key,
            "purpose": self.purpose.value,
            "consent": self.consent.to_metadata() if self.consent else None,
            "signals": [s.to_metadata() for s in self.signals],
            "retention_days": self.retention_days,
            "separated_from_objective_outcomes": self.separated_from_objective_outcomes,
            "anti_manipulation_enabled": self.anti_manipulation_enabled,
            "deletion_rights_supported": self.deletion_rights_supported,
            "eligible_for_adaptation": self.eligible_for_adaptation,
            "abstention_reason": self.abstention_reason,
        }


class BehavioralLearningError(ValueError):
    """Fail-closed when behavioral learning violates governance."""


def evaluate_user_action_as_outcome_proof(action_type: str) -> dict[str, Any]:
    """TEMP-AR-0360: clicking Buy is never automatic proof Buy was correct."""
    normalized = (action_type or "").strip().lower()
    prohibited_as_proof = normalized in {"buy", "sell", "follow", "click_buy", "click_sell"}
    return {
        "treated_as_outcome_proof": False,
        "action_type": action_type,
        "prohibited_as_automatic_proof": prohibited_as_proof,
        "user_action_not_outcome_proof": USER_ACTION_NOT_OUTCOME_PROOF,
    }


def record_behavioral_signal(
    *,
    user_key: str,
    action_type: str,
    asset: str | None = None,
    followed_system: bool | None = None,
    consent: BehavioralConsentRecord | None = None,
    metadata: Mapping[str, Any] | None = None,
) -> BehavioralSignal:
    if not USER_BEHAVIOR_NOT_FINANCIAL_TRUTH:
        raise BehavioralLearningError("user_behavior_cannot_be_financial_truth")
    proof_eval = evaluate_user_action_as_outcome_proof(action_type)
    if proof_eval["treated_as_outcome_proof"]:
        raise BehavioralLearningError("user_action_cannot_be_outcome_proof")

    now = datetime.now(UTC)
    return BehavioralSignal(
        signal_id=f"ubl-{user_key}-{int(now.timestamp())}",
        user_key=user_key,
        action_type=action_type,
        asset=asset,
        followed_system=followed_system,
        recorded_at=now,
        is_outcome_truth=False,
        metadata={
            **dict(metadata or {}),
            "explicit_purpose": consent.purpose.value if consent else "unspecified",
            "minimized": True,
        },
    )


def build_behavioral_learning_state(
    *,
    user_key: str,
    purpose: BehavioralLearningPurpose,
    signals: Sequence[BehavioralSignal] = (),
    consent: BehavioralConsentRecord | None = None,
    retention_days: int = 90,
) -> UserBehavioralLearningState:
    if not consent:
        return UserBehavioralLearningState(
            user_key=user_key,
            purpose=purpose,
            consent=None,
            signals=tuple(signals),
            retention_days=retention_days,
            separated_from_objective_outcomes=True,
            anti_manipulation_enabled=True,
            deletion_rights_supported=True,
            eligible_for_adaptation=False,
            abstention_reason="consent_required",
        )

    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    retained = tuple(s for s in signals if s.recorded_at >= cutoff)
    return UserBehavioralLearningState(
        user_key=user_key,
        purpose=purpose,
        consent=consent,
        signals=retained,
        retention_days=retention_days,
        separated_from_objective_outcomes=True,
        anti_manipulation_enabled=True,
        deletion_rights_supported=True,
        eligible_for_adaptation=len(retained) > 0,
        abstention_reason=None if retained else "insufficient_behavioral_evidence",
    )


def delete_user_behavioral_data(
    state: UserBehavioralLearningState,
    *,
    user_key: str,
) -> UserBehavioralLearningState:
    if state.user_key != user_key:
        raise BehavioralLearningError("deletion_rights_user_mismatch")
    return UserBehavioralLearningState(
        user_key=user_key,
        purpose=state.purpose,
        consent=state.consent,
        signals=(),
        retention_days=state.retention_days,
        separated_from_objective_outcomes=True,
        anti_manipulation_enabled=True,
        deletion_rights_supported=True,
        eligible_for_adaptation=False,
        abstention_reason="data_deleted",
    )
