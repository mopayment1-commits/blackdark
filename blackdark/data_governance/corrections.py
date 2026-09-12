"""Historical corrections — DSR-007, D-19."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from blackdark.data_governance._paths import CORRECTIONS_PATH, ensure_governance_dirs


def _utcnow() -> str:
    return datetime.now(UTC).isoformat()


def record_correction(
    *,
    target_asset: str,
    target_record_id: str,
    observed_at: str,
    effective_at: str,
    corrected_at: str | None = None,
    reason: str,
    prior_snapshot_ref: str,
    new_value_summary: dict[str, Any],
) -> dict[str, Any]:
    """Bitemporal correction — never overwrite prior snapshot."""
    ensure_governance_dirs()
    row = {
        "correction_id": f"corr_{uuid4().hex[:12]}",
        "target_asset": target_asset,
        "target_record_id": target_record_id,
        "observed_at": observed_at,
        "effective_at": effective_at,
        "corrected_at": corrected_at or _utcnow(),
        "reason": reason,
        "prior_snapshot_ref": prior_snapshot_ref,
        "new_value_summary": new_value_summary,
        "policy": "append_correction_never_erase",
    }
    with CORRECTIONS_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row
