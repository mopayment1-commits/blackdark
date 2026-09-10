"""Canonical capability spine for BLACKDARK local CAP/EC/UX IDs (70-item closure scope)."""

from capability_spine.integration import enrich_opportunity_capabilities
from capability_spine.registry import CAPABILITY_REGISTRY, scoped_capability_ids

__all__ = [
    "CAPABILITY_REGISTRY",
    "enrich_opportunity_capabilities",
    "scoped_capability_ids",
]
