"""Asset Value Ledger — DSR-020, D-17."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from blackdark.data_governance._paths import ASSET_VALUE_LEDGER_PATH, ensure_governance_dirs


def record_asset_value(
    *,
    asset_id: str,
    cost_usd: float | None = None,
    usage_count: int | None = None,
    effectiveness_score: float | None = None,
    uniqueness_score: float | None = None,
    rights_profile_id: str | None = None,
    strategic_reuse: str | None = None,
    review_action: str | None = None,
) -> dict[str, Any]:
    ensure_governance_dirs()
    row = {
        "entry_id": f"avl_{uuid4().hex[:12]}",
        "asset_id": asset_id,
        "cost_usd": cost_usd,
        "usage_count": usage_count,
        "effectiveness_score": effectiveness_score,
        "uniqueness_score": uniqueness_score,
        "rights_profile_id": rights_profile_id,
        "strategic_reuse": strategic_reuse,
        "review_action": review_action,
        "recorded_at": datetime.now(UTC).isoformat(),
    }
    with ASSET_VALUE_LEDGER_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False, default=str) + "\n")
    return row
