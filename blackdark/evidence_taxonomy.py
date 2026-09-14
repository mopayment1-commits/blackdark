"""Canonical BLACKDARK evidence taxonomy — single owner for CAP646 + TEAS.

CAP646 exposes a 4-class product surface; TEAS temporal spine uses a 6-class
granular model. This module owns class registries, deterministic bidirectional
mapping, and promotion rules for both domains. Cross-domain promotion requires
an explicit governing gate and is fail-closed by default.
"""

from __future__ import annotations

from enum import Enum
from typing import Final, Literal

EVIDENCE_TAXONOMY_VERSION: Final[str] = "1.0.0"

EvidenceDomain = Literal["cap646", "temporal"]


class TemporalEvidenceClass(str, Enum):
    """TEAS temporal spine evidence classes (TEMP-AR-0138..0143)."""

    HISTORICAL_BACKTEST = "HISTORICAL_BACKTEST"
    HISTORICAL_REPLAY = "HISTORICAL_REPLAY"
    SIMULATED = "SIMULATED"
    FORWARD_SHADOW = "FORWARD_SHADOW"
    VERIFIED_PRODUCTION = "VERIFIED_PRODUCTION"
    INDEPENDENTLY_VERIFIED = "INDEPENDENTLY_VERIFIED"


CAP646_EVIDENCE_CLASSES: tuple[str, ...] = (
    "BACKTESTED",
    "SIMULATED",
    "SHADOW_LIVE_FORWARD",
    "PRODUCTION_VERIFIED",
)

CANONICAL_TEMPORAL_EVIDENCE_CLASSES: frozenset[str] = frozenset(c.value for c in TemporalEvidenceClass)
CANONICAL_CAP646_EVIDENCE_CLASSES: frozenset[str] = frozenset(CAP646_EVIDENCE_CLASSES)

# Deterministic CAP646 → temporal projection (default; replay hint refines BACKTESTED).
_CAP646_TO_TEMPORAL_DEFAULT: dict[str, str] = {
    "BACKTESTED": TemporalEvidenceClass.HISTORICAL_BACKTEST.value,
    "SIMULATED": TemporalEvidenceClass.SIMULATED.value,
    "SHADOW_LIVE_FORWARD": TemporalEvidenceClass.FORWARD_SHADOW.value,
    "PRODUCTION_VERIFIED": TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
}

_CAP646_TO_TEMPORAL_REPLAY: dict[str, str] = {
    **_CAP646_TO_TEMPORAL_DEFAULT,
    "BACKTESTED": TemporalEvidenceClass.HISTORICAL_REPLAY.value,
}

# Deterministic temporal → CAP646 projection (lossy for TEAS-only granularity).
_TEMPORAL_TO_CAP646: dict[str, str] = {
    TemporalEvidenceClass.HISTORICAL_BACKTEST.value: "BACKTESTED",
    TemporalEvidenceClass.HISTORICAL_REPLAY.value: "BACKTESTED",
    TemporalEvidenceClass.SIMULATED.value: "SIMULATED",
    TemporalEvidenceClass.FORWARD_SHADOW.value: "SHADOW_LIVE_FORWARD",
    TemporalEvidenceClass.VERIFIED_PRODUCTION.value: "PRODUCTION_VERIFIED",
    TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value: "PRODUCTION_VERIFIED",
}

# CAP646 whitelist promotion (product surfaces).
_CAP646_PROMOTION_ALLOWED: dict[str, frozenset[str]] = {
    "BACKTESTED": frozenset({"BACKTESTED"}),
    "SIMULATED": frozenset({"SIMULATED"}),
    "SHADOW_LIVE_FORWARD": frozenset({"SHADOW_LIVE_FORWARD", "PRODUCTION_VERIFIED"}),
    "PRODUCTION_VERIFIED": frozenset({"PRODUCTION_VERIFIED"}),
}

# TEAS forbidden transitions (TEMP-AR-0151..0153).
FORBIDDEN_TEMPORAL_EVIDENCE_CLASS_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        (TemporalEvidenceClass.HISTORICAL_REPLAY.value, TemporalEvidenceClass.FORWARD_SHADOW.value),
        (TemporalEvidenceClass.HISTORICAL_BACKTEST.value, TemporalEvidenceClass.FORWARD_SHADOW.value),
        (TemporalEvidenceClass.SIMULATED.value, TemporalEvidenceClass.FORWARD_SHADOW.value),
        (TemporalEvidenceClass.FORWARD_SHADOW.value, TemporalEvidenceClass.VERIFIED_PRODUCTION.value),
        (TemporalEvidenceClass.HISTORICAL_REPLAY.value, TemporalEvidenceClass.VERIFIED_PRODUCTION.value),
        (TemporalEvidenceClass.VERIFIED_PRODUCTION.value, TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value),
        (TemporalEvidenceClass.HISTORICAL_REPLAY.value, TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value),
    }
)

_CROSS_DOMAIN_GOVERNING_GATES: frozenset[str] = frozenset(
    {
        "EXTERNAL_ASSURANCE_VERIFIED",
        "INSTITUTIONAL_PROMOTION_REVIEW",
        "TEMPORAL_EVIDENCE_LEDGER_ADMISSION",
    }
)


def validate_cap646_evidence_class(value: str) -> None:
    if value not in CANONICAL_CAP646_EVIDENCE_CLASSES:
        raise ValueError(f"unknown cap646 evidence class: {value}")


def validate_temporal_evidence_class(value: str) -> None:
    if value not in CANONICAL_TEMPORAL_EVIDENCE_CLASSES:
        raise ValueError(f"unknown temporal evidence class: {value}")


def map_cap646_to_temporal(value: str, *, replay_hint: bool = False) -> str:
    """Project a CAP646 class into the temporal namespace (deterministic)."""
    validate_cap646_evidence_class(value)
    table = _CAP646_TO_TEMPORAL_REPLAY if replay_hint else _CAP646_TO_TEMPORAL_DEFAULT
    return table[value]


def map_temporal_to_cap646(value: str) -> str:
    """Project a temporal class into the CAP646 namespace (lossy, deterministic)."""
    validate_temporal_evidence_class(value)
    return _TEMPORAL_TO_CAP646[value]


def cap646_independently_verified_projection(value: str) -> bool:
    """Whether temporal→cap646 projection collapses an independently verified class."""
    validate_temporal_evidence_class(value)
    return value == TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value


def can_promote_cap646_evidence_class(from_class: str, to_class: str) -> bool:
    validate_cap646_evidence_class(from_class)
    validate_cap646_evidence_class(to_class)
    return to_class in _CAP646_PROMOTION_ALLOWED.get(from_class, frozenset())


def assert_cap646_promotion_allowed(current: str, target: str) -> None:
    if not can_promote_cap646_evidence_class(current, target):
        raise ValueError(f"evidence_promotion_denied:{current}->{target}")


def can_promote_temporal_evidence_class(from_class: str, to_class: str) -> bool:
    """TEMP-AR-0144: no automatic promotion across forbidden transitions."""
    validate_temporal_evidence_class(from_class)
    validate_temporal_evidence_class(to_class)
    if from_class == to_class:
        return True
    return (from_class, to_class) not in FORBIDDEN_TEMPORAL_EVIDENCE_CLASS_TRANSITIONS


def assert_no_automatic_temporal_promotion(from_class: str, to_class: str) -> None:
    if from_class != to_class and not can_promote_temporal_evidence_class(from_class, to_class):
        raise ValueError(
            f"automatic evidence class promotion forbidden: {from_class} -> {to_class}"
        )


def assert_governed_cross_domain_promotion(
    from_domain: EvidenceDomain,
    from_class: str,
    to_domain: EvidenceDomain,
    to_class: str,
    *,
    governing_gate: str | None,
) -> None:
    """Fail-closed unless an explicit institutional gate authorizes cross-domain promotion."""
    if from_domain == to_domain:
        if from_domain == "cap646":
            assert_cap646_promotion_allowed(from_class, to_class)
        else:
            assert_no_automatic_temporal_promotion(from_class, to_class)
        return

    if not governing_gate or governing_gate not in _CROSS_DOMAIN_GOVERNING_GATES:
        raise ValueError(
            "cross_domain_evidence_promotion_denied:"
            f"{from_domain}:{from_class}->{to_domain}:{to_class}"
        )

    if from_domain == "cap646":
        validate_cap646_evidence_class(from_class)
        projected_from = map_cap646_to_temporal(from_class)
    else:
        validate_temporal_evidence_class(from_class)
        projected_from = from_class

    if to_domain == "cap646":
        validate_cap646_evidence_class(to_class)
        projected_to = map_cap646_to_temporal(to_class)
    else:
        validate_temporal_evidence_class(to_class)
        projected_to = to_class

    assert_no_automatic_temporal_promotion(projected_from, projected_to)


def taxonomy_registry() -> dict[str, object]:
    """Machine-readable registry for audits and closure evidence."""
    return {
        "version": EVIDENCE_TAXONOMY_VERSION,
        "canonical_owner": "blackdark/evidence_taxonomy.py",
        "cap646_classes": list(CAP646_EVIDENCE_CLASSES),
        "temporal_classes": sorted(CANONICAL_TEMPORAL_EVIDENCE_CLASSES),
        "cap646_to_temporal_default": dict(_CAP646_TO_TEMPORAL_DEFAULT),
        "cap646_to_temporal_replay": dict(_CAP646_TO_TEMPORAL_REPLAY),
        "temporal_to_cap646": dict(_TEMPORAL_TO_CAP646),
        "cross_domain_governing_gates": sorted(_CROSS_DOMAIN_GOVERNING_GATES),
    }
