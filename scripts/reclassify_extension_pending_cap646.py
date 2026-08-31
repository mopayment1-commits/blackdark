#!/usr/bin/env python3
"""Reclassify CAP978-only extension IDs to EXTENSION-PENDING-CAP646."""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXTENSION_IDS = frozenset({704, 708, 725, 812, 813, 814, 815})
REASON = (
    "EXTENSION-PENDING-CAP646: ID present in CAP978/heroes evidence but absent from "
    "cap646.backend_registry (binding_for KeyError). Historical quad-evidence used "
    "pdf_capability_registry — apparent success did NOT prove production /api/cap646 path. "
    "Requires cap646 registration or dedicated CAP978 extension verification track."
)

EVIDENCE = ROOT / "data/hero_batch_01_evidence.jsonl"
AUDIT = ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCHES_01_02.json"


def main() -> None:
    changed = 0
    out_lines = []
    for line in EVIDENCE.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        cid = int(row["capability_id"])
        if cid not in EXTENSION_IDS:
            out_lines.append(json.dumps(row, ensure_ascii=False))
            continue
        row["prior_classification"] = row.get("prior_classification") or row.get("deep_audit_classification")
        row["deep_audit_classification"] = "EXTENSION-PENDING-CAP646"
        row["extension_pending_cap646"] = True
        row["reclassification_reason"] = REASON
        row["reclassified_at"] = datetime.now(UTC).isoformat()
        changed += 1
        out_lines.append(json.dumps(row, ensure_ascii=False))
    EVIDENCE.write_text("\n".join(out_lines) + "\n", encoding="utf-8")

    data = json.loads(AUDIT.read_text(encoding="utf-8"))
    for row in data.get("rows") or []:
        if int(row["capability_id"]) in EXTENSION_IDS:
            row["prior_classification"] = row.get("prior_classification") or row.get("classification")
            row["classification"] = "EXTENSION-PENDING-CAP646"
            row["reclassification_reason"] = REASON
            row["reclassified_at"] = datetime.now(UTC).isoformat()

    AUDIT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    import pandas as pd

    df = pd.read_excel(ROOT / "capabilities_checklist.xlsx")
    for idx, row in df.iterrows():
        try:
            cid = int(row["#"])
        except (TypeError, ValueError):
            continue
        if cid not in EXTENSION_IDS:
            continue
        old = str(row["الحالة"])
        if "EXTENSION-PENDING-CAP646" in old:
            continue
        base = re.sub(r"\s*—\s*(VERIFIED-DEEP|REUSED-LINK).*$", "", old)
        df.at[idx, "الحالة"] = f"{base} — EXTENSION-PENDING-CAP646; {REASON}"
    df.to_excel(ROOT / "capabilities_checklist.xlsx", index=False)

    manifest = {
        "reclassified_at": datetime.now(UTC).isoformat(),
        "total": len(EXTENSION_IDS),
        "classification": "EXTENSION-PENDING-CAP646",
        "ids": sorted(EXTENSION_IDS),
        "reason": REASON,
        "verification_path": "Register in cap646 catalog + backend_registry OR CAP978 extension closure track",
    }
    (ROOT / "docs/EXTENSION_PENDING_CAP646_MANIFEST.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(json.dumps({"changed": changed, "total": len(EXTENSION_IDS)}, indent=2))


if __name__ == "__main__":
    main()
