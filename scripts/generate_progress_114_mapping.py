#!/usr/bin/env python3
"""Generate explicit 114/826 ID mapping for CLOSURE-REJECT-03 item 16."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    inv = json.loads((ROOT / "docs/CAPABILITIES_826_INVENTORY.json").read_text(encoding="utf-8"))
    per_id = inv["per_id"]
    link_eligible = {106, 107, 110, 125}

    included = []
    excluded = []
    for k, v in per_id.items():
        cid = int(k)
        if v.get("status") == "PRODUCTION-ALIGNED":
            if cid in link_eligible:
                excluded.append({"id": cid, "reason": "LINK-ELIGIBLE", "status": v["status"]})
            else:
                included.append({"id": cid, "status": v["status"], "official_batch": v.get("official_batch")})

    hero_201_300_pa = [
        int(k)
        for k, v in per_id.items()
        if 201 <= int(k) <= 300 and v.get("status") == "PRODUCTION-ALIGNED"
    ]

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "numerator": len(included),
        "denominator": 826,
        "canonical_progress": f"{len(included)}/826",
        "included_ids": sorted([x["id"] for x in included]),
        "excluded_link_eligible": excluded,
        "hero_batch_03_201_300_production_aligned": {
            "ids": hero_201_300_pa,
            "count": len(hero_201_300_pa),
            "counted_in_114": False,
            "open_risk": "Requires re-evaluation under PRODUCTION-ALIGNED standard before counting",
        },
        "overlap_batch01_ids": [55, 56, 59, 60],
        "overlap_note": "Counted once in included_ids (batch01 spine), not double-counted",
    }
    path = ROOT / "docs/PROGRESS_114_ID_MAPPING.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    assert len(included) == 114, f"expected 114 got {len(included)}"
    print(json.dumps({"canonical_progress": out["canonical_progress"], "count": len(included)}, indent=2))


if __name__ == "__main__":
    main()
