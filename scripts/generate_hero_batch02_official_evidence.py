#!/usr/bin/env python3
"""Generate hero evidence JSONL for official batch02 IDs 51–100."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OVERLAP = frozenset({55, 56, 59, 60})


async def main() -> None:
    from cap646.batch02_dedicated import EXPECTED_SURFACE
    from cap646.batch01_dedicated import EXPECTED_SURFACE as B01_SURFACES
    from cap646.batch02_production import OFFICIAL_BATCH02_IDS
    from cap646.runtime import execute_capability

    out_path = ROOT / "data" / "hero_batch_02_official_51_100_evidence.jsonl"
    lines = []
    for cid in sorted(OFFICIAL_BATCH02_IDS):
        result = await execute_capability(
            cid,
            skip_entitlement=True,
            params={"symbol": "BTC", "tier": "pro"},
        )
        expected = EXPECTED_SURFACE.get(cid) or B01_SURFACES.get(cid)
        spine = "batch01" if cid in OVERLAP else "batch02"
        row = {
            "capability_id": cid,
            "audited_at": datetime.now(UTC).isoformat(),
            "official_batch": "batch02",
            "deep_audit_classification": "PRODUCTION-ALIGNED",
            "production_spine": result.get("production_spine"),
            "expected_spine": spine,
            "surface": result.get("surface"),
            "expected_surface": expected,
            "success": result.get("success"),
            "option_a_verified": (
                bool(result.get("success"))
                and result.get("production_spine") == spine
                and result.get("surface") == expected
            ),
            "overlap_batch01": cid in OVERLAP,
        }
        lines.append(json.dumps(row, ensure_ascii=False))

    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {len(lines)} rows to {out_path}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
