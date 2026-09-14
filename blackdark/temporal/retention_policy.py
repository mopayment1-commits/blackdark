"""Retention policy and tiered storage controls (P2)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Mapping


class StorageTier(str, Enum):
    """TEMP-AR-0192..0194."""

    HOT = "hot"
    WARM = "warm"
    COLD = "cold"


@dataclass(frozen=True, slots=True)
class RetentionPolicyDescriptor:
    """TEMP-AR-0195..0202 lifecycle controls."""

    tier: StorageTier
    compression: bool
    partitioning: bool
    deduplication: bool
    lifecycle_policies: bool
    rights_aware_retention: bool
    deterministic_reconstruction: bool
    reproducible_retrieval: bool
    delete_raw_for_low_learning_value: bool = False

    def to_metadata(self) -> dict[str, Any]:
        return {
            "tier": self.tier.value,
            "compression": self.compression,
            "partitioning": self.partitioning,
            "deduplication": self.deduplication,
            "lifecycle_policies": self.lifecycle_policies,
            "rights_aware_retention": self.rights_aware_retention,
            "deterministic_reconstruction": self.deterministic_reconstruction,
            "reproducible_retrieval": self.reproducible_retrieval,
            "delete_raw_for_low_learning_value": self.delete_raw_for_low_learning_value,
        }


def classify_storage_tier(
    *,
    access_frequency: str = "recent",
    is_raw_archive: bool = False,
) -> StorageTier:
    if is_raw_archive:
        return StorageTier.COLD
    if access_frequency in ("high", "live", "recent"):
        return StorageTier.HOT
    if access_frequency in ("normalized", "reusable", "frequent_replay"):
        return StorageTier.WARM
    return StorageTier.COLD


def build_retention_descriptor(
    tier: StorageTier,
    *,
    rights_metadata: Mapping[str, Any] | None = None,
) -> RetentionPolicyDescriptor:
    rights = dict(rights_metadata or {})
    return RetentionPolicyDescriptor(
        tier=tier,
        compression=tier != StorageTier.HOT,
        partitioning=True,
        deduplication=True,
        lifecycle_policies=True,
        rights_aware_retention=bool(rights.get("retention_rights")),
        deterministic_reconstruction=True,
        reproducible_retrieval=True,
        delete_raw_for_low_learning_value=False,
    )
