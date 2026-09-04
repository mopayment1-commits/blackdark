#!/usr/bin/env python3
"""Generate full Batch05 pre-build classification matrix (IDs 201–250)."""

from __future__ import annotations

import json
import subprocess
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = {r["id"]: r for r in json.loads((ROOT / "docs/cap646/CAP646_CATALOG.json").read_text())}
INVEST = {
    r["capability_id"]: r
    for r in json.loads((ROOT / "docs/BATCH05_CLASSIFICATION_INVEST_201_250.json").read_text())["rows"]
}

DUPLICATE_DELEGATION = {212: {"canonical_id": 17, "canonical_spine": "batch01", "adr": "docs/ADR_BATCH05_212_DUPLICATE_DELEGATION_BATCH01.md"}}
REUSED_LINK = {
    214: {"canonical_id": 214, "canonical_spine": "batch01", "adr": "docs/ADR_BATCH05_214_245_REUSED_LINK_BATCH01.md", "mece": "docs/BATCH05_MECE_OVERLAP_214_245_DECISION.json"},
    245: {"canonical_id": 245, "canonical_spine": "batch01", "adr": "docs/ADR_BATCH05_214_245_REUSED_LINK_BATCH01.md", "mece": "docs/BATCH05_MECE_OVERLAP_214_245_DECISION.json"},
    206: {"canonical_id": 86, "canonical_spine": "batch02", "adr": "docs/ADR_BATCH05_206_228_REUSED_LINK_BATCH02.md", "mece": "docs/BATCH05_MECE_OVERLAP_205_232_206_228_DECISION.json"},
    228: {"canonical_id": 86, "canonical_spine": "batch02", "adr": "docs/ADR_BATCH05_206_228_REUSED_LINK_BATCH02.md", "mece": "docs/BATCH05_MECE_OVERLAP_205_232_206_228_DECISION.json"},
    226: {"canonical_id": 69, "canonical_spine": "batch02", "adr": "docs/ADR_BATCH05_226_REUSED_LINK_BATCH02.md", "mece": "docs/BATCH05_MECE_OVERLAP_226_69_DECISION.json"},
    232: {"canonical_id": 205, "canonical_spine": "batch05", "adr": "docs/ADR_BATCH05_232_REUSED_LINK_205.md", "mece": "docs/BATCH05_MECE_OVERLAP_205_232_206_228_DECISION.json"},
}


def _git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def _classification(cid: int, inv: dict) -> str:
    lifecycle = inv.get("lifecycle_12207", "Brownfield")
    if lifecycle == "Greenfield":
        return "Greenfield"
    audit = inv.get("hero_audit_classification", "")
    if audit == "DEFERRED-EARLY-BATCH" and not inv.get("hero_underlying"):
        return "Stub-Template"
    return "Brownfield"


def _time_decision(cid: int) -> str:
    if cid in DUPLICATE_DELEGATION or cid in REUSED_LINK:
        return "Migrate"
    return "Invest"


def _closure_status(cid: int) -> str:
    if cid in DUPLICATE_DELEGATION:
        return "DUPLICATE_DELEGATION"
    if cid in REUSED_LINK:
        return "REUSED-LINK"
    return "NOT_COMPLETE"


def _build_decision(classification: str, closure: str) -> str:
    if closure == "DUPLICATE_DELEGATION":
        return "Preserve runtime duplicate delegation — exclude from batch05 routing spine"
    if closure == "REUSED-LINK":
        return "Strangler facade — REUSED-LINK to canonical spine; no parallel implementation"
    if classification == "Stub-Template":
        return "Strangler — replace generic stub with catalog-faithful payload"
    return "Strangler — complete delegated path or rebuild dedicated handler"


def _row(cid: int) -> dict:
    cat = CATALOG[cid]
    inv = INVEST.get(cid, {})
    classification = _classification(cid, inv)
    closure = _closure_status(cid)
    time_decision = _time_decision(cid)
    hero = inv.get("hero_underlying")
    hero_mod = inv.get("hero_module")
    evidence_parts = []
    if hero:
        evidence_parts.append(f"hero={hero_mod}.{hero}" if hero_mod else f"hero={hero}")
    if inv.get("split_brain"):
        evidence_parts.append("Type-4 SPLIT-BRAIN until strangler wired")
    if inv.get("legacy_test_file"):
        evidence_parts.append(f"legacy_test={inv['legacy_test_file']}")
    if cid in DUPLICATE_DELEGATION:
        link = DUPLICATE_DELEGATION[cid]
        evidence_parts.append(f"gap_matrix DUPLICATE→#{link['canonical_id']}; batch05_ids exclusion")
    if cid in REUSED_LINK:
        link = REUSED_LINK[cid]
        evidence_parts.append(f"REUSED-LINK→{link['canonical_spine']} #{link['canonical_id']}")

    row: dict = {
        "id": cid,
        "capability": cat["capability"],
        "track": cat["track"],
        "classification": classification,
        "evidence": "; ".join(evidence_parts) or "catalog row batch05 — strangler spine pending",
        "decision_justification": (
            "Strangler Fig — hero data wrapped in catalog-aligned surface; PA review deferred under OPEN"
            if classification == "Brownfield"
            else "ISO 25010 appropriateness not met — Strangler Fig stub until catalog-faithful payload"
            if classification == "Stub-Template"
            else "No hero predecessor — discovery spike required before strangler wiring"
        ),
        "rtm_status": closure if closure != "NOT_COMPLETE" else "NOT_COMPLETE",
        "closure_status": closure,
        "hero_underlying": hero,
        "build_decision": _build_decision(classification, closure),
        "time_decision": time_decision,
        "time_justification": (
            "Preserve pre-batch05 duplicate delegation; eliminate batch05 spine override"
            if closure == "DUPLICATE_DELEGATION"
            else "Facade to canonical spine — eliminate wrong-domain hero from production path"
            if closure == "REUSED-LINK"
            else "Bounded strangler Invest — wire catalog surface over brownfield hero/backend"
        ),
        "owner_decision": None,
        "duplicate_candidates": [],
        "production_aligned": False,
    }
    if cid in DUPLICATE_DELEGATION:
        row["duplicate_of"] = DUPLICATE_DELEGATION[cid]["canonical_id"]
        row["adr_ref"] = DUPLICATE_DELEGATION[cid]["adr"]
    if cid in REUSED_LINK:
        link = REUSED_LINK[cid]
        row["canonical_capability_id"] = link["canonical_id"]
        row["canonical_spine"] = link["canonical_spine"]
        row["adr_ref"] = link["adr"]
        row["mece_ref"] = link["mece"]
    return row


def main() -> None:
    commit = _git_head()
    matrix = [_row(cid) for cid in range(201, 251)]
    class_counts = Counter(r["classification"] for r in matrix)
    closure_counts = Counter(r["closure_status"] for r in matrix)
    time_counts = Counter(r["time_decision"] for r in matrix)

    out = {
        "generated_at": datetime.now(UTC).isoformat(),
        "commit": commit,
        "branch": "cursor/batch05-201-250-e85e",
        "pr": 366,
        "scope": "Batch05 Pre-Build Classification Matrix IDs 201-250 (full backfill)",
        "standard": "ISO/IEC/IEEE 12207 Phase A + Strangler Fig + Gartner TIME",
        "build_phase": "OPEN",
        "policy": "No implementation may proceed without a row in this matrix. Brownfield default = Strangler Fig.",
        "routing_lock": {
            "BATCH05_MANIFEST_IDS": 50,
            "BATCH05_DUPLICATE_DELEGATION_IDS": [212],
            "BATCH05_IDS_routing_spine": 49,
        },
        "summary": {
            "total": 50,
            "classification": dict(class_counts),
            "closure_status": dict(closure_counts),
            "time_decision": dict(time_counts),
            "not_complete_strangler": closure_counts.get("NOT_COMPLETE", 0),
            "reused_link": closure_counts.get("REUSED-LINK", 0),
            "duplicate_delegation": closure_counts.get("DUPLICATE_DELEGATION", 0),
            "batch05_independent": 0,
            "production_aligned": 0,
            "progress_826": 179,
        },
        "supersedes_partial": "docs/BATCH05_PREBUILD_CLASSIFICATION_212_226.json",
        "matrix": matrix,
    }
    path = ROOT / "docs/BATCH05_PREBUILD_CLASSIFICATION_201_250.json"
    path.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path} ({len(matrix)} rows)")
    print("classification:", dict(class_counts))
    print("closure:", dict(closure_counts))


if __name__ == "__main__":
    main()
