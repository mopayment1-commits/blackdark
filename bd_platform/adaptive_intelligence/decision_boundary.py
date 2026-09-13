"""Decision Boundary Contract — spec §25."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class DecisionBoundaryContract:
    variables: list[str] = field(default_factory=list)
    direction: str = "qualitative"
    threshold: str | float | None = None
    uncertainty_band: str | None = None
    persistence: str = "single_observation"
    regime: str = "any"
    validity_window: str = "until_stale"
    conflict_rule: str = "abstain_on_conflict"
    recompute_trigger: str = "freshness_breach_or_regime_change"
    evidence_link: str | None = None
    hysteresis: bool = False
    qualitative_invalidation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def validate(self) -> None:
        if self.threshold is not None and isinstance(self.threshold, (int, float)):
            if not self.evidence_link:
                raise ValueError("numeric_threshold_requires_evidence_link")
        if self.threshold is None and not (self.qualitative_invalidation or "").strip():
            raise ValueError("boundary_requires_threshold_or_qualitative_invalidation")


def build_boundary(
    *,
    variables: list[str],
    calibrated: bool = False,
    threshold: float | None = None,
    qualitative_invalidation: str | None = None,
    evidence_link: str | None = None,
) -> dict[str, Any]:
    if calibrated and threshold is not None:
        contract = DecisionBoundaryContract(
            variables=variables,
            direction="above",
            threshold=threshold,
            uncertainty_band="empirical",
            evidence_link=evidence_link or "calibration_history",
            qualitative_invalidation=None,
        )
    else:
        contract = DecisionBoundaryContract(
            variables=variables,
            direction="qualitative",
            threshold=None,
            qualitative_invalidation=qualitative_invalidation or "stale_data_or_regime_change",
        )
    contract.validate()
    return contract.to_dict()
