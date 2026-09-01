#!/usr/bin/env python3
"""Generate institutional inventory for 826 project-scope capabilities."""

from __future__ import annotations

import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap978.catalog import PROJECT_SCOPE_TOTAL

EVIDENCE_GLOBS = sorted((ROOT / "data").glob("hero_batch_*_evidence.jsonl"))
OPTION_A_MANIFEST = ROOT / "docs/OPTION_A_PRODUCTION_ALIGNED_MANIFEST.json"
BATCH01_MANIFEST = ROOT / "docs/BATCH01_826_COMPLETION_MANIFEST.json"
BATCH02_CLASSIFICATION = ROOT / "docs/BATCH02_CLASSIFICATION.json"


def _load_evidence() -> dict[int, dict[str, Any]]:
    rows: dict[int, dict[str, Any]] = {}
    for path in EVIDENCE_GLOBS:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            cid = int(row["capability_id"])
            if cid <= PROJECT_SCOPE_TOTAL:
                rows[cid] = row
    return rows


def main() -> None:
    from cap646.catalog import catalog_by_id
    from cap646.backend_registry import binding_for
    from cap646.batch01_production import BATCH01_IDS
    from cap646.batch02_production import BATCH02_IDS
    from cap646.waves import USER_FACING

    evidence = _load_evidence()
    production_aligned = set(json.loads(OPTION_A_MANIFEST.read_text()).get("ids", [])) if OPTION_A_MANIFEST.is_file() else set()
    if BATCH01_MANIFEST.is_file():
        production_aligned |= set(json.loads(BATCH01_MANIFEST.read_text()).get("capability_ids", []))
    batch02_manifest = ROOT / "docs/BATCH02_826_COMPLETION_MANIFEST.json"
    batch02_new_aligned: set[int] = set()
    batch02_overlap: set[int] = set()
    batch02_reused: set[int] = set()
    batch02_not_complete: set[int] = set()
    if batch02_manifest.is_file():
        b02 = json.loads(batch02_manifest.read_text())
        batch02_new_aligned = set(b02.get("new_production_aligned_ids", []))
        batch02_overlap = set(b02.get("overlap_batch01_ids", []))
        batch02_reused = set(b02.get("reused_link_ids", []))
        batch02_not_complete = set(b02.get("not_complete_ids", []))
        production_aligned |= batch02_new_aligned
    if BATCH02_CLASSIFICATION.is_file():
        b02c = json.loads(BATCH02_CLASSIFICATION.read_text())
        batch02_new_aligned |= set(b02c.get("new_production_aligned_ids", []))
        batch02_overlap |= set(b02c.get("overlap_batch01_ids", []))
        batch02_reused |= set(b02c.get("reused_link_ids", []))
        batch02_not_complete |= set(b02c.get("not_complete_ids", []))

    per_id: dict[str, Any] = {}
    counts: dict[str, int] = {}
    for cid in range(1, PROJECT_SCOPE_TOTAL + 1):
        ev = evidence.get(cid)
        cls = ev.get("deep_audit_classification") if ev else "NOT_IN_HERO_AUDIT"
        if cid in batch02_reused:
            cls = "REUSED-LINK"
        elif cid in batch02_overlap:
            cls = "OVERLAP_BATCH01"
        elif cid in batch02_not_complete:
            cls = "NOT_COMPLETE"
        elif cid in BATCH01_IDS or cid in batch02_new_aligned:
            cls = "PRODUCTION-ALIGNED"
        elif cid in production_aligned:
            cls = "PRODUCTION-ALIGNED"
        counts[cls] = counts.get(cls, 0) + 1
        try:
            binding = binding_for(cid)
        except Exception:
            binding = {}
        per_id[str(cid)] = {
            "capability": catalog_by_id().get(cid, {}).get("capability"),
            "classification": cls,
            "in_hero_evidence": cid in evidence,
            "user_facing": cid in USER_FACING,
            "binding_source": binding.get("binding_source"),
            "backend": f"{binding.get('backend_module')}.{binding.get('backend_entrypoint')}",
        }

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": f"IDs 1-{PROJECT_SCOPE_TOTAL} institutional completion inventory",
        "summary": {
            "total_ids": PROJECT_SCOPE_TOTAL,
            "classification_counts": counts,
            "production_aligned_count": counts.get("PRODUCTION-ALIGNED", 0),
            "user_facing_count": len([cid for cid in USER_FACING if cid <= PROJECT_SCOPE_TOTAL]),
        },
        "per_id": per_id,
    }
    json_path = ROOT / "docs/CAPABILITIES_826_INVENTORY.json"
    md_path = ROOT / "docs/CAPABILITIES_826_INVENTORY.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# CAPABILITIES 826 — Institutional Inventory",
        "",
        f"Generated: {out['generated_at']}",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| Total scope | {PROJECT_SCOPE_TOTAL} |",
        f"| PRODUCTION-ALIGNED | {counts.get('PRODUCTION-ALIGNED', 0)} |",
        "",
        "## Classification breakdown",
        "",
        "| Classification | Count |",
        "|----------------|------:|",
    ]
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v} |")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print(f"Wrote {json_path} and {md_path}")


if __name__ == "__main__":
    main()
