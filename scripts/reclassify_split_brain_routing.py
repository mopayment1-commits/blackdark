#!/usr/bin/env python3
"""Reclassify SPLIT_BRAIN_ROUTING capabilities to SPLIT-BRAIN-UNVERIFIED."""

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
    "SPLIT-BRAIN-UNVERIFIED: pdf_registry/audit binding ≠ production backend_registry; "
    "audit function not executed on production path GET /api/cap646/{id}; "
    "production serves alternate backend — VERIFIED-DEEP claim suspended pending explicit registry wiring."
)

AUDIT_JSON = ROOT / "docs/PRODUCTION_PATH_ALIGNMENT_AUDIT_BATCHES_01_06.json"

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


def _load_routing_ids() -> list[int]:
    data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    return list(data["by_status"]["SPLIT_BRAIN_ROUTING"]["ids"])


def _reason_for(cid: int, row: dict | None = None) -> str:
    extra = ""
    if row:
        extra = f" audit={row.get('audit_path')}; production={row.get('production_path')} ({row.get('production_binding_source')})."
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
            row["deep_audit_classification"] = "SPLIT-BRAIN-UNVERIFIED"
            row["implementation_class"] = "split_brain_unverified"
            row["split_brain_routing"] = True
            row["prior_classification"] = row.get("prior_classification") or row.get("deep_audit_classification") or "VERIFIED-DEEP"
            row["reclassification_reason"] = _reason_for(cid, rows_by_id.get(cid))
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            notes = str(row.get("notes") or "")
            if "SPLIT-BRAIN-UNVERIFIED" not in notes:
                row["notes"] = (notes + " — SPLIT-BRAIN-UNVERIFIED (SPLIT_BRAIN_ROUTING)").strip(" —")
            changed += 1
            out_lines.append(json.dumps(row, ensure_ascii=False))
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return changed


def _recount(rows: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        cls = row.get("classification") or row.get("deep_audit_classification") or "UNKNOWN"
        counts[cls] = counts.get(cls, 0) + 1
    return counts


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
            row["classification"] = "SPLIT-BRAIN-UNVERIFIED"
            row["prior_classification"] = row.get("prior_classification") or row.get("classification") or "VERIFIED-DEEP"
            row["split_brain_routing"] = True
            row["reclassification_reason"] = _reason_for(cid, rows_by_id.get(cid))
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
        counts = _recount(data["rows"])
        data["classification_counts"] = {
            k: counts.get(k, 0)
            for k in (
                "VERIFIED-DEEP",
                "REUSED-LINK",
                "WRAPPER-ONLY-UNVERIFIED",
                "SPLIT-BRAIN-UNVERIFIED",
                "DEFERRED/DELEGATED",
            )
        }
        if "verified_deep_native_count" in data:
            data["verified_deep_native_count"] = counts.get("VERIFIED-DEEP", 0)
        if "split_brain_unverified_count" in data or True:
            data["split_brain_unverified_count"] = counts.get("SPLIT-BRAIN-UNVERIFIED", 0)
        data["split_brain_routing_reclassified_count"] = sum(
            1 for r in data["rows"] if r.get("split_brain_routing")
        )
        data["split_brain_routing_reclassified_at"] = datetime.now(UTC).isoformat()
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def _patch_retrospective_01_04(ids: frozenset[int], rows_by_id: dict[int, dict]) -> int:
    path = ROOT / "docs/RETROSPECTIVE_RECLASSIFICATION_BATCHES_01_04.json"
    if not path.is_file():
        return 0
    data = json.loads(path.read_text(encoding="utf-8"))
    changed = 0
    per_batch: dict[str, dict[str, int]] = {}
    for row in data.get("rows", []):
        cid = int(row["capability_id"])
        batch = row.get("batch", "")
        per_batch.setdefault(batch, {})
        if cid in ids:
            row["classification"] = "SPLIT-BRAIN-UNVERIFIED"
            row["split_brain_routing"] = True
            row["reclassification_reason"] = _reason_for(cid, rows_by_id.get(cid))
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
        cls = row["classification"]
        per_batch[batch][cls] = per_batch[batch].get(cls, 0) + 1
    data["per_batch_counts"] = {
        b: {
            "VERIFIED-DEEP": c.get("VERIFIED-DEEP", 0),
            "REUSED-LINK": c.get("REUSED-LINK", 0),
            "WRAPPER-ONLY-UNVERIFIED": c.get("WRAPPER-ONLY-UNVERIFIED", 0),
            "SPLIT-BRAIN-UNVERIFIED": c.get("SPLIT-BRAIN-UNVERIFIED", 0),
            "DEFERRED/DELEGATED": c.get("DEFERRED/DELEGATED", 0),
        }
        for b, c in per_batch.items()
    }
    totals = _recount(data["rows"])
    data["classification_counts"] = {
        k: totals.get(k, 0)
        for k in (
            "VERIFIED-DEEP",
            "REUSED-LINK",
            "WRAPPER-ONLY-UNVERIFIED",
            "SPLIT-BRAIN-UNVERIFIED",
            "DEFERRED/DELEGATED",
        )
    }
    data["split_brain_routing_reclassified_count"] = changed
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def _patch_checklist(ids: frozenset[int], rows_by_id: dict[int, dict]) -> int:
    import pandas as pd

    path = ROOT / "capabilities_checklist.xlsx"
    df = pd.read_excel(path)
    id_col = "#"
    status_col = "الحالة"
    changed = 0
    marker = "SPLIT-BRAIN-UNVERIFIED — SPLIT_BRAIN_ROUTING"
    for idx, row in df.iterrows():
        try:
            cid = int(row[id_col])
        except (TypeError, ValueError):
            continue
        if cid not in ids:
            continue
        old = str(row[status_col])
        if marker in old:
            continue
        base = re.sub(r"\s*—\s*VERIFIED-DEEP.*$", "", old)
        base = re.sub(r"\s*—\s*مبني جزئيًا.*$", "", base)
        df.at[idx, status_col] = f"{base} — {marker}; {_reason_for(cid, rows_by_id.get(cid))}"
        changed += 1
    df.to_excel(path, index=False)
    completed_path = ROOT / "capabilities_checklist_completed.xlsx"
    if completed_path.is_file():
        df.to_excel(completed_path, index=False)
    return changed


def main() -> None:
    routing_ids = _load_routing_ids()
    assert len(routing_ids) == 144, len(routing_ids)
    audit_data = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))
    rows_by_id = {int(r["capability_id"]): r for r in audit_data["rows"]}
    ids = frozenset(routing_ids)

    manifest = {
        "reclassified_at": datetime.now(UTC).isoformat(),
        "total": len(routing_ids),
        "classification": "SPLIT-BRAIN-UNVERIFIED",
        "source_status": "SPLIT_BRAIN_ROUTING",
        "reason_template": REASON,
        "ids": routing_ids,
        "sample_after_reclass": routing_ids[:5],
    }
    out = ROOT / "docs/SPLIT_BRAIN_ROUTING_RECLASSIFICATION_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    ev = _patch_evidence(ids, rows_by_id)
    au = _patch_audit_files(ids, rows_by_id)
    retro = _patch_retrospective_01_04(ids, rows_by_id)
    xlsx = _patch_checklist(ids, rows_by_id)
    print(
        json.dumps(
            {
                "evidence": ev,
                "audit": au,
                "retro": retro,
                "xlsx": xlsx,
                "total": len(routing_ids),
                "sample_5": routing_ids[:5],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
