"""
Canonical Data Layer + Asset Metadata — core infrastructure (#16 + #29).

Not a user-facing feature. Stable canonical IDs and normalized reference data
for all downstream modules (execution, rankings, on-chain, ingestion).
"""

from blackdark.canonical.layer import CanonicalDataLayer, get_canonical_layer
from blackdark.canonical.resolver import resolve_asset
from blackdark.canonical.schema import CanonicalAsset, ResolveResult

__all__ = [
    "CanonicalAsset",
    "CanonicalDataLayer",
    "ResolveResult",
    "get_canonical_layer",
    "resolve_asset",
]
