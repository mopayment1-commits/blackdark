"""Multi-dimensional Trust Status — spec §11 (AIE-007)."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class TrustDimensionVector:
    assurance: str = "experimental"
    freshness: str = "near_live"
    availability: str = "healthy"
    coverage: str = "partial"
    methodology_maturity: str = "under_review"
    evidence_class: str = "forward_shadow"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def compact_label(self) -> str:
        return f"{self.assurance} · {self.freshness} · {self.coverage}"

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> TrustDimensionVector:
        return cls(
            assurance=str(payload.get("assurance") or "experimental"),
            freshness=str(payload.get("freshness") or payload.get("freshness_band") or "near_live"),
            availability=str(payload.get("availability") or "healthy"),
            coverage=str(payload.get("coverage") or "partial"),
            methodology_maturity=str(payload.get("methodology_maturity") or "under_review"),
            evidence_class=str(payload.get("evidence_class") or "forward_shadow"),
        )
