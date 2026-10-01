#!/usr/bin/env python3
"""Generate per-ID PA closure registry for Batch04 (151-200).

Documents candidacy and blockers — does NOT promote any ID to PRODUCTION-ALIGNED.
batch04_independent remains 0 until owner-approved PA records exist.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
PENTAGONAL = ROOT / "docs/BATCH04_PENTAGONAL_TEMPLATE_151_200.json"
ACCEPTANCE = ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json"
OUT = ROOT / "docs/BATCH04_PA_CLOSURE_REGISTRY.json"

CUSTOM_HANDLER_IDS = frozenset({151, 152, 153, 156, 159, 161, 162, 183, 189})
OVERLAP_BATCH01 = frozenset({175})
PENDING_CANONICAL = frozenset({159, 183})
CATALOG_TEMPLATE_IDS = frozenset(range(151, 201)) - CUSTOM_HANDLER_IDS - OVERLAP_BATCH01


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def pa_phase(cid: int) -> str:
    if cid in OVERLAP_BATCH01:
        return "OVERLAP-PARTIAL"
    if cid in PENDING_CANONICAL:
        return "PENDING_CANONICAL_AUDIT"
    if cid in CATALOG_TEMPLATE_IDS:
        return "CANDIDATE_DEFERRED"
    return "CANDIDATE_REVIEW"


def pa_eligible(cid: int, domain_all_pass: bool) -> bool:
    if cid in OVERLAP_BATCH01 or cid in PENDING_CANONICAL:
        return False
    if cid in CATALOG_TEMPLATE_IDS:
        return False
    return domain_all_pass


def functional_gap_note(cid: int) -> str | None:
    if cid in CATALOG_TEMPLATE_IDS:
        return "catalog_template_stub — ok+feature_ref only; ISO 25010 appropriateness not met"
    if cid == 159:
        return "BLOCKER-159-103 — canonical #103 PENDING_SCOPE_REALIGNMENT"
    if cid == 183:
        return "BLOCKER-183-130 — semantic gap whale≠mindshare; canonical #130 not PA"
    if cid == 175:
        return "OVERLAP-PARTIAL — batch01 sentiment_ai; excluded from batch04_independent"
    if cid == 156:
        return "PARTIAL_MISNAMED — asset_registry seed used as knowledge-graph proxy"
    return None


def build_registry() -> dict[str, Any]:
    pent = json.loads(PENTAGONAL.read_text(encoding="utf-8"))
    acc = {r["capability_id"]: r for r in json.loads(ACCEPTANCE.read_text(encoding="utf-8"))["rows"]}
    rows: list[dict[str, Any]] = []

    for prow in sorted(pent["rows"], key=lambda r: r["capability_id"]):
        cid = prow["capability_id"]
        er = prow["pentagonal"]["external_result_iso29148"]
        domain_all_pass = er["all_pass"]
        phase = pa_phase(cid)
        eligible = pa_eligible(cid, domain_all_pass)
        gap = functional_gap_note(cid) or acc[cid].get("functional_gap")

        rows.append(
            {
                "capability_id": cid,
                "capability_name": prow["capability_name"],
                "pa_closure_phase": phase,
                "pa_eligible": eligible,
                "closure_status": "NOT_COMPLETE" if cid not in OVERLAP_BATCH01 else "OVERLAP-PARTIAL",
                "production_aligned": False,
                "domain_rules_passed": er["rules_passed"],
                "domain_rules_total": er["rules_total"],
                "domain_all_pass": domain_all_pass,
                "functional_gap": gap if isinstance(gap, str) else gap,
                "blocker": prow.get("pending_canonical_audit"),
                "production_spine": prow["probe"].get("production_spine"),
                "next_action": (
                    "Owner: resolve BLOCKER or DISTINCT ADR"
                    if cid in PENDING_CANONICAL
                    else "Implement catalog-faithful payload beyond template stub"
                    if cid in CATALOG_TEMPLATE_IDS
                    else "Complete 25010 appropriateness review + pentagonal sign-off"
                    if phase == "CANDIDATE_REVIEW"
                    else "N/A — batch01 overlap"
                ),
            }
        )

    eligible_count = sum(1 for r in rows if r["pa_eligible"])
    review_count = sum(1 for r in rows if r["pa_closure_phase"] == "CANDIDATE_REVIEW")
    deferred_count = sum(1 for r in rows if r["pa_closure_phase"] == "CANDIDATE_DEFERRED")

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "scope": "Batch04 PA closure registry IDs 151-200",
        "build_phase": "OPEN",
        "batch04_independent": 0,
        "progress_826": 148,
        "production_aligned_count": 0,
        "summary": {
            "pa_eligible_now": eligible_count,
            "candidate_review": review_count,
            "candidate_deferred_template": deferred_count,
            "pending_canonical_audit": len(PENDING_CANONICAL),
            "overlap_partial": len(OVERLAP_BATCH01),
        },
        "policy": (
            "domain_rules pass is necessary but NOT sufficient for PA. "
            "No ID promoted to PRODUCTION-ALIGNED in this registry."
        ),
        "rows": rows,
    }


def main() -> None:
    doc = build_registry()
    assert len(doc["rows"]) == 50
    assert doc["batch04_independent"] == 0
    assert doc["production_aligned_count"] == 0
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT} — eligible={doc['summary']['pa_eligible_now']} "
        f"review={doc['summary']['candidate_review']} deferred={doc['summary']['candidate_deferred_template']}"
    )


if __name__ == "__main__":
    main()
