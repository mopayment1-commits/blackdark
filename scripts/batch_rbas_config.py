#!/usr/bin/env python3
"""Batch RBAS configuration — IDs, paths, spine names for batches 01–17."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

from scripts.rbas001_scoping import WF027_UNRESOLVED_LEGACY_IDS as WF027_UNRESOLVED  # noqa: E402


def batch_id_range(batch_num: int) -> range:
    if batch_num < 1 or batch_num > 17:
        raise ValueError(f"batch_num must be 1–17, got {batch_num}")
    if batch_num == 17:
        return range(801, 827)
    start = (batch_num - 1) * 50 + 1
    return range(start, start + 50)


@dataclass(frozen=True)
class BatchRbasConfig:
    batch_num: int

    @property
    def batch_key(self) -> str:
        return f"batch{self.batch_num:02d}"

    @property
    def id_range(self) -> range:
        return batch_id_range(self.batch_num)

    @property
    def id_start(self) -> int:
        return self.id_range.start

    @property
    def id_end(self) -> int:
        return self.id_range.stop - 1

    @property
    def count(self) -> int:
        return len(self.id_range)

    @property
    def spine_name(self) -> str:
        return f"{self.batch_key}_prep"

    @property
    def audit_dir(self) -> Path:
        return ROOT / "institutional_due_diligence_2026" / f"{self.batch_key}_independent_audit"

    @property
    def rtm_path(self) -> Path:
        return ROOT / "docs" / f"BATCH{self.batch_num:02d}_OFFICIAL_RTM_{self.id_start}_{self.id_end}.json"

    @property
    def closure_tag(self) -> str:
        return f"{self.batch_key}-closure-verified"

    def wf027_in_range(self) -> frozenset[int]:
        return WF027_UNRESOLVED & set(self.id_range)


# Per-batch Path B flags — survive generate_batch_scripts regeneration (Run 021).
BATCH_CONCEPTUAL_FLAGS: dict[int, dict[int, str]] = {
    13: {
        648: "BigQuery datashare export not verifiable in local_dev_vm — Path B HEURISTIC",
        649: "826 inventory reserved slot — Path B HEURISTIC",
        650: "826 inventory reserved slot — Path B HEURISTIC",
    },
}
