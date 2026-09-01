#!/usr/bin/env python3
"""Audit execution paths for official batch IDs 1–100."""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BATCH01_FREE_TIER = frozenset({1, 2, 3, 4, 10, 21, 38, 39, 45})
BATCH02_OVERLAP = frozenset({55, 56, 59, 60})


def _classify_path(capability_id: int) -> dict:
    from cap646.batch01_dedicated import BATCH01_DEDICATED_IDS
    from cap646.batch02_dedicated import BATCH02_DEDICATED_IDS

    if capability_id <= 50:
        if capability_id in BATCH01_DEDICATED_IDS:
            return {
                "path": "batch01_dedicated",
                "module": "cap646.batch01_dedicated.execute",
                "official_spine": "cap646.batch01_production",
                "non_standard": False,
            }
        if capability_id in BATCH01_FREE_TIER:
            return {
                "path": "batch01_free_tier",
                "module": "bd_platform.free_tier_capabilities.execute_free_tier_capability",
                "official_spine": "cap646.batch01_production",
                "non_standard": True,
                "justification": "Declared in batch01_production._BATCH01_FREE_TIER; stamped batch01 spine",
            }
        return {
            "path": "batch01_handler_group",
            "module": "cap646.batch01_production.execute -> handler groups",
            "official_spine": "cap646.batch01_production",
            "non_standard": False,
        }

    if capability_id in BATCH02_OVERLAP:
        return {
            "path": "overlap_batch01_legacy",
            "module": "cap646.batch01_production (LEGACY_BATCH01_EXTENSION_IDS)",
            "official_spine": "cap646.batch01_production",
            "non_standard": True,
            "classification": "OVERLAP_BATCH01",
            "justification": "Listed in batch02 scope but no batch02 handler; routed via batch01 legacy extension",
        }

    if capability_id in BATCH02_DEDICATED_IDS:
        return {
            "path": "batch02_dedicated",
            "module": "cap646.batch02_dedicated.execute",
            "official_spine": "cap646.batch02_production",
            "non_standard": False,
        }

    return {
        "path": "unmapped",
        "module": None,
        "official_spine": None,
        "non_standard": True,
    }


async def main() -> None:
    rows = []
    non_standard = []
    for cid in range(1, 101):
        info = _classify_path(cid)
        row = {"capability_id": cid, **info}
        rows.append(row)
        if info.get("non_standard"):
            non_standard.append(row)

    out = {
        "audited_at": datetime.now(UTC).isoformat(),
        "scope": "IDs 1–100",
        "total": 100,
        "non_standard_count": len(non_standard),
        "non_standard_ids": [r["capability_id"] for r in non_standard],
        "paths": rows,
    }
    path = ROOT / "docs/EXECUTION_PATH_AUDIT_1_100.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"non_standard_count": len(non_standard), "ids": out["non_standard_ids"]}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    asyncio.run(main())
