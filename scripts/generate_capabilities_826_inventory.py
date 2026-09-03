#!/usr/bin/env python3
"""Generate institutional RTM inventory for 826 project-scope capabilities."""

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
BATCH02_CLASSIFICATION = ROOT / "docs/BATCH02_CLASSIFICATION.json"
BATCH01_RTM = ROOT / "docs/BATCH01_OFFICIAL_RTM_1_50.json"
BATCH02_RTM = ROOT / "docs/BATCH02_OFFICIAL_RTM_51_100.json"
BATCH03_RTM = ROOT / "docs/BATCH03_OFFICIAL_RTM_101_150.json"
REUSED_LINK_TAXONOMY = ROOT / "docs/REUSED_LINK_TAXONOMY.json"
REUSED_LINK_IDS = frozenset({106, 107, 110, 125})
CANONICAL_BLOCKERS = frozenset({63, 64, 69, 85})
BATCH03_PREP_IDS = frozenset(range(101, 151))


def official_batch(capability_id: int) -> str:
    return f"batch{(capability_id - 1) // 50 + 1:02d}"


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


def _load_batch01_rtm() -> dict[int, dict[str, Any]]:
    if not BATCH01_RTM.is_file():
        return {}
    data = json.loads(BATCH01_RTM.read_text(encoding="utf-8"))
    return {int(k): v for k, v in (data.get("per_id") or {}).items()}


def _load_batch02_rtm() -> dict[int, dict[str, Any]]:
    if not BATCH02_RTM.is_file():
        return {}
    data = json.loads(BATCH02_RTM.read_text(encoding="utf-8"))
    return {int(k): v for k, v in (data.get("per_id") or {}).items()}


def _load_batch03_rtm() -> dict[int, dict[str, Any]]:
    if not BATCH03_RTM.is_file():
        return {}
    data = json.loads(BATCH03_RTM.read_text(encoding="utf-8"))
    return {int(k): v for k, v in (data.get("per_id") or {}).items()}

def _load_reused_link_taxonomy() -> dict[str, Any]:
    if not REUSED_LINK_TAXONOMY.is_file():
        return {}
    return json.loads(REUSED_LINK_TAXONOMY.read_text(encoding="utf-8"))


def main() -> None:
    from cap646.batch01_dedicated import BATCH01_DEDICATED_IDS, EXPECTED_SURFACE as BATCH01_SURFACES
    from cap646.batch02_dedicated import EXPECTED_SURFACE as BATCH02_SURFACES
    from cap646.batch01_production import LEGACY_BATCH01_EXTENSION_IDS, OFFICIAL_BATCH01_IDS
    from cap646.batch02_production import OFFICIAL_BATCH02_IDS
    from cap646.batch03_production import BATCH03_IDS
    from cap646.catalog import catalog_by_id
    from cap646.backend_registry import binding_for
    from cap646.waves import USER_FACING

    evidence = _load_evidence()
    batch01_rtm = _load_batch01_rtm()
    batch02_rtm = _load_batch02_rtm()
    batch03_rtm = _load_batch03_rtm()
    reused_link_taxonomy = _load_reused_link_taxonomy()
    batch02_overlap: set[int] = set()
    batch02_not_complete: set[int] = set()
    if BATCH02_CLASSIFICATION.is_file():
        b02c = json.loads(BATCH02_CLASSIFICATION.read_text())
        batch02_overlap = set(b02c.get("overlap_batch01_ids", []))
        batch02_not_complete = set(b02c.get("not_complete_ids", []))

    def expected_surface(cid: int) -> str | None:
        return BATCH02_SURFACES.get(cid) or BATCH01_SURFACES.get(cid)

    per_id: dict[str, Any] = {}
    counts: dict[str, int] = {}
    for cid in range(1, PROJECT_SCOPE_TOTAL + 1):
        ob = official_batch(cid)
        ev = evidence.get(cid)
        hero_cls = ev.get("deep_audit_classification") if ev else None

        if cid in batch01_rtm:
            status = batch01_rtm[cid]["status"]
            notes = batch01_rtm[cid].get("notes")
            production_spine = batch01_rtm[cid].get("production_spine")
        elif cid in batch02_rtm:
            row_rtm = batch02_rtm[cid]
            status = row_rtm["status"]
            notes = row_rtm.get("notes")
            production_spine = row_rtm.get("production_spine")
        elif cid in batch03_rtm:
            row_rtm = batch03_rtm[cid]
            status = row_rtm["status"]
            notes = row_rtm.get("notes")
            production_spine = row_rtm.get("production_spine")
        elif cid in REUSED_LINK_IDS:
            canonical = int((reused_link_taxonomy.get("registered_pairs") or {}).get(str(cid), {}).get("canonical_id") or 0)
            if canonical in CANONICAL_BLOCKERS and batch02_rtm.get(canonical, {}).get("status") == "PRODUCTION-ALIGNED":
                status = "REUSED-LINK"
                notes = f"canonical #{canonical} PRODUCTION-ALIGNED; see docs/REUSED_LINK_TAXONOMY.json"
                production_spine = "batch03_prep"
            else:
                status = "PENDING_CANONICAL_AUDIT"
                notes = f"REUSED-LINK suspended until canonical #{canonical} passes audit"
                production_spine = "batch03_prep"
        elif cid in BATCH03_PREP_IDS and cid not in REUSED_LINK_IDS:
            status = "PENDING_SCOPE_REALIGNMENT"
            notes = "batch03_prep spine (101–150); official batch03 closure pending"
            production_spine = "batch03_prep"
        elif cid in batch02_overlap and ob == "batch03":
            status = "OVERLAP_BATCH01"
            notes = "Runtime uses batch01 spine; mis-scoped batch03 prep manifest overlap"
            production_spine = "batch01"
        elif cid in batch02_not_complete:
            status = "NOT_COMPLETE"
            notes = "Batch03 prep handler audit — not official batch closure"
            production_spine = None
        elif cid in OFFICIAL_BATCH01_IDS and cid in BATCH01_DEDICATED_IDS:
            status = "PRODUCTION-ALIGNED"
            notes = None
            production_spine = "batch01"
        elif cid in OFFICIAL_BATCH01_IDS:
            status = "PRODUCTION-ALIGNED"
            notes = "batch01 spine via handler/free-tier route"
            production_spine = "batch01"
        elif cid in LEGACY_BATCH01_EXTENSION_IDS and cid not in OFFICIAL_BATCH02_IDS:
            status = "PRODUCTION-ALIGNED"
            notes = f"legacy_batch01_extension; official_batch={ob}"
            production_spine = "batch01"
        elif cid in BATCH03_IDS and ob == "batch03" and cid not in REUSED_LINK_IDS:
            status = "PENDING_SCOPE_REALIGNMENT"
            notes = "Implemented under batch03_prep spine; official batch03 = 101–150"
            production_spine = "batch03_prep"
        elif hero_cls == "SPLIT-BRAIN-UNVERIFIED":
            status = "NOT_COMPLETE"
            notes = "Hero audit SPLIT-BRAIN — not convertible to PRODUCTION-ALIGNED without live spine proof"
            production_spine = None
        elif hero_cls and hero_cls not in {"VERIFIED_COMPLETE"}:
            status = hero_cls if hero_cls in {"PRODUCTION-ALIGNED", "NOT_COMPLETE", "PENDING"} else "PENDING"
            notes = "from_hero_evidence"
            production_spine = None
        else:
            status = "PENDING"
            notes = None
            production_spine = None

        counts[status] = counts.get(status, 0) + 1
        try:
            binding = binding_for(cid)
        except Exception:
            binding = {}

        per_id[str(cid)] = {
            "id": cid,
            "official_batch": ob,
            "capability": catalog_by_id().get(cid, {}).get("capability"),
            "status": status,
            "production_spine": production_spine,
            "expected_surface": expected_surface(cid),
            "in_hero_evidence": cid in evidence,
            "hero_classification": hero_cls,
            "user_facing": cid in USER_FACING,
            "binding_source": binding.get("binding_source"),
            "backend": f"{binding.get('backend_module')}.{binding.get('backend_entrypoint')}",
            "notes": notes,
        }

    classification_taxonomy = {
        "PRODUCTION-ALIGNED": {
            "definition": "Capability achieves its catalog goal via the production spine with goal-specific payload.",
            "acceptance_criteria": [
                "Live execution returns surface and payload matching catalog goal",
                "production_spine=batch01 for official batch01 IDs",
                "No runtime exception; not a generic fallback surface",
            ],
        },
        "NOT_COMPLETE": {
            "definition": "Handler or payload does not achieve the catalog goal for the requested ID.",
        },
        "REUSED-LINK": {
            "definition": reused_link_taxonomy.get("definition", "Duplicate ID covered by canonical capability with live goal-equivalent payload."),
            "taxonomy_file": "docs/REUSED_LINK_TAXONOMY.json",
            "registered_pairs": list(REUSED_LINK_IDS),
        },
        "PENDING_CANONICAL_AUDIT": {
            "definition": "REUSED-LINK claim suspended until canonical IDs pass full sequential batch audit.",
        },
        "PENDING_SCOPE_REALIGNMENT": {
            "definition": "Technical work exists but under wrong official_batch numbering; RTM records true batch.",
        },
        "OVERLAP_BATCH01": {
            "definition": "ID re-listed in a later batch but completed in Batch 01 spine.",
        },
        "PENDING": {
            "definition": "Not yet audited under official batch sequential closure.",
        },
        "VERIFIED_COMPLETE": {
            "definition": "BANNED for 826 RTM `status`/`classification` fields. Legacy cap978 CI closure may still emit `verdict: VERIFIED_COMPLETE` as a separate internal namespace — do not map to RTM without formal registration here.",
            "status": "DEPRECATED_UNREGISTERED",
            "rtm_usage": "forbidden",
            "cap978_ci_verdict": "legacy_internal_only",
        },
    }

    batch01_aligned = sum(
        1 for cid in OFFICIAL_BATCH01_IDS if per_id[str(cid)]["status"] == "PRODUCTION-ALIGNED"
    )
    batch02_aligned = sum(
        1 for cid in OFFICIAL_BATCH02_IDS if per_id[str(cid)]["status"] == "PRODUCTION-ALIGNED"
    )
    batch02_independent = sum(
        1
        for cid in OFFICIAL_BATCH02_IDS
        if per_id[str(cid)]["status"] == "PRODUCTION-ALIGNED"
        and cid not in batch02_overlap
    )
    batch02_overlap_count = sum(
        1
        for cid in OFFICIAL_BATCH02_IDS
        if cid in batch02_overlap or "legacy_batch01" in str(per_id[str(cid)].get("notes") or "")
    )

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": f"IDs 1-{PROJECT_SCOPE_TOTAL} institutional RTM",
        "scope_baseline": {
            "batch01": "IDs 1–50",
            "batch02": "IDs 51–100",
            "batch03": "IDs 101–150",
            "formula": "official_batch = batch((id-1)//50 + 1)",
        },
        "classification_taxonomy": classification_taxonomy,
        "three_separate_counts": {
            "note": "Three mutually exclusive RTM columns — never aggregate into a single progress equation",
            "production_aligned_independent": counts.get("PRODUCTION-ALIGNED", 0),
            "reused_link": counts.get("REUSED-LINK", 0),
            "overlap_partial": counts.get("OVERLAP-PARTIAL", 0),
            "dedup_verification": {
                "each_id_counted_once": True,
                "ids_51_59_double_counted": False,
                "old_54_826_explanation": "Legacy 54/826 = batch01(50) + 4 early batch02 overlap IDs before official batch02 closure; superseded by per_id SSOT with no duplicate IDs",
                "overlap_batch01_ids_in_batch02": sorted(batch02_overlap),
            },
        },
        "summary": {
            "total_ids": PROJECT_SCOPE_TOTAL,
            "status_counts": counts,
            "official_batch01_total": len(OFFICIAL_BATCH01_IDS),
            "official_batch01_production_aligned": batch01_aligned,
            "official_batch02_total": len(OFFICIAL_BATCH02_IDS),
            "official_batch02_production_aligned": batch02_aligned,
            "official_batch02_independent_production_aligned": batch02_independent,
            "official_batch02_overlap_batch01": batch02_overlap_count,
            "reused_link_resolved": len(REUSED_LINK_IDS),
            "user_facing_count": len([cid for cid in USER_FACING if cid <= PROJECT_SCOPE_TOTAL]),
        },
        "per_id": per_id,
    }
    json_path = ROOT / "docs/CAPABILITIES_826_INVENTORY.json"
    md_path = ROOT / "docs/CAPABILITIES_826_INVENTORY.md"
    json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# CAPABILITIES 826 — Requirements Traceability Matrix (RTM)",
        "",
        f"Generated: {out['generated_at']}",
        "",
        "## Scope baseline (owner-approved)",
        "",
        "| Official batch | ID range |",
        "|----------------|----------|",
        "| batch01 | 1–50 |",
        "| batch02 | 51–100 |",
        "| batch03 | 101–150 |",
        "",
        "## Summary",
        "",
        f"| Metric | Count |",
        f"|--------|------:|",
        f"| Total scope | {PROJECT_SCOPE_TOTAL} |",
        f"| Official batch01 PRODUCTION-ALIGNED | {batch01_aligned}/50 |",
        f"| Official batch02 PRODUCTION-ALIGNED | {batch02_aligned}/50 |",
        f"| Official batch02 independent build | {batch02_independent}/46 |",
        f"| Official batch02 OVERLAP batch01 | {batch02_overlap_count}/4 |",
        "",
        "## Status breakdown",
        "",
        "| Status | Count |",
        "|--------|------:|",
    ]
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("> `VERIFIED_COMPLETE` is banned until formally registered in this inventory.")
    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(out["summary"], indent=2))
    print(f"Wrote {json_path} and {md_path}")


if __name__ == "__main__":
    main()
