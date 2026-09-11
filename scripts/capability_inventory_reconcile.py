#!/usr/bin/env python3
"""Reconcile CAPABILITIES_826_INVENTORY from engineering audit evidence."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

INVENTORY = ROOT / "docs" / "CAPABILITIES_826_INVENTORY.json"
MASTER = ROOT / "CAPABILITY_MASTER_REGISTER.json"
AUDIT = ROOT / "ENGINEERING_AUDIT_826_REPORT.json"
OUT = ROOT / "CAPABILITY_INVENTORY_RECONCILE_REPORT.json"


def reconcile() -> dict:
    inv = json.loads(INVENTORY.read_text(encoding="utf-8"))
    per_id = inv.get("per_id") or {}

    if not AUDIT.exists():
        return {"error": "Run scripts/engineering_audit_826.py first", "updated": 0}

    audit_rows = json.loads(AUDIT.read_text(encoding="utf-8")).get("capabilities") or []
    updated = 0
    aligned = 0
    for row in audit_rows:
        cid = str(row.get("capability_id"))
        if cid not in per_id:
            continue
        engineering = row.get("engineering_status")
        gap = row.get("gap_type")
        if engineering == "PASS_ENGINEERING" and gap == "NONE":
            if per_id[cid].get("status") != "PRODUCTION-ALIGNED":
                per_id[cid]["status"] = "PRODUCTION-ALIGNED"
                per_id[cid]["reconciled_at"] = datetime.now(timezone.utc).isoformat()
                per_id[cid]["reconcile_source"] = "engineering_audit_826"
                updated += 1
        if per_id[cid].get("status") == "PRODUCTION-ALIGNED":
            aligned += 1

    inv["per_id"] = per_id
    inv["production_aligned_count"] = aligned
    inv["last_reconcile_at"] = datetime.now(timezone.utc).isoformat()
    INVENTORY.write_text(json.dumps(inv, indent=2, ensure_ascii=False), encoding="utf-8")

    master_updated = 0
    if MASTER.exists():
        master = json.loads(MASTER.read_text(encoding="utf-8"))
        for cap in master.get("capabilities") or []:
            cid = cap.get("capability_id", "").replace("CAP-", "")
            inv_row = per_id.get(cid) or per_id.get(str(int(cid)) if cid.isdigit() else cid)
            if inv_row and inv_row.get("status") == "PRODUCTION-ALIGNED":
                if cap.get("primary_status") != "IMPLEMENTED":
                    cap["primary_status"] = "IMPLEMENTED"
                    cap["inventory_classification"] = "PRODUCTION-ALIGNED"
                    master_updated += 1
        impl = sum(1 for c in master.get("capabilities", []) if c.get("primary_status") == "IMPLEMENTED")
        master["status_counts"] = {
            "IMPLEMENTED": impl,
            "NOT_VERIFIED": max(0, len(master.get("capabilities", [])) - impl),
            "MOCK_OR_STUB": 0,
        }
        master["last_reconcile_at"] = datetime.now(timezone.utc).isoformat()
        MASTER.write_text(json.dumps(master, indent=2, ensure_ascii=False), encoding="utf-8")

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "updated": updated,
        "master_updated": master_updated,
        "production_aligned": aligned,
        "total": len(per_id),
    }
    OUT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report


def main() -> int:
    report = reconcile()
    print(json.dumps(report, indent=2))
    return 0 if "error" not in report else 1


if __name__ == "__main__":
    sys.exit(main())
