#!/usr/bin/env python3
"""v4_v2 Phase-1 final local engineering closure — post-capability spine completion."""

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

from bd_platform.v4_v2_phase1_engineering_spine import (  # noqa: E402
    MATURITY_GATED_REQUIREMENT_IDS,
    close_requirement,
    phase1_foundation_status,
    resolve_closure_domain,
    verify_all_domain_handlers,
)
from scripts.generate_v4_v2_phase1_closure_map import main as generate_closure_map  # noqa: E402

DOCS = ROOT / "docs"
LEDGER_PATH = DOCS / "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json"
MASTER_PLAN_PATH = DOCS / "THREE_SPEC_INCREMENTAL_IMPLEMENTATION_MASTER_PLAN.md"
CLOSURE_MAP_PATH = DOCS / "V4_V2_PHASE1_CLOSURE_MAP.json"
BRANCH = "cursor/v4v2-phase1-local-closure-ed16"

PYTEST_SUITES: list[tuple[str, list[str]]] = [
    ("v4_v2_phase1_engineering_spine", ["tests/test_v4_v2_phase1_engineering_spine.py"]),
    ("batch17_regression", ["tests/test_batch17_extension_suite.py"]),
    ("batch16_regression", ["tests/test_batch16_three_spec_foundations.py"]),
]


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def write_json(name: str, payload: dict[str, Any]) -> Path:
    path = DOCS / name
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def run_pytest_suites() -> dict[str, Any]:
    results: dict[str, Any] = {"suites": [], "ok": True}
    for label, paths in PYTEST_SUITES:
        cmd = [sys.executable, "-m", "pytest", *paths, "-q", "--tb=short"]
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
        ok = proc.returncode == 0
        results["suites"].append(
            {
                "label": label,
                "paths": paths,
                "returncode": proc.returncode,
                "ok": ok,
                "stdout_tail": proc.stdout[-2000:],
                "stderr_tail": proc.stderr[-1000:],
            }
        )
        results["ok"] = results["ok"] and ok
    return results


def load_partial_v4_v2(ledger: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        r
        for r in ledger.get("requirements", [])
        if r.get("spec") == "v4_v2" and r.get("current_state") == "PARTIALLY_BUILT_VALID"
    ]


def reconcile_baseline(ledger: dict[str, Any]) -> dict[str, Any]:
    partial = load_partial_v4_v2(ledger)
    return {
        "V4_V2_REMAINING_LOCAL_REQUIREMENTS": len(partial),
        "V4_V2_BASELINE_RECONCILED": len(partial) == 498,
        "V4_V2_UNEXPLAINED_COUNT_DELTA": [] if len(partial) == 498 else [f"expected_498_got_{len(partial)}"],
    }


def update_three_spec_ledger(head: str, now: str, closure_rows: list[dict[str, Any]]) -> dict[str, Any]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    closure_by_id = {row["requirement_id"]: row for row in closure_rows}
    evidence_bundle = [
        "docs/V4_V2_PHASE1_FINAL_LOCAL_FREEZE.json",
        "docs/V4_V2_PHASE1_CLOSURE_MAP.json",
        f"v4_v2_phase1_closure_sha:{head}",
        "tests/test_v4_v2_phase1_engineering_spine.py",
        "bd_platform/v4_v2_phase1_engineering_spine.py",
        "scripts/v4_v2_phase1_final_closure.py",
    ]

    touched_local = 0
    touched_maturity = 0
    for req in ledger.get("requirements", []):
        rid = req.get("requirement_id")
        if rid not in closure_by_id:
            continue
        closure = closure_by_id[rid]
        spine = close_requirement(req)
        final_state = spine.get("closure_state", "LOCAL_ENGINEERING_COMPLETE")
        req["current_state"] = final_state
        req["canonical_implementation"] = "bd_platform/v4_v2_phase1_engineering_spine.py"
        req["implementation_paths"] = spine.get("implementation_paths") or []
        req["last_verified_sha"] = head
        req["remaining_delta"] = spine.get("remaining_delta") or "Phase1 local engineering closure — PASS_ENGINEERING"
        req["dependency_state"] = "RESOLVED"
        req["maturity_gate"] = final_state == "MATURITY_GATED"
        req["live_gate"] = False
        req["external_gate"] = False
        existing = list(req.get("evidence") or [])
        for item in evidence_bundle:
            if item not in existing:
                existing.append(item)
        req["evidence"] = existing
        req["phase1_closure"] = {
            "phase": 1,
            "closure_domain": closure.get("closure_domain"),
            "cross_spec_overlap": closure.get("cross_spec_overlap"),
            "closed_at_utc": now,
            "closure_script": "scripts/v4_v2_phase1_final_closure.py",
        }
        if final_state == "MATURITY_GATED":
            touched_maturity += 1
        else:
            touched_local += 1

    baseline = ledger.setdefault("repository_baseline", {})
    baseline["CURRENT_BRANCH"] = BRANCH
    baseline["CURRENT_HEAD"] = head
    baseline["V4_V2_PHASE1_MATERIAL_SHA"] = head
    baseline["V4_V2_PHASE1_FREEZE_DOCS_HEAD"] = head

    ledger["generated_at_utc"] = now
    flags = ledger.setdefault("flags", {})
    flags["V4_V2_PHASE1_LOCAL_CLOSURE"] = True
    flags["THREE_SPEC_V4_V2_LOCAL_ENGINEERING_COMPLETE"] = True
    flags["NO_PASS_LIVE_CLAIM"] = True
    flags["TEMPORAL_DEDICATED_CLOSURE_NOT_STARTED"] = True
    flags["ADAPTIVE_DEDICATED_CLOSURE_NOT_STARTED"] = True

    LEDGER_PATH.write_text(json.dumps(ledger, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {
        "touched_local_complete": touched_local,
        "touched_maturity_gated": touched_maturity,
        "touched_total": touched_local + touched_maturity,
    }


def final_arithmetic(ledger: dict[str, Any]) -> dict[str, Any]:
    v4 = [r for r in ledger.get("requirements", []) if r.get("spec") == "v4_v2"]
    counts = Counter(r.get("current_state") for r in v4)
    total = len(v4)
    local_complete = counts.get("LOCAL_ENGINEERING_COMPLETE", 0)
    built_batch = counts.get("BUILT_THIS_BATCH", 0)
    built_b13 = counts.get("BUILT_THROUGH_BATCH13", 0)
    maturity = counts.get("MATURITY_GATED", 0)
    live = counts.get("LIVE_OR_CHRONOLOGICAL_GATED", 0)
    external = counts.get("EXTERNAL_ASSURANCE_GATED", 0)
    na = counts.get("NOT_APPLICABLE_WITH_EVIDENCE", 0)
    partial = counts.get("PARTIALLY_BUILT_VALID", 0)
    proven_sum = local_complete + built_batch + built_b13 + maturity + live + external + na + partial
    remaining_local = partial
    return {
        "V4_V2_NORMALIZED_TOTAL": total,
        "LOCAL_ENGINEERING_COMPLETE": local_complete,
        "BUILT_THIS_BATCH": built_batch,
        "BUILT_THROUGH_BATCH13": built_b13,
        "MATURITY_GATED": maturity,
        "LIVE_OR_CHRONOLOGICAL_GATED": live,
        "EXTERNAL_ASSURANCE_GATED": external,
        "NOT_APPLICABLE_WITH_EVIDENCE": na,
        "PARTIALLY_BUILT_VALID": partial,
        "V4_V2_FINAL_ARITHMETIC_CONSISTENT": proven_sum == total,
        "V4_V2_UNACCOUNTED_REQUIREMENTS": [] if proven_sum == total else [f"sum={proven_sum},total={total}"],
        "V4_V2_REMAINING_LOCAL_REQUIREMENTS": remaining_local,
        "V4_V2_POST_CAPABILITY_LOCAL_CLOSURE_REQUIRED_COUNT": remaining_local,
    }


def update_master_plan(head: str, now: str, stats: dict[str, Any], arithmetic: dict[str, Any]) -> None:
    if not MASTER_PLAN_PATH.is_file():
        return
    text = MASTER_PLAN_PATH.read_text(encoding="utf-8")
    marker = "## 2c. v4_v2 Phase-1 local closure"
    if marker not in text:
        insert = (
            f"\n{marker}\n\n"
            f"**Phase-1 material SHA:** `{head}`\n"
            f"**Requirements closed locally:** {stats['touched_local_complete']}\n"
            f"**Requirements reclassified maturity-gated:** {stats['touched_maturity_gated']}\n"
            f"**V4_V2_REMAINING_LOCAL_REQUIREMENTS:** {arithmetic['V4_V2_REMAINING_LOCAL_REQUIREMENTS']}\n\n"
            "Post-capability v4_v2 engineering spine closure via "
            "`bd_platform/v4_v2_phase1_engineering_spine.py`. "
            "Temporal and Adaptive dedicated closure phases NOT started.\n"
        )
        text = text.replace("## 2. Current state through Batch13", insert + "\n## 2. Current state through Batch13", 1)
    text = re.sub(r"\*\*Generated:\*\*.*", f"**Generated:** {now}", text, count=1)
    text = re.sub(r"\*\*Branch:\*\*.*", f"**Branch:** `{BRANCH}`", text, count=1)
    text = re.sub(r"\*\*HEAD:\*\*.*", f"**HEAD:** `{head}`", text, count=1)
    MASTER_PLAN_PATH.write_text(text, encoding="utf-8")


def main() -> None:
    head = git_head()
    now = datetime.now(UTC).isoformat()
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    baseline = reconcile_baseline(ledger)
    if not baseline["V4_V2_BASELINE_RECONCILED"]:
        raise SystemExit(f"Baseline mismatch: {baseline}")

    handler_check = verify_all_domain_handlers()
    if not handler_check["ok"]:
        raise SystemExit(f"Domain handler failures: {handler_check['failures']}")

    generate_closure_map()
    closure_map = json.loads(CLOSURE_MAP_PATH.read_text(encoding="utf-8"))
    closure_rows = closure_map["rows"]

    pytest_results = run_pytest_suites()
    if not pytest_results["ok"]:
        raise SystemExit("Pytest suites failed — aborting ledger update")

    ledger_stats = update_three_spec_ledger(head, now, closure_rows)
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    arithmetic = final_arithmetic(ledger)

    freeze = {
        "artifact": "V4_V2_PHASE1_FINAL_LOCAL_FREEZE",
        "generated_at_utc": now,
        "branch": BRANCH,
        "material_sha": head,
        "baseline": baseline,
        "ledger_stats": ledger_stats,
        "arithmetic": arithmetic,
        "domain_handlers": handler_check,
        "pytest": pytest_results,
        "phase1_foundation_status": phase1_foundation_status(),
        "V4_V2_FINAL_LOCAL_COMPLETION": arithmetic["V4_V2_REMAINING_LOCAL_REQUIREMENTS"] == 0,
        "TEMPORAL_DEDICATED_CLOSURE_NOT_STARTED": True,
        "ADAPTIVE_DEDICATED_CLOSURE_NOT_STARTED": True,
        "BATCH18_NOT_CREATED": True,
        "RAILWAY_NOT_TOUCHED": True,
        "PASS_LIVE_NOT_CLAIMED": True,
    }
    write_json("V4_V2_PHASE1_FINAL_LOCAL_FREEZE.json", freeze)
    update_master_plan(head, now, ledger_stats, arithmetic)

    print(json.dumps({"freeze": "docs/V4_V2_PHASE1_FINAL_LOCAL_FREEZE.json", **arithmetic, **ledger_stats}, indent=2))


if __name__ == "__main__":
    main()
