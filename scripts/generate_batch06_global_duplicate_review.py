#!/usr/bin/env python3
"""Global duplicate/canonical review — Batch06 (251-300) vs official batches 01-05."""

from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch06_dedicated import BATCH06_REUSED_LINK_IDS, EXPECTED_SURFACE, _REUSED_LINK_CATALOG  # noqa: E402

OUT_JSON = ROOT / "docs/BATCH06_GLOBAL_DUPLICATE_CANONICAL_REVIEW_BATCH01_06.json"
OUT_MD = ROOT / "docs/BATCH06_GLOBAL_DUPLICATE_CANONICAL_REVIEW_BATCH01_06.md"
GAP = ROOT / "docs/cap646/CAP646_GAP_MATRIX.json"
CATALOG = ROOT / "docs/cap646/CAP646_CATALOG.json"

PRIOR_ACCEPTANCE = {
    "batch03": ROOT / "docs/BATCH03_ACCEPTANCE_101_150.json",
    "batch04": ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json",
    "batch05": ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json",
}

BATCH_MODULES = {
    "batch01": "cap646.batch01_dedicated",
    "batch02": "cap646.batch02_dedicated",
    "batch03": "cap646.batch03_dedicated",
    "batch04": "cap646.batch04_dedicated",
    "batch05": "cap646.batch05_dedicated",
    "batch06": "cap646.batch06_dedicated",
}


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _load_surfaces(module_name: str) -> dict[int, str]:
    mod = importlib.import_module(module_name)
    return dict(getattr(mod, "EXPECTED_SURFACE", {}))


def _load_catalog() -> dict[int, dict]:
    raw = json.loads(CATALOG.read_text(encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("capabilities", [])
    return {int(r["id"]): r for r in rows}


def _load_gap() -> dict[int, dict]:
    rows = json.loads(GAP.read_text(encoding="utf-8"))["rows"]
    return {int(r["id"]): r for r in rows}


def _load_acceptance_surfaces() -> dict[int, dict[str, Any]]:
    by_id: dict[int, dict[str, Any]] = {}
    for batch, path in PRIOR_ACCEPTANCE.items():
        if not path.is_file():
            continue
        doc = json.loads(path.read_text(encoding="utf-8"))
        for row in doc["rows"]:
            cid = row["capability_id"]
            by_id[cid] = {
                "batch": batch,
                "expected_surface": row.get("expected_surface"),
                "status": row.get("status"),
                "capability_name": row.get("capability_name"),
            }
    return by_id


def _parse_duplicate_of(reason: str) -> int | None:
    m = re.search(r"(?:ID|#)(\d+)", reason or "")
    return int(m.group(1)) if m else None


def review_row(
    cid: int,
    catalog: dict,
    gap: dict,
    prior_surfaces: dict[str, dict[int, str]],
    acceptance_surfaces: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    cat = catalog[cid]
    surface = EXPECTED_SURFACE[cid]
    gap_row = gap.get(cid, {})
    gap_class = gap_row.get("final_classification")
    gap_canonical = _parse_duplicate_of(gap_row.get("reason", ""))

    collisions: list[dict[str, Any]] = []
    for batch, surfaces in prior_surfaces.items():
        if batch == "batch06":
            continue
        for prior_id, prior_surface in surfaces.items():
            if prior_surface == surface and prior_id != cid:
                collisions.append(
                    {
                        "type": "SURFACE_COLLISION",
                        "prior_batch": batch,
                        "prior_id": prior_id,
                        "shared_surface": surface,
                    }
                )

    reused = cid in BATCH06_REUSED_LINK_IDS
    link = _REUSED_LINK_CATALOG.get(cid, {})
    canonical_id = link.get("canonical_capability_id") or gap_canonical
    canonical_batch = link.get("canonical_spine") or (
        acceptance_surfaces.get(canonical_id, {}).get("batch") if canonical_id else None
    )

    decision = "DISTINCT"
    if reused:
        decision = "REUSED-LINK"
    elif gap_class == "DUPLICATE/ALREADY_COVERED":
        decision = "DUPLICATE_ALIAS"
    elif collisions:
        decision = "SURFACE_OVERLAP_REVIEW"

    return {
        "capability_id": cid,
        "capability_name": cat["capability"],
        "expected_surface": surface,
        "gap_matrix_classification": gap_class,
        "gap_matrix_canonical_hint": gap_canonical,
        "batch06_decision": decision,
        "reused_link": reused,
        "canonical_capability_id": canonical_id,
        "canonical_spine": canonical_batch,
        "binding": link.get("binding"),
        "alias_of": link.get("alias_of"),
        "surface_collisions": collisions,
        "mece_action": (
            "Migrate facade — no parallel implementation"
            if reused
            else "Strangler — preserve DISTINCT catalog ID with dedicated surface"
            if decision == "DISTINCT"
            else "Review MECE — resolve surface/name collision before PA elevation"
        ),
    }


def build_report() -> dict[str, Any]:
    catalog = _load_catalog()
    gap = _load_gap()
    prior_surfaces = {batch: _load_surfaces(mod) for batch, mod in BATCH_MODULES.items()}
    acceptance_surfaces = _load_acceptance_surfaces()

    rows = [review_row(cid, catalog, gap, prior_surfaces, acceptance_surfaces) for cid in range(251, 301)]
    by_decision: dict[str, int] = defaultdict(int)
    for row in rows:
        by_decision[row["batch06_decision"]] += 1

    cross_batch_canonical = [
        r for r in rows if r["reused_link"] and r.get("canonical_capability_id")
    ]

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "scope": "Batch06 IDs 251-300 compared against official batches 01-05",
        "method": "EXPECTED_SURFACE cross-batch scan + gap matrix DUPLICATE hints + REUSED-LINK catalog",
        "locks": {
            "batch06_independent": 0,
            "progress_826": 179,
            "production_aligned_count": 0,
        },
        "summary": {
            "total": 50,
            "reused_link": len(BATCH06_REUSED_LINK_IDS),
            "strangler": 50 - len(BATCH06_REUSED_LINK_IDS),
            "by_decision": dict(by_decision),
            "surface_collision_ids": [r["capability_id"] for r in rows if r["surface_collisions"]],
            "new_hidden_duplicates": sum(
                1
                for r in rows
                if r["batch06_decision"] == "DUPLICATE_ALIAS" and not r["reused_link"]
            ),
        },
        "reused_link_cross_batch": cross_batch_canonical,
        "rows": rows,
    }


def write_md(report: dict[str, Any]) -> None:
    s = report["summary"]
    lines = [
        "# Batch06 Global Duplicate / Canonical Review (Batches 01–06)",
        "",
        f"**Generated:** {report['generated_at']} · **Commit:** `{report['git_commit'][:8]}`",
        "",
        "## Summary",
        "",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| Total IDs | {s['total']} |",
        f"| REUSED-LINK | {s['reused_link']} |",
        f"| Strangler | {s['strangler']} |",
        f"| Surface collision IDs | {len(s['surface_collision_ids'])} |",
        f"| New hidden duplicates | {s['new_hidden_duplicates']} |",
        "",
        "## Decision breakdown",
        "",
    ]
    for decision, count in sorted(s["by_decision"].items()):
        lines.append(f"- **{decision}**: {count}")
    lines += [
        "",
        "## REUSED-LINK cross-batch canonical map",
        "",
        "| ID | Canonical | Spine | Binding |",
        "|----|-----------|-------|---------|",
    ]
    for row in report["reused_link_cross_batch"]:
        lines.append(
            f"| {row['capability_id']} | #{row['canonical_capability_id']} | {row['canonical_spine']} | `{row.get('binding', '—')}` |"
        )
    lines += ["", f"Full JSON: `{OUT_JSON.relative_to(ROOT)}`"]
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    report = build_report()
    OUT_JSON.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    write_md(report)
    print(
        f"Wrote {OUT_JSON.name} — reused_link={report['summary']['reused_link']} "
        f"decisions={report['summary']['by_decision']}"
    )


if __name__ == "__main__":
    main()
