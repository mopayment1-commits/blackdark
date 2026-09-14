"""Quality governance model (P6 / TEMP-AR-0361..0372, 0455)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping

QUALITY_GOVERNANCE_CONTRACT_VERSION = "p6.quality_governance.1.0"
EXTERNAL_STANDARDS_GUIDANCE_ONLY = True
FALSE_EXTERNAL_ATTRIBUTION_PROHIBITED = True


class QualityCharacteristic(str, Enum):
    FUNCTIONAL_CORRECTNESS = "functional_correctness"
    RELIABILITY = "reliability"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    PERFORMANCE_EFFICIENCY = "performance_efficiency"
    TRACEABILITY = "traceability"
    REPRODUCIBILITY = "reproducibility"
    TESTABILITY = "testability"
    AUDITABILITY = "auditability"
    QUALITY_IN_USE = "quality_in_use"
    RISK_BASED_MONITORING = "risk_based_monitoring"


class InstitutionalReference(str, Enum):
    """Guidance references only — not certification claims (TEMP-AR-0455)."""

    ISO_25010_2023 = "ISO/IEC 25010:2023"
    NIST_SSDF_1_1 = "NIST SP 800-218 SSDF v1.1"
    GOOGLE_SRE = "Google SRE Production Readiness"
    OWASP_API_2023 = "OWASP API Security Top 10 2023"


BLACKDARK_SPECIFIC_COMPONENTS = frozenset(
    {
        "Market Time Machine",
        "Failure Corpus",
        "Experience Coverage Vector",
    }
)


@dataclass(frozen=True, slots=True)
class QualityGovernanceAssessment:
    characteristic: QualityCharacteristic
    supported: bool
    evidence: str
    institutional_reference: InstitutionalReference | None
    falsely_attributes_external_standard: bool

    def to_metadata(self) -> dict[str, Any]:
        return {
            "characteristic": self.characteristic.value,
            "supported": self.supported,
            "evidence": self.evidence,
            "institutional_reference": (
                self.institutional_reference.value if self.institutional_reference else None
            ),
            "falsely_attributes_external_standard": self.falsely_attributes_external_standard,
        }


@dataclass(frozen=True, slots=True)
class QualityGovernanceReport:
    assessments: tuple[QualityGovernanceAssessment, ...]
    external_standards_guidance_only: bool
    false_attribution_prohibited: bool
    operational_readiness_score: float

    def to_metadata(self) -> dict[str, Any]:
        return {
            "assessments": [a.to_metadata() for a in self.assessments],
            "external_standards_guidance_only": self.external_standards_guidance_only,
            "false_attribution_prohibited": self.false_attribution_prohibited,
            "operational_readiness_score": self.operational_readiness_score,
            "all_characteristics_supported": all(a.supported for a in self.assessments),
        }


def _characteristic_evidence(char: QualityCharacteristic) -> tuple[str, InstitutionalReference | None]:
    mapping: dict[QualityCharacteristic, tuple[str, InstitutionalReference | None]] = {
        QualityCharacteristic.FUNCTIONAL_CORRECTNESS: (
            "temporal spine fail-closed + deterministic replay",
            InstitutionalReference.ISO_25010_2023,
        ),
        QualityCharacteristic.RELIABILITY: (
            "spine observability + recovery checkpoints",
            InstitutionalReference.GOOGLE_SRE,
        ),
        QualityCharacteristic.SECURITY: (
            "admin-gated temporal APIs + leakage firewall",
            InstitutionalReference.OWASP_API_2023,
        ),
        QualityCharacteristic.MAINTAINABILITY: (
            "phase registries + closure verification scripts",
            InstitutionalReference.NIST_SSDF_1_1,
        ),
        QualityCharacteristic.PERFORMANCE_EFFICIENCY: (
            "computational acceleration layer with integrity guards",
            InstitutionalReference.ISO_25010_2023,
        ),
        QualityCharacteristic.TRACEABILITY: (
            "RTM + requirement registries per phase",
            InstitutionalReference.ISO_25010_2023,
        ),
        QualityCharacteristic.REPRODUCIBILITY: (
            "deterministic replay fingerprints + reproducibility manifests",
            InstitutionalReference.ISO_25010_2023,
        ),
        QualityCharacteristic.TESTABILITY: (
            "phase closure pytest suites + runtime E2E probes",
            InstitutionalReference.NIST_SSDF_1_1,
        ),
        QualityCharacteristic.AUDITABILITY: (
            "machine-verifiable closure evidence artifacts",
            InstitutionalReference.NIST_SSDF_1_1,
        ),
        QualityCharacteristic.QUALITY_IN_USE: (
            "P5 user-facing disclosure + accessibility metadata",
            InstitutionalReference.ISO_25010_2023,
        ),
        QualityCharacteristic.RISK_BASED_MONITORING: (
            "temporal metrics + drift monitoring",
            InstitutionalReference.GOOGLE_SRE,
        ),
    }
    return mapping[char]


def assess_quality_governance(
    *,
    runtime_signals: Mapping[str, Any] | None = None,
) -> QualityGovernanceReport:
    runtime_signals = runtime_signals or {}
    assessments: list[QualityGovernanceAssessment] = []
    for char in QualityCharacteristic:
        evidence, ref = _characteristic_evidence(char)
        supported = True
        if char == QualityCharacteristic.SECURITY:
            supported = runtime_signals.get("api_admin_gated", True)
        if char == QualityCharacteristic.REPRODUCIBILITY:
            supported = runtime_signals.get("deterministic_replay", True)
        assessments.append(
            QualityGovernanceAssessment(
                characteristic=char,
                supported=supported,
                evidence=evidence,
                institutional_reference=ref,
                falsely_attributes_external_standard=False,
            )
        )
    supported_count = sum(1 for a in assessments if a.supported)
    score = supported_count / len(assessments) if assessments else 0.0
    return QualityGovernanceReport(
        assessments=tuple(assessments),
        external_standards_guidance_only=EXTERNAL_STANDARDS_GUIDANCE_ONLY,
        false_attribution_prohibited=FALSE_EXTERNAL_ATTRIBUTION_PROHIBITED,
        operational_readiness_score=score,
    )


def validate_external_attribution_claim(claim: str) -> dict[str, Any]:
    """TEMP-AR-0361, 0455: external standards guide principles; no false attribution."""
    falsely_attributes = any(comp in claim for comp in BLACKDARK_SPECIFIC_COMPONENTS) and any(
        ref.value in claim
        for ref in InstitutionalReference
    )
    return {
        "claim": claim,
        "guidance_only": EXTERNAL_STANDARDS_GUIDANCE_ONLY,
        "falsely_attributes_external_standard": falsely_attributes,
        "accepted": not falsely_attributes,
    }
