#!/usr/bin/env python3
"""Reclassify Option A IDs (#338,#500,#507,#534) to PRODUCTION-ALIGNED."""

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
PROOF = ROOT / "docs/OPTION_A_PRODUCTION_PROOF.json"

EVIDENCE_FILES = {
    4: ROOT / "data/hero_batch_04_301_400_evidence.jsonl",
    5: ROOT / "data/hero_batch_05_401_500_evidence.jsonl",
    6: ROOT / "data/hero_batch_06_501_600_evidence.jsonl",
}

AUDIT_FILES = {
    4: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_04_301_400.json",
    5: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_05_401_500.json",
    6: ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_06_501_600.json",
}


def _reason_for(cid: int) -> str:
    proof = json.loads(PROOF.read_text(encoding="utf-8"))
    row = next(p for p in proof["proofs"] if p["capability_id"] == cid)
    binding = row["backend_registry"]
    return (
        f"PRODUCTION-ALIGNED: explicit_option_a binding verified live via cap646.runtime.execute_capability; "
        f"backend={binding['backend_module']}.{binding['backend_entrypoint']}; "
        f"surface={binding['surface']}; proof={PROOF.name}."
    )


def _patch_evidence() -> int:
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
            if cid not in OPTION_A_IDS:
                out_lines.append(json.dumps(row, ensure_ascii=False))
                continue
            row["prior_classification"] = row.get("prior_classification") or row.get("deep_audit_classification")
            row["deep_audit_classification"] = "PRODUCTION-ALIGNED"
            row["implementation_class"] = "production_aligned"
            row["option_a_verified"] = True
            row["template_seed_stub"] = False
            row["reclassification_reason"] = _reason_for(cid)
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
            out_lines.append(json.dumps(row, ensure_ascii=False))
        path.write_text("\n".join(out_lines) + "\n", encoding="utf-8")
    return changed


def _patch_audit() -> int:
    changed = 0
    for path in AUDIT_FILES.values():
        data = json.loads(path.read_text(encoding="utf-8"))
        for row in data.get("rows") or []:
            cid = int(row["capability_id"])
            if cid not in OPTION_A_IDS:
                continue
            row["prior_classification"] = row.get("prior_classification") or row.get("classification")
            row["classification"] = "PRODUCTION-ALIGNED"
            row["option_a_verified"] = True
            row["reclassification_reason"] = _reason_for(cid)
            row["reclassified_at"] = datetime.now(UTC).isoformat()
            changed += 1
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return changed


def _patch_checklist() -> int:
    import pandas as pd

    path = ROOT / "capabilities_checklist.xlsx"
    df = pd.read_excel(path)
    changed = 0
    marker = "PRODUCTION-ALIGNED — Option A"
    for idx, row in df.iterrows():
        try:
            cid = int(row["#"])
        except (TypeError, ValueError):
            continue
        if cid not in OPTION_A_IDS:
            continue
        old = str(row["الحالة"])
        if marker in old:
            continue
        base = re.sub(r"\s*—\s*(WRAPPER-ONLY-UNVERIFIED|DEFERRED/TEMPLATE-STUB).*$", "", old)
        df.at[idx, "الحالة"] = f"{base} — {marker}; {_reason_for(cid)}"
        changed += 1
    df.to_excel(path, index=False)
    return changed


def main() -> None:
    manifest = {
        "reclassified_at": datetime.now(UTC).isoformat(),
        "total": len(OPTION_A_IDS),
        "classification": "PRODUCTION-ALIGNED",
        "ids": sorted(OPTION_A_IDS),
        "entries": {str(cid): _reason_for(cid) for cid in sorted(OPTION_A_IDS)},
        "proof_file": str(PROOF.relative_to(ROOT)),
    }
    out = ROOT / "docs/OPTION_A_PRODUCTION_ALIGNED_MANIFEST.json"
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    ev = _patch_evidence()
    au = _patch_audit()
    xlsx = _patch_checklist()
    print(json.dumps({"evidence": ev, "audit": au, "xlsx": xlsx, "total": len(OPTION_A_IDS)}, indent=2))


if __name__ == "__main__":
    main()
