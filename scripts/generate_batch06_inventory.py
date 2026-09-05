#!/usr/bin/env python3
"""Generate BATCH06_INVENTORY.json — 50-row slice from catalog + gap matrix + module map."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch06_dedicated import BATCH06_REUSED_LINK_IDS, EXPECTED_SURFACE  # noqa: E402
from cap646.batch06_ids import BATCH06_IDS, BATCH06_MANIFEST_IDS  # noqa: E402

CATALOG_PATH = ROOT / "docs/cap646/CAP646_CATALOG.json"
GAP_PATH = ROOT / "docs/cap646/CAP646_GAP_MATRIX.json"
MODULE_MAP_PATH = ROOT / "docs/cap646/CAP646_MODULE_MAP.json"
OUT = ROOT / "docs/BATCH06_INVENTORY.json"


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _load_rows(path: Path, key: str = "rows") -> dict[int, dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = doc[key] if key in doc else doc.get("entries", [])
    return {int(r["id"]): r for r in rows}


def _inventory_row(cid: int, catalog: dict, gap: dict, module_map: dict) -> dict:
    cat = catalog[cid]
    gap_row = gap.get(cid, {})
    mod = module_map.get(cid)
    reused = cid in BATCH06_REUSED_LINK_IDS
    surface = EXPECTED_SURFACE.get(cid)
    gap_class = gap_row.get("final_classification", "UNKNOWN")
    return {
        "id": cid,
        "official_batch": "batch06",
        "capability": cat["capability"],
        "track": cat["track"],
        "track_name": cat.get("track_name"),
        "expected_surface": surface,
        "status": "REUSED-LINK" if reused else "NOT_COMPLETE",
        "production_spine": "batch06",
        "binding_file": "cap646/batch06_dedicated.py",
        "binding_function": f"_cap{cid}",
        "independent_build": False,
        "reused_link": reused,
        "strangler": not reused,
        "gap_matrix": {
            "final_classification": gap_class,
            "current_status": gap_row.get("current_status"),
            "reason": gap_row.get("reason"),
            "existing_code_components": gap_row.get("existing_code_components") or [],
            "tests_evidence": gap_row.get("tests_evidence") or [],
        },
        "module_map": (
            {
                "backend_module": mod["backend_module"],
                "backend_entrypoint": mod["backend_entrypoint"],
                "surface": mod["surface"],
                "binding_source": mod["binding_source"],
            }
            if mod
            else None
        ),
        "notes": (
            "REUSED-LINK facade — canonical spine delegated in batch06_dedicated"
            if reused
            else "Strangler spine — catalog-aligned payload pending PA elevation"
        ),
    }


def _load_catalog() -> dict[int, dict]:
    raw = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        return {int(r["id"]): r for r in raw}
    return {int(r["id"]): r for r in raw.get("capabilities", raw.get("rows", []))}


def main() -> None:
    catalog = _load_catalog()

    gap = _load_rows(GAP_PATH)
    module_map = _load_rows(MODULE_MAP_PATH)

    rows = [_inventory_row(cid, catalog, gap, module_map) for cid in range(251, 301)]
    counts = {
        "reused_link": sum(1 for r in rows if r["reused_link"]),
        "strangler": sum(1 for r in rows if r["strangler"]),
        "not_complete": sum(1 for r in rows if r["status"] == "NOT_COMPLETE"),
        "production_aligned": 0,
    }

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "commit": _git_head(),
        "official_batch": "batch06",
        "scope": "IDs 251–300",
        "total": 50,
        "sources": [
            str(CATALOG_PATH.relative_to(ROOT)),
            str(GAP_PATH.relative_to(ROOT)),
            str(MODULE_MAP_PATH.relative_to(ROOT)),
        ],
        "routing_lock": {
            "BATCH06_MANIFEST_IDS": len(BATCH06_MANIFEST_IDS),
            "BATCH06_DUPLICATE_DELEGATION_IDS": 0,
            "BATCH06_IDS_routing_spine": len(BATCH06_IDS),
            "BATCH06_REUSED_LINK_IDS": sorted(BATCH06_REUSED_LINK_IDS),
        },
        "locks": {
            "batch06_independent": 0,
            "progress_826": 179,
            "production_aligned_count": 0,
        },
        "counts": counts,
        "per_id": {str(r["id"]): r for r in rows},
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} — reused_link={counts['reused_link']} strangler={counts['strangler']}")


if __name__ == "__main__":
    main()
