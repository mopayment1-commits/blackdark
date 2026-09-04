#!/usr/bin/env python3
"""Generate Batch05 RTM baseline (IDs 201-250) from catalog + classification + acceptance."""

from __future__ import annotations

import asyncio
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs/BATCH05_RTM_201_250.json"
CLASSIFICATION = ROOT / "docs/BATCH05_CLASSIFICATION_INVEST_201_250.json"
ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"
CATALOG = ROOT / "docs/cap646/CAP646_CATALOG.json"
MECE_214_245 = ROOT / "docs/BATCH05_MECE_OVERLAP_214_245_DECISION.json"
MECE_OI_FUNDING = ROOT / "docs/BATCH05_MECE_OVERLAP_205_232_206_228_DECISION.json"

REUSED_LINK_BATCH01 = frozenset({214, 245})
REUSED_LINK_BATCH02 = frozenset({206, 228})
REUSED_LINK_INTERNAL = frozenset({232})
REUSED_LINK_ALL = REUSED_LINK_BATCH01 | REUSED_LINK_BATCH02 | REUSED_LINK_INTERNAL


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def git_branch() -> str:
    return subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()


def duplication_state(cid: int, acceptance: dict[str, Any]) -> str:
    if cid in REUSED_LINK_ALL:
        return "REUSED_LINK"
    if acceptance.get("status") == "REUSED-LINK":
        return "REUSED_LINK"
    return "DISTINCT"


def duplication_canonical(cid: int, acceptance: dict[str, Any]) -> str:
    if cid in REUSED_LINK_BATCH01:
        return acceptance.get("binding_file", "") + "::" + acceptance.get("binding_function", "")
    if cid in REUSED_LINK_BATCH02:
        return "cap646/batch02_production.py::cap_086"
    if cid in REUSED_LINK_INTERNAL:
        return "cap646/batch05_dedicated.py::_cap205"
    return f"cap646/batch05_dedicated.py::_cap{cid}"


async def runtime_probe(cap_id: int) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    return await execute_capability(cap_id, skip_entitlement=True, params={"symbol": "BTC", "tier": "pro"})


async def main() -> None:
    catalog = {r["id"]: r for r in json.loads(CATALOG.read_text(encoding="utf-8"))}
    cls_rows = {r["capability_id"]: r for r in json.loads(CLASSIFICATION.read_text(encoding="utf-8"))["rows"]}
    acceptance_rows = {r["capability_id"]: r for r in json.loads(ACCEPTANCE.read_text(encoding="utf-8"))["rows"]}

    commit = git_commit()
    rows: list[dict[str, Any]] = []

    for cap_id in range(201, 251):
        cat = catalog[cap_id]
        cls = cls_rows[cap_id]
        acc = acceptance_rows[cap_id]
        probe = await runtime_probe(cap_id)
        dup = duplication_state(cap_id, acc)
        spine = acc.get("production_spine", "batch05")
        if cap_id in REUSED_LINK_BATCH01:
            runtime_spine = "batch01"
        else:
            runtime_spine = probe.get("production_spine", "batch05")

        row = {
            "id": cap_id,
            "capability": cat["capability"],
            "gate1_state": "BROWNFIELD",
            "business_purpose": cat["capability"],
            "canonical_module_function": duplication_canonical(cap_id, acc),
            "canonical_route": f"/api/cap646/{cap_id}",
            "data_source_owner": (
                f"{cls.get('hero_module')}.{cls.get('hero_underlying')}"
                if cls.get("hero_module")
                else "NOT_VERIFIED"
            ),
            "acceptance_criteria": f"docs/BATCH05_ACCEPTANCE_201_250.json domain_rules for #{cap_id}",
            "expected_output_domain": acc.get("expected_surface", ""),
            "expected_surface_planned": acc.get("expected_surface"),
            "binding_file_planned": acc.get("binding_file"),
            "binding_function_planned": acc.get("binding_function"),
            "functional_completeness": "VERIFIED_LOCAL" if probe.get("success") else "NOT_VERIFIED",
            "functional_correctness": "VERIFIED_LOCAL" if probe.get("success") else "NOT_VERIFIED",
            "functional_appropriateness": "VERIFIED_LOCAL" if probe.get("success") else "NOT_VERIFIED",
            "duplication_state": dup,
            "duplication_compared": "hero-layer" if cls.get("split_brain") else "catalog",
            "duplication_canonical": duplication_canonical(cap_id, acc),
            "blocker": None,
            "blocker_type": None,
            "semantic_miswire": cls.get("hero_audit_classification") if cls.get("split_brain") else None,
            "evidence_path": f"cap646/batch05_dedicated.py + runtime probe @ {commit}",
            "evidence_commit": commit,
            "runtime_probe": {
                "success": probe.get("success"),
                "surface": probe.get("surface"),
                "production_spine": runtime_spine,
                "classification": probe.get("classification"),
                "closure_status": probe.get("closure_status"),
            },
            "hero_underlying": cls.get("hero_underlying"),
            "status": acc.get("status", "NOT_COMPLETE"),
            "production_spine": runtime_spine,
            "canonical_spine_acceptance": spine,
            "time_decision": acc.get("time_decision"),
            "build_decision": acc.get("build_decision"),
        }
        rows.append(row)

    reused = [r["id"] for r in rows if r["duplication_state"] == "REUSED_LINK"]
    closure = {
        "NOT_COMPLETE": sum(1 for r in rows if r["status"] == "NOT_COMPLETE"),
        "REUSED-LINK": sum(1 for r in rows if r["status"] == "REUSED-LINK"),
    }

    rtm = {
        "generated_at": datetime.now(UTC).isoformat(),
        "gate": "G1_BASELINE + MECE_OVERLAP_214_245 + MECE_OVERLAP_205_232_206_228",
        "branch": git_branch(),
        "commit": commit,
        "scope": "Batch05 IDs 201-250",
        "official_batch": "batch05",
        "batch05_independent": 0,
        "progress_826": 179,
        "build_phase": "OPEN",
        "mece_overlap_refs": [
            str(MECE_214_245.relative_to(ROOT)),
            str(MECE_OI_FUNDING.relative_to(ROOT)),
        ],
        "summary": {
            "total": 50,
            "gate1_state": {"BROWNFIELD": 50},
            "duplication_state": {
                "DISTINCT": 50 - len(reused),
                "REUSED_LINK": len(reused),
            },
            "reused_link": sorted(reused),
            "closure_status": closure,
            "production_aligned": 0,
        },
        "rows": rows,
    }

    OUT.write_text(json.dumps(rtm, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} — reused_link={len(reused)} NOT_COMPLETE={closure['NOT_COMPLETE']}")


if __name__ == "__main__":
    asyncio.run(main())
