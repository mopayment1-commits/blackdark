"""Source rights metadata preservation (P2) — upstream authority consumed, not replaced."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from blackdark.temporal.event_contract import ProvenanceMetadata

UPSTREAM_PROVENANCE_AUTHORITY = "DATA_GOVERNANCE"


@dataclass(frozen=True, slots=True)
class SourceRightsMetadata:
    """TEMP-AR-0281..0289: preserve rights metadata from upstream provenance."""

    source: str
    permitted_purpose: str | None = None
    historical_use_rights: str | None = None
    retention_rights: str | None = None
    derivative_data_rights: str | None = None
    redistribution_rights: str | None = None
    model_training_rights: str | None = None
    provenance: str | None = None
    contractual_restrictions: str | None = None
    expiry_revocation_conditions: str | None = None
    upstream_authority: str = UPSTREAM_PROVENANCE_AUTHORITY
    rights_metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "permitted_purpose": self.permitted_purpose,
            "historical_use_rights": self.historical_use_rights,
            "retention_rights": self.retention_rights,
            "derivative_data_rights": self.derivative_data_rights,
            "redistribution_rights": self.redistribution_rights,
            "model_training_rights": self.model_training_rights,
            "provenance": self.provenance,
            "contractual_restrictions": self.contractual_restrictions,
            "expiry_revocation_conditions": self.expiry_revocation_conditions,
            "upstream_authority": self.upstream_authority,
            "rights_metadata": dict(self.rights_metadata),
        }


def extract_source_rights(
    provenance: ProvenanceMetadata,
    *,
    rights_metadata: Mapping[str, Any] | None = None,
) -> SourceRightsMetadata:
    """Consume upstream provenance without reinterpreting authority."""
    meta = dict(rights_metadata or {})
    return SourceRightsMetadata(
        source=provenance.source,
        permitted_purpose=meta.get("permitted_purpose"),
        historical_use_rights=meta.get("historical_use_rights"),
        retention_rights=meta.get("retention_rights") or provenance.retention_policy_reference,
        derivative_data_rights=meta.get("derivative_data_rights"),
        redistribution_rights=meta.get("redistribution_rights"),
        model_training_rights=meta.get("model_training_rights"),
        provenance=provenance.source,
        contractual_restrictions=meta.get("contractual_restrictions"),
        expiry_revocation_conditions=meta.get("expiry_revocation_conditions"),
        rights_metadata=meta,
    )


def historical_availability_does_not_imply_permission() -> bool:
    """TEMP-AR-0290 acceptance restriction."""
    return True
