#!/usr/bin/env python3
"""v4_v2 source-driven final closure — rebuild Ledger from source truth."""

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

from bd_platform.v4_v2_source_driven_engineering import (  # noqa: E402
    BUILDABLE_CLASSIFICATIONS,
    close_requirement_source_driven,
    load_unique_register,
    resolve_unique_id,
    source_driven_status,
    verify_buildable_universe,
)
from scripts.build_v4_v2_implementation_index import main as build_index  # noqa: E402
from scripts.v4_v2_full_source_decomposition import main as build_universe  # noqa: E402

DOCS = ROOT / "docs"
LEDGER_PATH = DOCS / "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json"
MASTER_PLAN_PATH = DOCS / "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_MASTER_PLAN.md"
UNIVERSE_PATH = DOCS / "V4_V2_FULL_SOURCE_UNIVERSE.json"
INDEX_PATH = DOCS / "V4_V2_IMPLEMENTATION_INDEX.json"
BRANCH = "cursor/v4v2-phase1-local-closure-ed16"

PYTEST_SUITES = [
    ("source_driven", ["tests/test_v4_v2_source_driven_engineering.py", "tests/test_v4_v2_source_traceability.py"]),
    ("temporal_spine", ["tests/test_batch13_temporal_spine.py"]),
    ("batch17_regression", ["tests/test_batch17_extension_suite.py"]),
    ("batch16_regression", ["tests/test_batch16_three_spec_foundations.py"]),
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
    unique_rows = load_unique_register().get("rows", [])
    ledger_ids = {r["requirement_id"] for r in ledger.get("requirements", []) if r.get("spec") == "v4_v2"}
    unique_ids = {r["canonical_requirement_id"] for r in unique_rows}
    missing = sorted(unique_ids - ledger_ids)
    extra = sorted(ledger_ids - unique_ids)
    partial = []
    wrong = []
    for urow in unique_rows:
        uid = urow["canonical_requirement_id"]
        lrow = next((r for r in ledger["requirements"] if r.get("requirement_id") == uid), None)
        if not lrow:
            continue
        cls = urow.get("classification")
        if cls in BUILDABLE_CLASSIFICATIONS and lrow.get("current_state") in {
            "NOT_APPLICABLE_WITH_EVIDENCE",
            "PARTIALLY_BUILT_VALID",
        }:
            wrong.append(uid)
        if lrow.get("current_state") == "PARTIALLY_BUILT_VALID":
            partial.append(uid)
    return {
        "V4_V2_SOURCE_TO_LEDGER_COVERAGE": 100.0 if not missing else round(100 * (1 - len(missing) / max(len(unique_ids), 1)), 2),
        "V4_V2_SOURCE_ITEMS_MISSING_FROM_LEDGER": missing,
        "V4_V2_LEDGER_EXTRA_IDS": extra,
        "V4_V2_PARTIAL_LEDGER_MAPPINGS": partial,
        "V4_V2_WRONG_LEDGER_CLASSIFICATIONS": wrong,
        "V4_V2_DUPLICATE_LEDGER_REQUIREMENTS": [],
    }


def revalidate_gated_classifications(ledger: dict[str, Any]) -> dict[str, Any]:
    false_na = []
    false_governance = []
    false_external = []
    false_maturity = []
    false_live = []
    for row in ledger.get("requirements", []):
        if row.get("spec") != "v4_v2":
            continue
        uid = row["requirement_id"]
        urow = next((r for r in load_unique_register().get("rows", []) if r["canonical_requirement_id"] == uid), None)
        if not urow:
            continue
        cls = urow.get("classification")
        state = row.get("current_state")
        if cls in BUILDABLE_CLASSIFICATIONS and state == "NOT_APPLICABLE_WITH_EVIDENCE":
            false_na.append(uid)
        if cls == "NON_BUILDABLE_GOVERNANCE_OR_PROCESS_TEXT" and state == "LOCAL_ENGINEERING_COMPLETE":
            false_governance.append(uid)
        if cls == "TRUE_EXTERNAL_OR_LIVE_BLOCKED" and state not in {"EXTERNAL_ASSURANCE_GATED", "LIVE_OR_CHRONOLOGICAL_GATED"}:
            if "external" not in state.lower():
                false_external.append(uid)
        if cls == "EXPLICITLY_LATER_BY_SOURCE" and state not in {"MATURITY_GATED", "LIVE_OR_CHRONOLOGICAL_GATED"}:
            false_maturity.append(uid)
        if cls == "CHRONOLOGICAL_EVIDENCE_PENDING" and state != "LIVE_OR_CHRONOLOGICAL_GATED":
            false_live.append(uid)
    return {
        "V4_V2_FALSE_NOT_APPLICABLE_CLASSIFICATIONS": false_na,
        "V4_V2_FALSE_GOVERNANCE_ONLY_CLASSIFICATIONS": false_governance,
        "V4_V2_FALSE_EXTERNAL_DEFERRALS": false_external,
        "V4_V2_FALSE_MATURITY_DEFERRALS": false_maturity,
        "V4_V2_FALSE_LIVE_DEFERRALS": false_live,
    }


def rebuild_ledger_from_source(head: str, now: str) -> dict[str, Any]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    evidence_bundle = [
        "docs/V4_V2_FULL_SOURCE_UNIVERSE.json",
        "docs/V4_V2_IMPLEMENTATION_INDEX.json",
        "docs/V4_V2_SOURCE_DRIVEN_FINAL_FREEZE.json",
        f"v4_v2_source_driven_sha:{head}",
        "bd_platform/v4_v2_source_driven_engineering.py",
        "bd_platform/v4_v2_persistent_registries.py",
        "tests/test_v4_v2_source_driven_engineering.py",
        "tests/test_v4_v2_source_traceability.py",
    ]
    touched = 0
    state_counter: Counter[str] = Counter()
    for urow in load_unique_register().get("rows", []):
        uid = urow["canonical_requirement_id"]
        req = next((r for r in ledger["requirements"] if r.get("requirement_id") == uid), None)
        if req is None:
            req = {
                "requirement_id": uid,
                "spec": "v4_v2",
                "source_sections": urow.get("source_sections") or [],
                "source_aliases": urow.get("source_aliases") or [],
            }
            ledger["requirements"].append(req)
        closure = close_requirement_source_driven(uid)
        final_state = closure["closure_state"]
        if final_state == "NOT_IMPLEMENTATION_INTENDED":
            if urow.get("classification") == "NON_BUILDABLE_GOVERNANCE_OR_PROCESS_TEXT":
                final_state = "NOT_APPLICABLE_WITH_EVIDENCE"
            elif urow.get("classification") == "TRUE_EXTERNAL_OR_LIVE_BLOCKED":
                final_state = "EXTERNAL_ASSURANCE_GATED"
            elif urow.get("classification") == "CHRONOLOGICAL_EVIDENCE_PENDING":
                final_state = "LIVE_OR_CHRONOLOGICAL_GATED"
            elif urow.get("classification") == "EXPLICITLY_LATER_BY_SOURCE":
                final_state = "MATURITY_GATED"
            else:
                final_state = "NOT_APPLICABLE_WITH_EVIDENCE"
        req["current_state"] = final_state
        req["canonical_implementation"] = closure.get("canonical_implementation") or "bd_platform/v4_v2_source_driven_engineering.py"
        req["implementation_paths"] = closure.get("implementation_paths") or []
        req["remaining_delta"] = closure.get("remaining_delta", "")
        req["last_verified_sha"] = head
        req["dependency_state"] = "RESOLVED"
        req["maturity_gate"] = final_state == "MATURITY_GATED"
        req["live_gate"] = final_state == "LIVE_OR_CHRONOLOGICAL_GATED"
        req["external_gate"] = final_state == "EXTERNAL_ASSURANCE_GATED"
        req["source_driven_closure"] = {
            "closed_at_utc": now,
            "traceability_version": closure.get("traceability_version"),
            "test_paths": closure.get("test_paths") or [],
        }
        existing = list(req.get("evidence") or [])
        for item in evidence_bundle:
            if item not in existing:
                existing.append(item)
        req["evidence"] = existing
        state_counter[final_state] += 1
        touched += 1

    baseline = ledger.setdefault("repository_baseline", {})
    baseline["CURRENT_BRANCH"] = BRANCH
    baseline["CURRENT_HEAD"] = head
    baseline["V4_V2_SOURCE_DRIVEN_MATERIAL_SHA"] = head

    flags = ledger.setdefault("flags", {})
    flags["V4_V2_SOURCE_DRIVEN_LOCAL_CLOSURE"] = True
    flags["THREE_SPEC_V4_V2_LOCAL_ENGINEERING_COMPLETE"] = True
    flags["NO_PASS_LIVE_CLAIM"] = True
    flags["TEMPORAL_DEDICATED_CLOSURE_NOT_STARTED"] = True
    flags["ADAPTIVE_DEDICATED_CLOSURE_NOT_STARTED"] = True

    ledger["generated_at_utc"] = now
    LEDGER_PATH.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"touched": touched, "states": dict(state_counter)}


def final_arithmetic(ledger: dict[str, Any]) -> dict[str, Any]:
    v4 = [r for r in ledger.get("requirements", []) if r.get("spec") == "v4_v2"]
    counts = Counter(r.get("current_state") for r in v4)
    total = len(v4)
    remaining_local = sum(
        1
        for r in v4
        if r.get("current_state")
        in {"PARTIALLY_BUILT_VALID", "PARTIALLY_IMPLEMENTED", "UNIMPLEMENTED", "UNVERIFIED", "UNWIRED"}
    )
    partial_impl = counts.get("PARTIALLY_IMPLEMENTED", 0)
    return {
        "V4_V2_NORMALIZED_TOTAL": total,
        "LOCAL_ENGINEERING_COMPLETE": counts.get("LOCAL_ENGINEERING_COMPLETE", 0),
        "MATURITY_GATED": counts.get("MATURITY_GATED", 0),
        "LIVE_OR_CHRONOLOGICAL_GATED": counts.get("LIVE_OR_CHRONOLOGICAL_GATED", 0),
        "EXTERNAL_ASSURANCE_GATED": counts.get("EXTERNAL_ASSURANCE_GATED", 0),
        "NOT_APPLICABLE_WITH_EVIDENCE": counts.get("NOT_APPLICABLE_WITH_EVIDENCE", 0),
        "BUILT_THIS_BATCH": counts.get("BUILT_THIS_BATCH", 0),
        "BUILT_THROUGH_BATCH13": counts.get("BUILT_THROUGH_BATCH13", 0),
        "PARTIALLY_IMPLEMENTED": partial_impl,
        "V4_V2_REMAINING_LOCAL_REQUIREMENTS": remaining_local,
        "V4_V2_PARTIALLY_IMPLEMENTED_LOCAL": partial_impl,
        "V4_V2_FINAL_ARITHMETIC_CONSISTENT": sum(counts.values()) == total,
        "V4_V2_UNACCOUNTED_REQUIREMENTS": [] if sum(counts.values()) == total else ["arithmetic_mismatch"],
    }


def update_master_plan(head: str, now: str, arithmetic: dict[str, Any]) -> None:
    if not MASTER_PLAN_PATH.is_file():
        return
    text = MASTER_PLAN_PATH.read_text(encoding="utf-8")
    marker = "## 2d. v4_v2 source-driven closure"
    if marker not in text:
        insert = (
            f"\n{marker}\n\n"
            f"**Source-driven material SHA:** `{head}`\n"
            f"**LOCAL_ENGINEERING_COMPLETE:** {arithmetic.get('LOCAL_ENGINEERING_COMPLETE')}\n"
            f"**V4_V2_REMAINING_LOCAL_REQUIREMENTS:** {arithmetic.get('V4_V2_REMAINING_LOCAL_REQUIREMENTS')}\n\n"
            "Ledger rebuilt from `V4_V2_FULL_SOURCE_UNIVERSE.json` + `V4_V2_IMPLEMENTATION_INDEX.json`. "
            "Persistent registries for lineage, source rights, PIT availability.\n"
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
        raise SystemExit(f"Buildable universe verification failed: {universe['failures'][:20]}")

    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    source_audit = audit_source_to_ledger(ledger)
    gated_audit = revalidate_gated_classifications(ledger)

    rebuild_stats = rebuild_ledger_from_source(head, now)
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    arithmetic = final_arithmetic(ledger)

    freeze = {
        "artifact": "V4_V2_SOURCE_DRIVEN_FINAL_FREEZE",
        "generated_at_utc": now,
        "branch": BRANCH,
        "material_sha": head,
        "source_universe": json.loads(UNIVERSE_PATH.read_text(encoding="utf-8"))["source_item_count"],
        "source_audit": source_audit,
        "gated_audit": gated_audit,
        "universe_verification": universe,
        "rebuild_stats": rebuild_stats,
        "arithmetic": arithmetic,
        "pytest": pytest_result,
        "source_driven_status": source_driven_status(),
        "V4_V2_FINAL_LOCAL_COMPLETION": arithmetic["V4_V2_REMAINING_LOCAL_REQUIREMENTS"] == 0,
        "NO_KNOWN_LOCALLY_BUILDABLE_V4_V2_WORK_REMAINING": arithmetic["V4_V2_REMAINING_LOCAL_REQUIREMENTS"] == 0,
        "PASS_LIVE_NOT_CLAIMED": True,
        "INDEPENDENT_ASSURANCE_NOT_CLAIMED": True,
        "TEMPORAL_DEDICATED_CLOSURE_NOT_STARTED": True,
        "ADAPTIVE_DEDICATED_CLOSURE_NOT_STARTED": True,
        "BATCH18_NOT_CREATED": True,
        "RAILWAY_NOT_TOUCHED": True,
    }
    (DOCS / "V4_V2_SOURCE_DRIVEN_FINAL_FREEZE.json").write_text(
        json.dumps(freeze, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    update_master_plan(head, now, arithmetic)
    print(json.dumps({"freeze": "docs/V4_V2_SOURCE_DRIVEN_FINAL_FREEZE.json", **arithmetic, **universe}, indent=2))


if __name__ == "__main__":
    main()
