#!/usr/bin/env python3
"""Generate final 50-row Batch04 closure status table."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RTM = json.loads((ROOT / "docs/BATCH04_RTM_151_200.json").read_text(encoding="utf-8"))

rows = []
for row in sorted(RTM["rows"], key=lambda r: r["id"]):
    rows.append(
        {
            "id": row["id"],
            "capability": row.get("capability"),
            "closure_status": row.get("closure_status"),
            "final_state": row.get("closure_status"),
            "binding": f"{row.get('binding_file')}::{row.get('binding_function')}" if row.get("binding_file") else row.get("canonical_module_function"),
            "owner_note": row.get("owner_note") or row.get("blocker") or row.get("vendor_status"),
            "miswire_remediation": row.get("miswire_remediation"),
        }
    )

out = {
    "generated_at": RTM.get("generated_at"),
    "build_phase": RTM.get("build_phase"),
    "production_aligned_count": RTM.get("production_aligned_count"),
    "progress_826_batch04_pa": RTM.get("production_aligned_count"),
    "rows": rows,
}
path = ROOT / "docs/BATCH04_FINAL_CLOSURE_STATUS_151_200.json"
path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
print(f"Wrote {path} — PA={out['production_aligned_count']}/50")
