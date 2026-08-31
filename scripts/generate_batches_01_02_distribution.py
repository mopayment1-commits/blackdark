#!/usr/bin/env python3
"""Generate batches 01-02 classification distribution report."""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BATCH01 = json.loads((ROOT / "scripts/partial_batches/batch_hero_01.json").read_text())["capability_ids"]
AUDIT = ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCHES_01_02.json"


def main() -> None:
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    rows = audit["rows"]
    b01_set = set(BATCH01)

    # Prefer live evidence classification over stale audit rows
    ev_by_id: dict[int, str] = {}
    for p in [
        ROOT / "data/hero_batch_01_evidence.jsonl",
        ROOT / "data/hero_batch_02_101_200_evidence.jsonl",
    ]:
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            ev_by_id[int(r["capability_id"])] = r.get("deep_audit_classification", "UNKNOWN")

    def _cls(row: dict) -> str:
        cid = int(row["capability_id"])
        return ev_by_id.get(cid) or row.get("classification", "UNKNOWN")

    by_scope: dict[str, Counter] = {
        "all_200_audit_rows": Counter(),
        "batch01_manifest_100": Counter(),
        "batch02_range_101_200": Counter(),
        "batch01_only_not_in_101_200": Counter(),
        "overlap_101_200_in_batch01": Counter(),
    }

    for row in rows:
        cid = int(row["capability_id"])
        cls = _cls(row)
        by_scope["all_200_audit_rows"][cls] += 1
        if cid in b01_set:
            by_scope["batch01_manifest_100"][cls] += 1
        if 101 <= cid <= 200:
            by_scope["batch02_range_101_200"][cls] += 1
            if cid in b01_set:
                by_scope["overlap_101_200_in_batch01"][cls] += 1
        if cid in b01_set and not (101 <= cid <= 200):
            by_scope["batch01_only_not_in_101_200"][cls] += 1

    # Evidence unique for batch01 file and batch02 file
    ev01 = {}
    for line in (ROOT / "data/hero_batch_01_evidence.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            ev01[int(r["capability_id"])] = r
    ev02 = {}
    for line in (ROOT / "data/hero_batch_02_101_200_evidence.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            ev02[int(r["capability_id"])] = r

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "note_97_verified_deep": (
            "Historical 97 VERIFIED-DEEP (batches 01-02) was unique-ID count in evidence JSONL before "
            "SPLIT-BRAIN/EXTENSION reclassifications, using dedup across overlapping batch-01 hero pulls. "
            "Current audit file has 200 rows (109 batch-01 scope + 91 batch-02-only 101-200)."
        ),
        "deferred_early_batch_clarification": (
            "DEFERRED-EARLY-BATCH (57 unique across ALL batches 01-06; was 58 before #725 moved to "
            "EXTENSION-PENDING-CAP646) is NOT the same as SPLIT-BRAIN B/C/D (58). Zero ID overlap. "
            "Prior label DEFERRED/DELEGATED was misleading when described as 'from batches 01-02 only' — "
            "actual split: b01=11, b02-range=40, b03=11 unique (evidence files)."
        ),
        "distribution": {k: dict(v) for k, v in by_scope.items()},
        "evidence_file_unique": {
            "hero_batch_01_evidence.jsonl": dict(Counter(r.get("deep_audit_classification") for r in ev01.values())),
            "hero_batch_02_101_200_evidence.jsonl": dict(
                Counter(r.get("deep_audit_classification") for r in ev02.values() if 101 <= int(r["capability_id"]) <= 200)
            ),
        },
        "historical_verified_deep_count_pre_reclass": 97,
    }

    json_path = ROOT / "docs/BATCHES_01_02_DISTRIBUTION_REPORT.json"
    md_path = ROOT / "docs/BATCHES_01_02_DISTRIBUTION_REPORT.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# Batches 01–02 — current classification distribution",
        "",
        f"**Generated:** {out['generated_at']}",
        "",
        "## Historical vs current",
        "",
        f"- **97 VERIFIED-DEEP** = pre-reclassification unique count (methodology difference; see note in JSON).",
        "- **200 audit rows** = `RETROSPECTIVE_DEEP_AUDIT_BATCHES_01_02.json` (109 batch-01 + 91 batch-02-only).",
        "",
        "## Current distribution (200 audit rows)",
        "",
        "| Classification | Count |",
        "|----------------|------:|",
    ]
    for k, v in sorted(by_scope["all_200_audit_rows"].items()):
        lines.append(f"| `{k}` | {v} |")
    lines.extend(
        [
            "",
            "## DEFERRED-EARLY-BATCH vs SPLIT-BRAIN B/C/D",
            "",
            out["deferred_early_batch_clarification"],
            "",
            "**By evidence file (unique IDs):**",
            "",
            f"- batch-01 file: `{out['evidence_file_unique']['hero_batch_01_evidence.jsonl']}`",
            f"- batch-02 file (101–200): `{out['evidence_file_unique']['hero_batch_02_101_200_evidence.jsonl']}`",
            "",
        ]
    )
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(by_scope["all_200_audit_rows"], indent=2))


if __name__ == "__main__":
    main()
