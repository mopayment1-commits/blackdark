#!/usr/bin/env python3
"""Reclassify SPLIT_BRAIN B/C/D (58 IDs) to SPLIT-BRAIN-UNVERIFIED."""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

REASON = (
    "SPLIT-BRAIN-UNVERIFIED: REUSED/OTHER/GENERIC_HANDLER — audit binding not executed on production path; "
    "live execute_capability uses alternate backend_registry binding; VERIFIED-DEEP/REUSED-LINK claim suspended."
)

AUDIT_JSON = ROOT / "docs/PRODUCTION_PATH_ALIGNMENT_AUDIT_BATCHES_01_06.json"
CATEGORIES = ("SPLIT_BRAIN_REUSED", "SPLIT_BRAIN_OTHER", "SPLIT_BRAIN_GENERIC_HANDLER")

EVIDENCE_FILES = [
    ROOT / "data/hero_batch_01_evidence.jsonl",
    ROOT / "data/hero_batch_02_101_200_evidence.jsonl",
    ROOT / "data/hero_batch_03_201_300_evidence.jsonl",
    ROOT / "data/hero_batch_04_301_400_evidence.jsonl",
    ROOT / "data/hero_batch_05_401_500_evidence.jsonl",
    ROOT / "data/hero_batch_06_501_600_evidence.jsonl",
]

AUDIT_FILES = [
    ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCHES_01_02.json",
    ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_201_300.json",
    ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_04_301_400.json",
    ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_05_401_500.json",
    ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_06_501_600.json",
]


def _load_bcd_ids() -> tuple[list[int], dict[int, dict]]:
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    rows_by_id = {int(r["capability_id"]): r for r in data["rows"]}
    ids: list[int] = []
    for cat in CATEGORIES:
        ids.extend(data["by_status"][cat]["ids"])
    return sorted(set(ids)), rows_by_id


def _reason_for(cid: int, row: dict | None = None) -> str:
    extra = ""
    if row:
        extra = (
            f" category={row.get('alignment_status')};"
            f" audit={row.get('audit_path')};"
            f" production={row.get('production_path')} ({row.get('production_binding_source')})."
        )
    return f"{REASON}{extra}"


def _patch_evidence(ids: frozenset[int], rows_by_id: dict[int, dict]) -> int:
    changed = 0
    for path in EVIDENCE_FILES:
        if not path.is_file():
            continue
        out_lines: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cid = int(row["capability_id"])
            if cid not in ids:
                out_lines.append(json.dumps(row, ensure_ascii=False))
                continue
            row["prior_classification"] = row.get("prior_classification") or row.get("deep_audit_classification")
            row["deep_audit_classification"] = "SPLIT-BRAIN-UNVERIFIED"
            row["implementation_class"] = "split_brain_unverified"
            row["split_brain_bcd"] = True
            row["split_brain_category"] = rows_by_id.get(cid, {}).get("alignment_status")
            row["reclassification_reason"] = _reason_for(cid, rows_by_id.get(cid))
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
            out_lines.append(json.dumps(row, ensure_ascii=False))
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return changed


def _patch_audit_files(ids: frozenset[int], rows_by_id: dict[int, dict]) -> int:
    changed = 0
    for path in AUDIT_FILES:
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("rows") or []:
            cid = int(row["capability_id"])
            if cid not in ids:
                continue
            row["prior_classification"] = row.get("prior_classification") or row.get("classification")
            row["classification"] = "SPLIT-BRAIN-UNVERIFIED"
            row["split_brain_bcd"] = True
            row["reclassification_reason"] = _reason_for(cid, rows_by_id.get(cid))
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def _patch_checklist(ids: frozenset[int], rows_by_id: dict[int, dict]) -> int:
    import pandas as pd

    path = ROOT / "capabilities_checklist.xlsx"
    df = pd.read_excel(path)
    changed = 0
    marker = "SPLIT-BRAIN-UNVERIFIED — B/C/D"
    for idx, row in df.iterrows():
        try:
            cid = int(row["#"])
        except (TypeError, ValueError):
            continue
        if cid not in ids:
            continue
        old = str(row["الحالة"])
        if marker in old:
            continue
        base = re.sub(r"\s*—\s*(VERIFIED-DEEP|REUSED-LINK|مبني جزئيًا).*$", "", old)
        df.at[idx, "الحالة"] = f"{base} — {marker}; {_reason_for(cid, rows_by_id.get(cid))}"
        changed += 1
    df.to_excel(path, index=False)
    return changed


def main() -> None:
    bcd_ids, rows_by_id = _load_bcd_ids()
    assert len(bcd_ids) == 58, len(bcd_ids)
    ids = frozenset(bcd_ids)
    by_cat = {c: [] for c in CATEGORIES}
    for cid in bcd_ids:
        by_cat[rows_by_id[cid]["alignment_status"]].append(cid)

    manifest = {
        "reclassified_at": datetime.now(UTC).isoformat(),
        "total": len(bcd_ids),
        "classification": "SPLIT-BRAIN-UNVERIFIED",
        "source_categories": CATEGORIES,
        "by_category": {k: {"count": len(v), "ids": v} for k, v in by_cat.items()},
        "reason_template": REASON,
        "entries": {str(cid): _reason_for(cid, rows_by_id.get(cid)) for cid in bcd_ids},
    }
    out = ROOT / "docs/SPLIT_BRAIN_BCD_RECLASSIFICATION_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ev = _patch_evidence(ids, rows_by_id)
    au = _patch_audit_files(ids, rows_by_id)
    xlsx = _patch_checklist(ids, rows_by_id)
    print(json.dumps({"evidence": ev, "audit": au, "xlsx": xlsx, "total": len(bcd_ids)}, indent=2))


if __name__ == "__main__":
    main()
