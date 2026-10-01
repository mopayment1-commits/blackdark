#!/usr/bin/env python3
"""Generate BATCH03_INVENTORY.json and BATCH03_RTM.json from live RTM audit."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> None:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/audit_official_batch03_rtm.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=600,
    )
    rtm_path = ROOT / "docs/BATCH03_OFFICIAL_RTM_101_150.json"
    if not rtm_path.is_file():
        raise SystemExit(f"RTM audit did not produce {rtm_path}\n{proc.stderr}")
    rtm = json.loads(rtm_path.read_text(encoding="utf-8"))

    from cap646.catalog import catalog_by_id

    catalog = catalog_by_id()
    inventory_rows = []
    rtm_rows = []
    for cid in range(101, 151):
        row = rtm["per_id"][str(cid)]
        inventory_rows.append(
            {
                "id": cid,
                "official_batch": "batch03",
                "capability": catalog.get(cid, {}).get("capability"),
                "status": row["status"],
                "production_spine": row.get("production_spine"),
                "binding_file": row.get("binding_file"),
                "binding_function": row.get("binding_function"),
                "surface": row.get("surface"),
                "expected_surface": row.get("expected_surface"),
                "notes": row.get("notes"),
                "independent_build": row["status"] == "PRODUCTION-ALIGNED",
                "reused_link": row["status"] == "REUSED-LINK",
                "overlap_partial": row["status"] == "OVERLAP-PARTIAL",
            }
        )
        rtm_rows.append(
            {
                "id": cid,
                "capability": catalog.get(cid, {}).get("capability"),
                "official_batch": row["official_batch"],
                "status": row["status"],
                "production_spine": row.get("production_spine"),
                "binding_file": row.get("binding_file"),
                "binding_function": row.get("binding_function"),
                "surface": row.get("surface"),
                "expected_surface": row.get("expected_surface"),
                "notes": row.get("notes"),
            }
        )

    inventory = {
        "generated_at": datetime.now(UTC).isoformat(),
        "official_batch": "batch03",
        "scope": "IDs 101–150",
        "total": 50,
        "counts": {
            "production_aligned": rtm["production_aligned"],
            "independent_production_aligned": rtm["independent_production_aligned"],
            "reused_link": rtm["reused_link"],
            "overlap_partial": rtm["overlap_partial"],
            "not_complete": rtm["not_complete"],
        },
        "per_id": {str(r["id"]): r for r in inventory_rows},
    }
    rtm_out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "official_batch": "batch03",
        "scope": "IDs 101–150",
        "rtm_standard": "ISO/IEC/IEEE 29148",
        "all_verified": rtm["all_verified"],
        "counts": inventory["counts"],
        "rows": rtm_rows,
        "per_id": rtm["per_id"],
    }
    inv_path = ROOT / "docs/BATCH03_INVENTORY.json"
    rtm_doc_path = ROOT / "docs/BATCH03_RTM.json"
    inv_path.write_text(json.dumps(inventory, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    rtm_doc_path.write_text(json.dumps(rtm_out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"inventory": str(inv_path), "rtm": str(rtm_doc_path), "not_complete": rtm["not_complete"]}, indent=2))
    if proc.returncode != 0:
        raise SystemExit(proc.stderr or "RTM audit failed")


if __name__ == "__main__":
    main()
