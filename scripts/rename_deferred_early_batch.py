#!/usr/bin/env python3
"""Rename DEFERRED/DELEGATED → DEFERRED-EARLY-BATCH to avoid confusion with SPLIT-BRAIN B/C/D."""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = "DEFERRED/DELEGATED"
NEW = "DEFERRED-EARLY-BATCH"
REASON = (
    "Renamed from DEFERRED/DELEGATED: hero batches 01-03 early closure deferrals (missing domain spec / "
    "Wave deferral) — NOT the same as SPLIT-BRAIN B/C/D (58) nor DEFERRED/TEMPLATE-STUB (307 Option B)."
)

EVIDENCE = list((ROOT / "data").glob("hero_batch_*_evidence.jsonl")) + [ROOT / "data/hero_batch_01_evidence.jsonl"]
EVIDENCE = sorted(set(EVIDENCE))
AUDIT_FILES = list((ROOT / "docs").glob("RETROSPECTIVE_DEEP_AUDIT*.json"))


def main() -> None:
    ev_changed = 0
    for path in EVIDENCE:
        if not path.is_file():
            continue
        out = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("deep_audit_classification") == OLD:
                row["deep_audit_classification"] = NEW
                row["deferred_early_batch"] = True
                row["rename_reason"] = REASON
                row["renamed_at"] = datetime.now(UTC).isoformat()
                ev_changed += 1
            out.append(json.dumps(row, ensure_ascii=False))
        path.write_text("\n".join(out) + "\n", encoding="utf-8")

    au_changed = 0
    for path in AUDIT_FILES:
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("rows", []):
            if row.get("classification") == OLD:
                row["classification"] = NEW
                row["deferred_early_batch"] = True
                au_changed += 1
        if "classification_counts" in data and OLD in data["classification_counts"]:
            counts = data["classification_counts"]
            counts[NEW] = counts.get(NEW, 0) + counts.pop(OLD, 0)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    import pandas as pd

    xlsx_changed = 0
    for xlsx in [ROOT / "capabilities_checklist.xlsx"]:
        if not xlsx.is_file():
            continue
        df = pd.read_excel(xlsx)
        col = "الحالة"
        for idx, val in df[col].items():
            s = str(val)
            if OLD in s:
                df.at[idx, col] = s.replace(OLD, NEW)
                xlsx_changed += 1
        df.to_excel(xlsx, index=False)

    manifest = {
        "renamed_at": datetime.now(UTC).isoformat(),
        "old_classification": OLD,
        "new_classification": NEW,
        "reason": REASON,
        "scope": "58 unique IDs across hero batches 01-06 (NOT batches 01-02 only)",
        "by_evidence_file": {},
    }
    ids = set()
    for path in EVIDENCE:
        c = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("deep_audit_classification") == NEW:
                c += 1
                ids.add(int(row["capability_id"]))
        manifest["by_evidence_file"][str(path.relative_to(ROOT))] = c
    manifest["unique_ids"] = sorted(ids)
    manifest["unique_count"] = len(ids)

    out = ROOT / "docs/DEFERRED_EARLY_BATCH_RENAME_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"evidence": ev_changed, "audit": au_changed, "xlsx": xlsx_changed, "unique": len(ids)}, indent=2))


if __name__ == "__main__":
    main()
