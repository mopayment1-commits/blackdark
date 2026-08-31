#!/usr/bin/env python3
"""Reclassify 307 Option-B TEMPLATE-STUB IDs to DEFERRED/TEMPLATE-STUB."""

from __future__ import annotations

import json
import re
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OPTION_A_IDS = frozenset({338, 500, 507, 534})
PLAN = ROOT / "docs/TEMPLATE_STUB_311_REMEDIATION_PLAN.json"

EVIDENCE_FILES = {
    3: ROOT / "data/hero_batch_03_201_300_evidence.jsonl",
    4: ROOT / "data/hero_batch_04_301_400_evidence.jsonl",
    5: ROOT / "data/hero_batch_05_401_500_evidence.jsonl",
    6: ROOT / "data/hero_batch_06_501_600_evidence.jsonl",
}

AUDIT_FILES = {
    3: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_201_300.json",
    4: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_04_301_400.json",
    5: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_05_401_500.json",
    6: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_06_501_600.json",
}


def _load_deferred_entries() -> dict[int, dict]:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    out: dict[int, dict] = {}
    for entry in plan["entries"]:
        if entry["decision"] != "B_DEFERRED":
            continue
        cid = int(entry["capability_id"])
        out[cid] = entry
    assert len(out) == 307, len(out)
    return out


def _reason_for(entry: dict) -> str:
    deferral = entry.get("deferral_if_B") or {}
    return (
        f"DEFERRED/TEMPLATE-STUB: {entry.get('decision_rationale')} "
        f"blocked_by={deferral.get('blocked_by')}; "
        f"allowed_interim={deferral.get('allowed_interim')}; "
        f"catalog={entry.get('catalog_name')}."
    )


def _patch_evidence(entries: dict[int, dict]) -> int:
    changed = 0
    for path in EVIDENCE_FILES.values():
        if not path.is_file():
            continue
        out_lines: list[str] = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cid = int(row["capability_id"])
            if cid not in entries:
                out_lines.append(json.dumps(row, ensure_ascii=False))
                continue
            entry = entries[cid]
            row["prior_classification"] = row.get("prior_classification") or row.get("deep_audit_classification")
            row["deep_audit_classification"] = "DEFERRED/TEMPLATE-STUB"
            row["implementation_class"] = "deferred_template_stub"
            row["template_seed_stub"] = True
            row["option_b_deferred"] = True
            row["reclassification_reason"] = _reason_for(entry)
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
            out_lines.append(json.dumps(row, ensure_ascii=False))
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return changed


def _patch_audit(entries: dict[int, dict]) -> int:
    changed = 0
    for path in AUDIT_FILES.values():
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("rows") or []:
            cid = int(row["capability_id"])
            if cid not in entries:
                continue
            row["prior_classification"] = row.get("prior_classification") or row.get("classification")
            row["classification"] = "DEFERRED/TEMPLATE-STUB"
            row["option_b_deferred"] = True
            row["reclassification_reason"] = _reason_for(entries[cid])
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def _patch_checklist(entries: dict[int, dict]) -> int:
    import pandas as pd

    path = ROOT / "capabilities_checklist.xlsx"
    df = pd.read_excel(path)
    changed = 0
    marker = "DEFERRED/TEMPLATE-STUB — Option B"
    for idx, row in df.iterrows():
        try:
            cid = int(row["#"])
        except (TypeError, ValueError):
            continue
        if cid not in entries:
            continue
        old = str(row["الحالة"])
        if marker in old:
            continue
        base = re.sub(r"\s*—\s*WRAPPER-ONLY-UNVERIFIED.*$", "", old)
        df.at[idx, "الحالة"] = f"{base} — {marker}; {_reason_for(entries[cid])}"
        changed += 1
    df.to_excel(path, index=False)
    return changed


def main() -> None:
    entries = _load_deferred_entries()
    manifest = {
        "reclassified_at": datetime.now(UTC).isoformat(),
        "total": len(entries),
        "classification": "DEFERRED/TEMPLATE-STUB",
        "option": "B_DEFERRED",
        "excluded_option_a": sorted(OPTION_A_IDS),
        "entries": {str(cid): {**e, "reclassification_reason": _reason_for(e)} for cid, e in entries.items()},
    }
    out = ROOT / "docs/OPTION_B_DEFERRED_RECLASSIFICATION_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ev = _patch_evidence(entries)
    au = _patch_audit(entries)
    xlsx = _patch_checklist(entries)
    print(json.dumps({"evidence": ev, "audit": au, "xlsx": xlsx, "total": len(entries)}, indent=2))


if __name__ == "__main__":
    main()
