#!/usr/bin/env python3
"""Generate institutional 25-cap batch manifest for all 826 capabilities."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "docs" / "BATCH_MANIFEST_826_25CAP.json"


def main() -> int:
    from cap646.batch_constants import (
        CAPABILITIES_PER_BATCH,
        TOTAL_CAPABILITIES,
        batch_id_range,
        batch_ids,
        total_batch_count,
    )
    from cap646.catalog import catalog_by_id, is_duplicate, is_external

    batches: list[dict] = []
    for batch_num in range(1, total_batch_count() + 1):
        start, end = batch_id_range(batch_num)
        ids = sorted(batch_ids(batch_num))
        caps = []
        for cid in ids:
            row = catalog_by_id().get(cid, {})
            caps.append(
                {
                    "capability_id": cid,
                    "capability": row.get("capability", ""),
                    "track": row.get("track", ""),
                    "duplicate": is_duplicate(cid),
                    "external": is_external(cid),
                }
            )
        batches.append(
            {
                "batch": f"batch{batch_num:02d}",
                "batch_number": batch_num,
                "id_range": [start, end],
                "capability_count": len(ids),
                "capabilities": caps,
            }
        )

    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "standard": "BLACKDARK Institutional Capability Standard 2026 v6",
        "capabilities_per_batch": CAPABILITIES_PER_BATCH,
        "total_capabilities": TOTAL_CAPABILITIES,
        "total_batches": total_batch_count(),
        "formula": "batch_number = (capability_id - 1) // 25 + 1",
        "batches": batches,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {OUT} — {total_batch_count()} batches × {CAPABILITIES_PER_BATCH} cap (last batch may be smaller)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
