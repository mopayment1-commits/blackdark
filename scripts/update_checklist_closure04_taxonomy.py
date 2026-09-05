#!/usr/bin/env python3
"""Add OVERLAP / LINK-ELIGIBLE / CLASSIFICATION columns to capabilities_checklist.xlsx for IDs 1-100."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
XLSX = ROOT / "capabilities_checklist.xlsx"


def main() -> int:
    try:
        import pandas as pd
    except ImportError:
        print("pandas required", file=sys.stderr)
        return 1

    dedup = json.loads((ROOT / "docs/CAP_DEDUP_AUDIT_1_100.json").read_text(encoding="utf-8"))
    taxonomy = json.loads((ROOT / "docs/REUSED_LINK_TAXONOMY.json").read_text(encoding="utf-8"))
    overlap = set(taxonomy.get("OVERLAP_BATCH01", {}).get("ids", [55, 56, 59, 60]))

    df = pd.read_excel(XLSX)
    if "classification_1_100" not in df.columns:
        df["classification_1_100"] = ""
    if "overlap_batch01" not in df.columns:
        df["overlap_batch01"] = ""
    if "link_eligible" not in df.columns:
        df["link_eligible"] = ""

    per_id = dedup.get("per_id", {})
    for idx, row in df.iterrows():
        cid = int(row.get("id") or row.get("ID") or 0)
        if not (1 <= cid <= 100):
            continue
        entry = per_id.get(str(cid)) or per_id.get(cid) or {}
        df.at[idx, "classification_1_100"] = entry.get("final_classification", "PRODUCTION-ALIGNED")
        df.at[idx, "overlap_batch01"] = "YES" if cid in overlap else "NO"
        df.at[idx, "link_eligible"] = "YES" if str(cid) in taxonomy.get("registered_pairs", {}) else "NO"

    df.to_excel(XLSX, index=False)
    print(f"Updated {XLSX} with classification_1_100, overlap_batch01, link_eligible")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
