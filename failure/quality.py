"""Data quality model separate from availability (ERR-012)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class DataQualityState(StrEnum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    CONFLICTING = "CONFLICTING"
    INSUFFICIENT = "INSUFFICIENT"
    SUSPECT = "SUSPECT"
    UNVERIFIED = "UNVERIFIED"


@dataclass(slots=True)
class DataQuality:
    state: DataQualityState
    source_count: int = 0
    conflict_count: int = 0
    notes: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "source_count": self.source_count,
            "conflict_count": self.conflict_count,
            "notes": self.notes,
        }


def classify_quality(
    *,
    complete: bool = True,
    partial: bool = False,
    conflicting: bool = False,
    insufficient: bool = False,
    suspect: bool = False,
    source_count: int = 0,
) -> DataQuality:
    if conflicting:
        return DataQuality(DataQualityState.CONFLICTING, source_count=source_count, conflict_count=max(1, source_count))
    if insufficient:
        return DataQuality(DataQualityState.INSUFFICIENT, source_count=source_count)
    if suspect:
        return DataQuality(DataQualityState.SUSPECT, source_count=source_count)
    if partial or not complete:
        return DataQuality(DataQualityState.PARTIAL, source_count=source_count)
    if source_count <= 0:
        return DataQuality(DataQualityState.UNVERIFIED, source_count=0)
    return DataQuality(DataQualityState.COMPLETE, source_count=source_count)
