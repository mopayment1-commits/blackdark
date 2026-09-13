"""BLACKDARK data/storage/tracking governance runtime (v4_v2 / BGS-002)."""

from blackdark.data_governance.runtime import (
    GovernanceViolationError,
    enforce_material_write,
    governance_enforce_enabled,
    intelligence_receipt,
    require_capability_dna,
)

__all__ = [
    "GovernanceViolationError",
    "enforce_material_write",
    "governance_enforce_enabled",
    "intelligence_receipt",
    "require_capability_dna",
]
