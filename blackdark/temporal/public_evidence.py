"""Public evidence disclosure layer (P5 / TEMP-AR-0262..0280)."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Sequence

from blackdark.temporal.evidence_class import TemporalEvidenceClass, assert_no_automatic_promotion
from blackdark.temporal.evidence_provenance import EvidenceProvenanceLedger, EvidenceRecord
from blackdark.temporal.dependence_aware_sampling import DependenceAwareSampler

PUBLIC_EVIDENCE_CONTRACT_VERSION = "p5.public_evidence.1.0"
PUBLIC_LEDGER_MATURITY_REQUIRED = True


@dataclass(frozen=True, slots=True)
class PublicEvidenceDisclosure:
    """Mandatory disclosure envelope for every material public claim."""

    claim_id: str
    evidence_class: str
    date_range_start: datetime | None
    date_range_end: datetime | None
    sample_size: int
    effective_independent_count: float
    regime_distribution: Mapping[str, float]
    asset_universe: tuple[str, ...]
    evaluation_horizon: str | None
    model_version: str | None
    abstention_count: int
    methodology: str
    uncertainty_statement: str
    exclusions: tuple[str, ...]
    limitations: tuple[str, ...]
    freshness_timestamp: datetime
    confidence_summary: str | None
    provenance_reference: str
    maturity_sufficient: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "evidence_class": self.evidence_class,
            "date_range_start": self.date_range_start.isoformat() if self.date_range_start else None,
            "date_range_end": self.date_range_end.isoformat() if self.date_range_end else None,
            "sample_size": self.sample_size,
            "effective_independent_count": self.effective_independent_count,
            "regime_distribution": dict(self.regime_distribution),
            "asset_universe": list(self.asset_universe),
            "evaluation_horizon": self.evaluation_horizon,
            "model_version": self.model_version,
            "abstention_count": self.abstention_count,
            "methodology": self.methodology,
            "uncertainty_statement": self.uncertainty_statement,
            "exclusions": list(self.exclusions),
            "limitations": list(self.limitations),
            "freshness_timestamp": self.freshness_timestamp.isoformat(),
            "confidence_summary": self.confidence_summary,
            "provenance_reference": self.provenance_reference,
            "maturity_sufficient": self.maturity_sufficient,
        }


@dataclass(frozen=True, slots=True)
class PublicEvidenceControls:
    """Anti-bias controls for public evidence publication."""

    cherry_picking_blocked: bool
    survivorship_bias_disclosed: bool
    retroactive_deletion_blocked: bool
    selective_date_window_blocked: bool
    mixed_evidence_classes_blocked: bool
    violations: tuple[str, ...]

    def to_metadata(self) -> dict[str, Any]:
        return {
            "cherry_picking_blocked": self.cherry_picking_blocked,
            "survivorship_bias_disclosed": self.survivorship_bias_disclosed,
            "retroactive_deletion_blocked": self.retroactive_deletion_blocked,
            "selective_date_window_blocked": self.selective_date_window_blocked,
            "mixed_evidence_classes_blocked": self.mixed_evidence_classes_blocked,
            "violations": list(self.violations),
        }


def _parse_timestamp(value: Any) -> datetime | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    from blackdark.temporal.truth import parse_temporal_instant

    try:
        return parse_temporal_instant(str(value))
    except (TypeError, ValueError):
        return None


def build_public_disclosure_from_ledger(
    *,
    claim_id: str,
    ledger: EvidenceProvenanceLedger,
    sampler: DependenceAwareSampler | None = None,
    regime_distribution: Mapping[str, float] | None = None,
    asset_universe: Sequence[str] = (),
    evaluation_horizon: str | None = None,
    abstention_count: int = 0,
    maturity_sufficient: bool = True,
    freshness_timestamp: datetime | None = None,
) -> PublicEvidenceDisclosure:
    records = ledger.list_records()
    if not records:
        raise ValueError("cannot publish public claim without evidence records")

    evidence_classes = {r.evidence_class for r in records}
    if len(evidence_classes) > 1:
        raise ValueError("mixed evidence classes in single public claim forbidden")

    primary = records[0]
    timestamps = [_parse_timestamp(r.timestamps.get("recorded_at")) for r in records]
    valid_ts = [t for t in timestamps if t is not None]
    date_start = min(valid_ts) if valid_ts else None
    date_end = max(valid_ts) if valid_ts else None

    effective = sampler.total_effective_independent() if sampler else float(len(records))
    regimes = dict(regime_distribution or {})
    if not regimes:
        regimes = {"unspecified": 1.0}

    return PublicEvidenceDisclosure(
        claim_id=claim_id,
        evidence_class=primary.evidence_class,
        date_range_start=date_start,
        date_range_end=date_end,
        sample_size=len(records),
        effective_independent_count=effective,
        regime_distribution=regimes,
        asset_universe=tuple(asset_universe),
        evaluation_horizon=evaluation_horizon,
        model_version=(primary.versions or {}).get("model_version"),
        abstention_count=abstention_count,
        methodology=primary.methodology,
        uncertainty_statement="Outcomes carry residual uncertainty; see limitations.",
        exclusions=tuple(primary.limitations),
        limitations=tuple(primary.limitations) + ("Public view is read-only; evidence class cannot be upgraded here.",),
        freshness_timestamp=freshness_timestamp or datetime.now().astimezone(),
        confidence_summary=(primary.quality_state or {}).get("label_confidence"),
        provenance_reference=str((primary.source_provenance or {}).get("provenance_reference", primary.evidence_id)),
        maturity_sufficient=maturity_sufficient,
    )


def validate_public_evidence_controls(
    *,
    records: Sequence[EvidenceRecord],
    claimed_date_start: datetime | None,
    claimed_date_end: datetime | None,
    deleted_evidence_ids: Sequence[str] = (),
) -> PublicEvidenceControls:
    violations: list[str] = []
    evidence_classes = {r.evidence_class for r in records}
    if len(evidence_classes) > 1:
        violations.append("mixed_evidence_classes")

    if deleted_evidence_ids:
        violations.append("retroactive_deletion_attempt")

    recorded_starts = [_parse_timestamp(r.timestamps.get("recorded_at")) for r in records]
    recorded_ends = recorded_starts
    actual_start = min((t for t in recorded_starts if t), default=None)
    actual_end = max((t for t in recorded_ends if t), default=None)
    if claimed_date_start and actual_start and claimed_date_start > actual_start:
        violations.append("selective_date_window_start")
    if claimed_date_end and actual_end and claimed_date_end < actual_end:
        violations.append("selective_date_window_end")

    cherry_picking = any("cherry" in lim.lower() for r in records for lim in r.limitations)
    if cherry_picking:
        violations.append("cherry_picking")

    return PublicEvidenceControls(
        cherry_picking_blocked="cherry_picking" not in violations,
        survivorship_bias_disclosed=True,
        retroactive_deletion_blocked="retroactive_deletion_attempt" not in violations,
        selective_date_window_blocked=(
            "selective_date_window_start" not in violations
            and "selective_date_window_end" not in violations
        ),
        mixed_evidence_classes_blocked="mixed_evidence_classes" not in violations,
        violations=tuple(violations),
    )


def assert_public_claim_maturity(*, maturity_sufficient: bool, evidence_mature: bool) -> None:
    """TEMP-AR-0262: do not market public ledger until evidence mature."""
    if PUBLIC_LEDGER_MATURITY_REQUIRED and not (maturity_sufficient and evidence_mature):
        raise ValueError("public_ledger_evidence_not_mature")


def public_surface_cannot_reclassify(from_class: str, to_class: str) -> None:
    """Public surface is read-only — cannot promote evidence class."""
    assert_no_automatic_promotion(from_class, to_class)
    if from_class != to_class and to_class in {
        TemporalEvidenceClass.VERIFIED_PRODUCTION.value,
        TemporalEvidenceClass.INDEPENDENTLY_VERIFIED.value,
    }:
        raise ValueError("public_surface_cannot_reclassify_evidence")
