"""RVM data models — traceability fields per NASA/NIST requirements practice."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

FinalStatus = Literal["PASS", "FAIL", "EXTERNAL_EVIDENCE_REQUIRED"]
RequirementKind = Literal[
    "capability",
    "control",
    "platform",
    "commercial",
    "institutional",
    "governing",
]


@dataclass
class RVMEntry:
    """One traceable requirement row in the governing matrix."""

    id: str
    kind: RequirementKind
    source: str
    requirement: str
    intended_outcome: str
    verification_method: str
    validation_method: str
    required_evidence: list[str] = field(default_factory=list)
    implementation_evidence: list[str] = field(default_factory=list)
    runtime_evidence: list[str] = field(default_factory=list)
    verification_status: str = "PENDING"
    validation_status: str = "PENDING"
    final_status: FinalStatus = "FAIL"
    verification_detail: dict[str, Any] = field(default_factory=dict)
    validation_detail: dict[str, Any] = field(default_factory=dict)
    external_step: str | None = None
    gap_matrix_status: str | None = None
    reconciled: bool = True
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RVMSummary:
    generated_at: str
    governing_baseline_version: str
    total_requirements: int
    pass_count: int
    fail_count: int
    external_count: int
    by_kind: dict[str, dict[str, int]]
    platform_verdict: str
    commercial_ready: bool
    institutional_ready: bool
    conflicts_reconciled: int
    p0_external_remaining: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
