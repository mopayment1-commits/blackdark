#!/usr/bin/env python3
"""Compute canonical X/826 progress per CLOSURE-REJECT-02 item 23."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    inv = json.loads((ROOT / "docs/CAPABILITIES_826_INVENTORY.json").read_text(encoding="utf-8"))
    per_id = inv["per_id"]

    pre_batch = {338, 500, 507, 534}
    official_1_100 = set(range(1, 101))
    overlap_batch01 = {55, 56, 59, 60}
    link_eligible = {106, 107, 110, 125}

    production_aligned_ids = {
        int(k) for k, v in per_id.items() if v.get("status") == "PRODUCTION-ALIGNED"
    }

    # Independent builds in 1-100: batch01 (50) + batch02 dedicated (46), overlap not double-counted
    batch01_aligned = {i for i in range(1, 51) if per_id[str(i)]["status"] == "PRODUCTION-ALIGNED"}
    batch02_independent = {
        i
        for i in range(51, 101)
        if i not in overlap_batch01 and per_id[str(i)]["status"] == "PRODUCTION-ALIGNED"
    }

    # Hero batch 03 (201-300) from PR #343 — pending re-evaluation under PRODUCTION-ALIGNED standard
    hero_201_300 = {
        int(k)
        for k, v in per_id.items()
        if 201 <= int(k) <= 300 and v.get("hero_classification") == "PRODUCTION-ALIGNED"
    }

    # Canonical numerator: unique PRODUCTION-ALIGNED minus link-eligible minus overlap double-count adjustment
    # Overlap IDs are in both batch01 count and batch02 list — count once via production_aligned_ids set size
    # Pre-batch 4 may overlap inventory — they're in production_aligned_ids if status says so

    numerator = len(production_aligned_ids) - len(link_eligible & production_aligned_ids)

    out = {
        "computed_at": datetime.now(UTC).isoformat(),
        "canonical_progress": f"{numerator}/826",
        "numerator": numerator,
        "denominator": 826,
        "formula": {
            "a_pre_batch_338_500_507_534": {
                "ids": sorted(pre_batch),
                "in_production_aligned": sorted(pre_batch & production_aligned_ids),
                "note": "Completed before official batch system; included in inventory PRODUCTION-ALIGNED if status matches",
            },
            "b_hero_batch03_pr343_201_300": {
                "hero_production_aligned_count": len(hero_201_300),
                "re_evaluation_required": True,
                "re_evaluation_when": "After batch01+02 institutional closure with owner approval; not before",
                "intersection_with_1_100": sorted(hero_201_300 & official_1_100),
            },
            "c_overlap_batch01": {
                "ids": sorted(overlap_batch01),
                "counted_once_in_numerator": True,
                "independent_batch02_build": False,
            },
            "d_link_eligible_excluded": {
                "ids": sorted(link_eligible),
                "excluded_from_numerator": sorted(link_eligible & production_aligned_ids),
                "status": "LINK-ELIGIBLE — not counted",
            },
        },
        "breakdown": {
            "inventory_production_aligned_total": len(production_aligned_ids),
            "official_batch01_1_50": len(batch01_aligned),
            "official_batch02_independent_51_100_excl_overlap": len(batch02_independent),
            "overlap_batch01_in_1_100": len(overlap_batch01),
        },
        "single_source_of_truth": "docs/CAPABILITIES_826_INVENTORY.json summary must match this numerator",
    }

    path = ROOT / "docs/PROGRESS_826_CANONICAL.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"canonical_progress": out["canonical_progress"], "numerator": numerator}, indent=2))
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
