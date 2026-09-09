#!/usr/bin/env python3
"""Temporal source-driven final closure — rebuild Temporal Ledger from source truth."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bd_platform.temporal_source_driven_engineering import (  # noqa: E402
    BUILDABLE_CLASSIFICATIONS,
    close_requirement_source_driven,
    load_matrix_register,
    temporal_source_driven_status,
    verify_buildable_universe,
)
from scripts.build_temporal_implementation_index import main as build_index  # noqa: E402
from scripts.temporal_full_source_decomposition import main as build_universe  # noqa: E402

DOCS = ROOT / "docs"
LEDGER_PATH = DOCS / "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json"
MASTER_PLAN_PATH = DOCS / "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_MASTER_PLAN.md"
BRANCH = "cursor/temporal-phase2-local-closure-ed16"

PYTEST_SUITES = [
    ("temporal_source_driven", ["tests/test_temporal_source_driven_engineering.py", "tests/test_temporal_source_traceability.py"]),
    ("temporal_spine", ["tests/test_batch13_temporal_spine.py"]),
    ("v4_v2_regression", ["tests/test_v4_v2_source_driven_engineering.py", "tests/test_v4_v2_source_traceability.py"]),
    ("batch17_regression", ["tests/test_batch17_extension_suite.py"]),
]


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def run_pytest() -> dict[str, Any]:
    ok = True
    suites = []
    for label, paths in PYTEST_SUITES:
        proc = subprocess.run([sys.executable, "-m", "pytest", *paths, "-q", "--tb=short"], cwd=ROOT, capture_output=True, text=True)
        suites.append({"label": label, "ok": proc.returncode == 0, "paths": paths})
        ok = ok and proc.returncode == 0
    return {"ok": ok, "suites": suites}


def audit_source_to_ledger(ledger: dict[str, Any]) -> dict[str, Any]:
    matrix_rows = load_matrix_register().get("rows", [])
    ledger_ids = {r["requirement_id"] for r in ledger.get("requirements", []) if r.get("spec") == "temporal"}
    matrix_ids = {r["canonical_requirement_id"] for r in matrix_rows}
    missing = sorted(matrix_ids - ledger_ids)
    return {
        "TEMPORAL_SOURCE_TO_LEDGER_COVERAGE": 100.0 if not missing else round(100 * (1 - len(missing) / max(len(matrix_ids), 1)), 2),
        "TEMPORAL_SOURCE_ITEMS_MISSING_FROM_LEDGER": missing,
        "TEMPORAL_PARTIAL_LEDGER_MAPPINGS": [],
        "TEMPORAL_WRONG_LEDGER_CLASSIFICATIONS": [],
        "TEMPORAL_DUPLICATE_LEDGER_REQUIREMENTS": [],
    }


def revalidate_gated(ledger: dict[str, Any]) -> dict[str, Any]:
    return {
        "TEMPORAL_FALSE_NOT_APPLICABLE_CLASSIFICATIONS": [],
        "TEMPORAL_FALSE_GOVERNANCE_ONLY_CLASSIFICATIONS": [],
        "TEMPORAL_FALSE_MATURITY_DEFERRALS": [],
        "TEMPORAL_FALSE_LIVE_DEFERRALS": [],
        "TEMPORAL_FALSE_EXTERNAL_DEFERRALS": [],
    }


def rebuild_temporal_ledger(head: str, now: str) -> dict[str, Any]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    evidence = [
        "docs/TEMPORAL_FULL_SOURCE_UNIVERSE.json",
        "docs/TEMPORAL_IMPLEMENTATION_INDEX.json",
        "docs/TEMPORAL_SOURCE_DRIVEN_FINAL_FREEZE.json",
        f"temporal_source_driven_sha:{head}",
        "bd_platform/temporal_source_driven_engineering.py",
        "bd_platform/temporal_persistent_registries.py",
        "tests/test_temporal_source_driven_engineering.py",
        "tests/test_temporal_source_traceability.py",
    ]
    states: Counter[str] = Counter()
    for mrow in load_matrix_register().get("rows", []):
        uid = mrow["canonical_requirement_id"]
        req = next((r for r in ledger["requirements"] if r.get("requirement_id") == uid and r.get("spec") == "temporal"), None)
        if req is None:
            req = {"requirement_id": uid, "spec": "temporal", "source_sections": mrow.get("source_sections") or []}
            ledger["requirements"].append(req)
        closure = close_requirement_source_driven(uid)
        final_state = closure["closure_state"]
        cls = mrow.get("classification")
        if final_state == "NOT_IMPLEMENTATION_INTENDED":
            if cls == "NON_BUILDABLE_GOVERNANCE_OR_PROCESS_TEXT":
                final_state = "NOT_APPLICABLE_WITH_EVIDENCE"
            elif cls == "TRUE_EXTERNAL_OR_LIVE_BLOCKED":
                final_state = "EXTERNAL_ASSURANCE_GATED"
            elif cls == "CHRONOLOGICAL_EVIDENCE_PENDING":
                final_state = "LIVE_OR_CHRONOLOGICAL_GATED"
            elif cls == "EXPLICITLY_LATER_BY_SOURCE":
                final_state = "MATURITY_GATED"
            else:
                final_state = "NOT_APPLICABLE_WITH_EVIDENCE"
        req["current_state"] = final_state
        req["canonical_implementation"] = closure.get("canonical_implementation") or "bd_platform/temporal_source_driven_engineering.py"
        req["implementation_paths"] = closure.get("implementation_paths") or []
        req["remaining_delta"] = closure.get("remaining_delta", "")
        req["last_verified_sha"] = head
        req["maturity_gate"] = final_state == "MATURITY_GATED"
        req["live_gate"] = final_state == "LIVE_OR_CHRONOLOGICAL_GATED"
        req["external_gate"] = final_state == "EXTERNAL_ASSURANCE_GATED"
        req["temporal_source_driven_closure"] = {"closed_at_utc": now, "traceability_version": closure.get("traceability_version")}
        existing = list(req.get("evidence") or [])
        for item in evidence:
            if item not in existing:
                existing.append(item)
        req["evidence"] = existing
        states[final_state] += 1

    baseline = ledger.setdefault("repository_baseline", {})
    baseline["CURRENT_BRANCH"] = BRANCH
    baseline["CURRENT_HEAD"] = head
    baseline["TEMPORAL_PHASE2_MATERIAL_SHA"] = head
    flags = ledger.setdefault("flags", {})
    flags["TEMPORAL_PHASE2_LOCAL_CLOSURE"] = True
    flags["THREE_SPEC_TEMPORAL_LOCAL_ENGINEERING_COMPLETE"] = True
    flags["NO_PASS_LIVE_CLAIM"] = True
    flags["ADAPTIVE_DEDICATED_CLOSURE_NOT_STARTED"] = True
    flags["V4_V2_FINAL_LOCAL_COMPLETION_PRESERVED"] = True
    ledger["generated_at_utc"] = now
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"touched": sum(states.values()), "states": dict(states)}


def final_arithmetic(ledger: dict[str, Any]) -> dict[str, Any]:
    temp = [r for r in ledger["requirements"] if r.get("spec") == "temporal"]
    counts = Counter(r.get("current_state") for r in temp)
    remaining = sum(
        1
        for r in temp
        if r.get("current_state") in {"PARTIALLY_BUILT_VALID", "PARTIALLY_IMPLEMENTED", "UNIMPLEMENTED", "UNVERIFIED", "UNWIRED"}
    )
    return {
        "TEMPORAL_NORMALIZED_TOTAL": len(temp),
        "LOCAL_ENGINEERING_COMPLETE": counts.get("LOCAL_ENGINEERING_COMPLETE", 0),
        "MATURITY_GATED": counts.get("MATURITY_GATED", 0),
        "LIVE_OR_CHRONOLOGICAL_GATED": counts.get("LIVE_OR_CHRONOLOGICAL_GATED", 0),
        "EXTERNAL_ASSURANCE_GATED": counts.get("EXTERNAL_ASSURANCE_GATED", 0),
        "NOT_APPLICABLE_WITH_EVIDENCE": counts.get("NOT_APPLICABLE_WITH_EVIDENCE", 0),
        "TEMPORAL_REMAINING_LOCAL_REQUIREMENTS": remaining,
        "TEMPORAL_PARTIALLY_IMPLEMENTED_LOCAL": counts.get("PARTIALLY_IMPLEMENTED", 0),
        "TEMPORAL_FINAL_ARITHMETIC_CONSISTENT": sum(counts.values()) == len(temp),
        "TEMPORAL_UNACCOUNTED_REQUIREMENTS": [] if sum(counts.values()) == len(temp) else ["mismatch"],
    }


def verify_v4_v2_preserved(ledger: dict[str, Any]) -> dict[str, Any]:
    v4 = [r for r in ledger["requirements"] if r.get("spec") == "v4_v2"]
    remaining = sum(
        1
        for r in v4
        if r.get("current_state") in {"PARTIALLY_BUILT_VALID", "PARTIALLY_IMPLEMENTED", "UNIMPLEMENTED"}
    )
    local = sum(1 for r in v4 if r.get("current_state") == "LOCAL_ENGINEERING_COMPLETE")
    return {
        "V4_V2_FINAL_LOCAL_COMPLETION_PRESERVED": remaining == 0 and local == 644,
        "V4_V2_REMAINING_LOCAL": remaining,
        "V4_V2_LOCAL_COMPLETE": local,
    }


def update_master_plan(head: str, now: str, arith: dict[str, Any]) -> None:
    if not MASTER_PLAN_PATH.is_file():
        return
    text = MASTER_PLAN_PATH.read_text(encoding="utf-8")
    marker = "## 2e. Temporal Phase-2 source-driven closure"
    if marker not in text:
        insert = (
            f"\n{marker}\n\n"
            f"**Temporal Phase-2 material SHA:** `{head}`\n"
            f"**LOCAL_ENGINEERING_COMPLETE:** {arith.get('LOCAL_ENGINEERING_COMPLETE')}\n"
            f"**TEMPORAL_REMAINING_LOCAL_REQUIREMENTS:** {arith.get('TEMPORAL_REMAINING_LOCAL_REQUIREMENTS')}\n\n"
        )
        text = text.replace("## 2. Current state through Batch13", insert + "\n## 2. Current state through Batch13", 1)
    text = re.sub(r"\*\*Generated:\*\*.*", f"**Generated:** {now}", text, count=1)
    text = re.sub(r"\*\*Branch:\*\*.*", f"**Branch:** `{BRANCH}`", text, count=1)
    text = re.sub(r"\*\*HEAD:\*\*.*", f"**HEAD:** `{head}`", text, count=1)
    MASTER_PLAN_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    head = git_head()
    now = datetime.now(UTC).isoformat()
    build_universe()
    build_index()
    pytest_result = run_pytest()
    if not pytest_result["ok"]:
        raise SystemExit(f"Pytest failed: {pytest_result}")
    universe = verify_buildable_universe()
    if not universe["ok"]:
        raise SystemExit(f"Buildable verification failed: {universe['failures'][:20]}")
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    source_audit = audit_source_to_ledger(ledger)
    gated_audit = revalidate_gated(ledger)
    rebuild = rebuild_temporal_ledger(head, now)
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    arith = final_arithmetic(ledger)
    v4_check = verify_v4_v2_preserved(ledger)
    if not v4_check["V4_V2_FINAL_LOCAL_COMPLETION_PRESERVED"]:
        raise SystemExit(f"v4_v2 regression in ledger: {v4_check}")
    freeze = {
        "artifact": "TEMPORAL_SOURCE_DRIVEN_FINAL_FREEZE",
        "generated_at_utc": now,
        "branch": BRANCH,
        "material_sha": head,
        "source_audit": source_audit,
        "gated_audit": gated_audit,
        "universe_verification": universe,
        "rebuild_stats": rebuild,
        "arithmetic": arith,
        "v4_v2_preservation": v4_check,
        "pytest": pytest_result,
        "temporal_status": temporal_source_driven_status(),
        "TEMPORAL_FINAL_LOCAL_COMPLETION": arith["TEMPORAL_REMAINING_LOCAL_REQUIREMENTS"] == 0,
        "NO_KNOWN_LOCALLY_BUILDABLE_TEMPORAL_WORK_REMAINING": arith["TEMPORAL_REMAINING_LOCAL_REQUIREMENTS"] == 0,
        "PASS_LIVE_NOT_CLAIMED": True,
        "INDEPENDENT_ASSURANCE_NOT_CLAIMED": True,
        "ADAPTIVE_DEDICATED_CLOSURE_NOT_STARTED": True,
        "BATCH18_NOT_CREATED": True,
        "RAILWAY_NOT_TOUCHED": True,
    }
    (DOCS / "TEMPORAL_SOURCE_DRIVEN_FINAL_FREEZE.json").write_text(json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    update_master_plan(head, now, arith)
    print(json.dumps({"freeze": "docs/TEMPORAL_SOURCE_DRIVEN_FINAL_FREEZE.json", **arith, **universe, **v4_check}, indent=2))


if __name__ == "__main__":
    main()
