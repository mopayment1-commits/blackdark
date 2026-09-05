#!/usr/bin/env python3
"""Generate Batch06 pre-build classification matrix (IDs 251–300)."""

from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cap646.batch06_dedicated import BATCH06_REUSED_LINK_IDS, EXPECTED_SURFACE, _REUSED_LINK_CATALOG  # noqa: E402
from cap646.batch06_ids import BATCH06_IDS, BATCH06_MANIFEST_IDS  # noqa: E402

CATALOG = ROOT / "docs/cap646/CAP646_CATALOG.json"
GAP = ROOT / "docs/cap646/CAP646_GAP_MATRIX.json"
MODULE_MAP = ROOT / "docs/cap646/CAP646_MODULE_MAP.json"
AUDIT = ROOT / "docs/RETROSPECTIVE_DEEP_AUDIT_BATCH_03_201_300.json"
OUT = ROOT / "docs/BATCH06_PREBUILD_CLASSIFICATION_251_300.json"


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _git_branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()


def _load_indexed(path: Path) -> dict[int, dict]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    rows = doc["rows"] if isinstance(doc, dict) and "rows" in doc else doc
    return {int(r["id" if "id" in r else "capability_id"]): r for r in rows}


def _classify(cid: int, gap: dict, module: dict | None, audit: dict) -> str:
    if cid in BATCH06_REUSED_LINK_IDS:
        return "DUPLICATE_ALIAS"
    gap_class = gap.get("final_classification", "")
    if gap_class == "DUPLICATE/ALREADY_COVERED":
        return "DUPLICATE_ALIAS"
    if gap_class == "PARTIALLY_IMPLEMENTED" or (module and gap_class != "NOT_IMPLEMENTED"):
        return "PARTIAL_CANONICAL"
    if gap_class == "NOT_IMPLEMENTED" and not gap.get("existing_code_components") and not audit.get("underlying_function"):
        return "GREENFIELD"
    if audit.get("underlying_function") or audit.get("classification") == "SPLIT-BRAIN-UNVERIFIED":
        return "BROWNFIELD"
    if module:
        return "PARTIAL_CANONICAL"
    return "GREENFIELD"


def _closure_status(cid: int) -> str:
    if cid in BATCH06_REUSED_LINK_IDS:
        return "REUSED-LINK"
    return "NOT_COMPLETE"


def _time_decision(cid: int) -> str:
    return "Migrate" if cid in BATCH06_REUSED_LINK_IDS else "Invest"


def _build_decision(classification: str, closure: str) -> str:
    if closure == "REUSED-LINK":
        return "Strangler facade — REUSED-LINK to canonical spine; no parallel implementation"
    if classification == "GREENFIELD":
        return "Strangler — discovery spike then catalog-faithful dedicated handler"
    if classification == "PARTIAL_CANONICAL":
        return "Strangler — wrap module_map / partial backend in catalog-aligned surface"
    if classification == "DUPLICATE_ALIAS":
        return "Migrate — facade only; eliminate wrong-domain hero from production path"
    return "Strangler — complete delegated path or rebuild dedicated handler"


def _row(cid: int, catalog: dict, gap: dict, module: dict | None, audit: dict) -> dict:
    cat = catalog[cid]
    classification = _classify(cid, gap, module, audit)
    closure = _closure_status(cid)
    evidence_parts = [f"expected_surface={EXPECTED_SURFACE.get(cid)}"]
    if audit.get("underlying_module") and audit.get("underlying_function"):
        evidence_parts.append(f"hero={audit['underlying_module']}.{audit['underlying_function']}")
    if audit.get("split_brain_routing"):
        evidence_parts.append("Type-4 SPLIT-BRAIN until strangler wired")
    if gap.get("final_classification"):
        evidence_parts.append(f"gap_matrix={gap['final_classification']}")
    if module:
        evidence_parts.append(
            f"module_map={module['backend_module']}.{module['backend_entrypoint']}"
        )
    if cid in BATCH06_REUSED_LINK_IDS:
        link = _REUSED_LINK_CATALOG[cid]
        evidence_parts.append(
            f"REUSED-LINK→{link['canonical_spine']} #{link['canonical_capability_id']}"
        )

    row: dict = {
        "id": cid,
        "capability": cat["capability"],
        "track": cat["track"],
        "classification": classification,
        "evidence": "; ".join(evidence_parts),
        "decision_justification": (
            "REUSED-LINK — canonical spine facade; no independent batch06 implementation"
            if closure == "REUSED-LINK"
            else "Strangler Fig — catalog surface over brownfield/module_map backend"
            if classification in {"BROWNFIELD", "PARTIAL_CANONICAL"}
            else "No hero predecessor — bounded strangler Invest required"
        ),
        "rtm_status": closure,
        "closure_status": closure,
        "hero_underlying": audit.get("underlying_function"),
        "hero_module": audit.get("underlying_module"),
        "build_decision": _build_decision(classification, closure),
        "time_decision": _time_decision(cid),
        "time_justification": (
            "Facade to canonical spine — eliminate wrong-domain hero from production path"
            if closure == "REUSED-LINK"
            else "Bounded strangler Invest — wire catalog surface over backend"
        ),
        "owner_decision": None,
        "duplicate_candidates": [],
        "production_aligned": False,
        "expected_surface": EXPECTED_SURFACE.get(cid),
    }
    if cid in BATCH06_REUSED_LINK_IDS:
        link = _REUSED_LINK_CATALOG[cid]
        row["canonical_capability_id"] = link["canonical_capability_id"]
        row["canonical_spine"] = link["canonical_spine"]
        row["binding"] = link["binding"]
        if link.get("alias_of"):
            row["alias_of"] = link["alias_of"]
    return row


def main() -> None:
    raw_catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    catalog = (
        {int(r["id"]): r for r in raw_catalog}
        if isinstance(raw_catalog, list)
        else {int(r["id"]): r for r in raw_catalog.get("capabilities", [])}
    )
    gap = _load_indexed(GAP)
    module_map = _load_indexed(MODULE_MAP)
    audit_rows = _load_indexed(AUDIT)

    matrix = [_row(cid, catalog, gap.get(cid, {}), module_map.get(cid), audit_rows.get(cid, {})) for cid in range(251, 301)]
    class_counts = Counter(r["classification"] for r in matrix)
    closure_counts = Counter(r["closure_status"] for r in matrix)
    time_counts = Counter(r["time_decision"] for r in matrix)

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "commit": _git_head(),
        "branch": _git_branch(),
        "scope": "Batch06 Pre-Build Classification Matrix IDs 251-300",
        "standard": "ISO/IEC/IEEE 12207 Phase A + Strangler Fig + Gartner TIME",
        "build_phase": "OPEN",
        "policy": "No implementation may proceed without a row in this matrix. REUSED-LINK = DUPLICATE_ALIAS.",
        "routing_lock": {
            "BATCH06_MANIFEST_IDS": len(BATCH06_MANIFEST_IDS),
            "BATCH06_DUPLICATE_DELEGATION_IDS": 0,
            "BATCH06_IDS_routing_spine": len(BATCH06_IDS),
            "BATCH06_REUSED_LINK_IDS": sorted(BATCH06_REUSED_LINK_IDS),
            "strangler_count": 50 - len(BATCH06_REUSED_LINK_IDS),
        },
        "summary": {
            "total": 50,
            "classification": dict(class_counts),
            "closure_status": dict(closure_counts),
            "time_decision": dict(time_counts),
            "not_complete_strangler": closure_counts.get("NOT_COMPLETE", 0),
            "reused_link": closure_counts.get("REUSED-LINK", 0),
            "batch06_independent": 0,
            "production_aligned": 0,
            "progress_826": 179,
        },
        "matrix": matrix,
    }
    OUT.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(matrix)} rows)")
    print("classification:", dict(class_counts))
    print("closure:", dict(closure_counts))


if __name__ == "__main__":
    main()
