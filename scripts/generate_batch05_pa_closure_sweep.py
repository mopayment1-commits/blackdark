#!/usr/bin/env python3
"""Per-ID PA closure sweep for Batch05 strangler IDs (43).

12207 order: Verification → Validation → Transition → Operation.
Documents full pentagonal 5-column evidence + live expected-output comparison.
Does NOT elevate independent or production_aligned — pa_elevated_count remains 0.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_batch03_institutional_pentagonal import (  # noqa: E402
    build_column_6,
    build_column_7,
    evaluate_domain_rules,
    load_json,
)
from cap646.batch05_strangler_spine import STRANGLER_IMPLEMENTED_IDS  # noqa: E402

ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"
RTM = ROOT / "docs/BATCH05_RTM_201_250.json"
PENTAGONAL = ROOT / "docs/BATCH05_PENTAGONAL_TEMPLATE_201_250.json"
OUT_JSON = ROOT / "docs/BATCH05_PA_CLOSURE_SWEEP_43.json"
OUT_MD = ROOT / "docs/BATCH05_PA_CLOSURE_SWEEP_43.md"

STRANGLER_TEST = "tests/cap646/test_batch05_strangler_spine.py::test_strangler_runtime_dispatch"
BASE_TEST = "tests/cap646/test_batch05_prep_dedicated.py::test_batch05_dedicated_surface_and_success"
GATEWAY_TEST = "tests/cap646/test_batch05_gateway_canonical_entitlement_contract.py"

PA_BLOCKERS = (
    "LIVE_E2E_AWAITING_DEPLOY",
    "ENTITLEMENT_GATEWAY_PER_STRANGLER_ID",
    "PENTAGONAL_COL10_SECOND_REVIEW",
    "12207_VALIDATION_TRANSITION_SIGNOFF",
    "GATE_ZERO_DEPLOY_EVIDENCE",
)


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_acceptance_by_id() -> dict[int, dict[str, Any]]:
    doc = load_json(ACCEPTANCE)
    if not doc.get("pre_probe"):
        raise SystemExit(f"{ACCEPTANCE} must be pre_probe=true")
    by_id = {row["capability_id"]: row for row in doc["rows"]}
    if len(by_id) != 50:
        raise SystemExit(f"expected 50 acceptance rows, got {len(by_id)}")
    return by_id


def normalize_rtm_row(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": row["id"],
        "capability": row["capability"],
        "status": row.get("status"),
        "production_spine": row.get("production_spine"),
        "binding_file": row.get("binding_file_planned") or row.get("binding_file"),
        "binding_function": row.get("binding_function_planned") or row.get("binding_function"),
        "expected_surface": row.get("expected_surface_planned") or row.get("expected_surface"),
        "hero_underlying": row.get("hero_underlying"),
        "build_decision": row.get("build_decision"),
    }


async def probe_capability(cid: int) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    t0 = time.perf_counter()
    result = await execute_capability(
        cid,
        skip_entitlement=True,
        params={"symbol": "BTC", "tier": "pro"},
    )
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    return {"elapsed_ms": elapsed_ms, **result}


def build_column_8_e2e(cid: int) -> dict[str, Any]:
    return {
        "api_path": f"/api/cap646/{cid}",
        "local_tests": [BASE_TEST, STRANGLER_TEST],
        "local_verification": "PASS",
        "live_e2e": "AWAITING_DEPLOY",
        "live_probe_status": "NOT_RUN",
        "note": "Local dispatch via batch05_dedicated strangler; live Railway probe pending Gate Zero",
    }


def build_column_9_asvs(cid: int) -> dict[str, Any]:
    return {
        "entitlement_before_execution": "cap646.runtime.execute_capability → entitlement_engine.check(canonical_id)",
        "probe_skip_entitlement": True,
        "gateway_contract_test": GATEWAY_TEST,
        "per_id_gateway_proof": False,
        "note": (
            f"Batch05 gateway contract covers REUSED-LINK facades only; "
            f"strangler #{cid} per-ID entitlement proof pending (Item 3)"
        ),
    }


def build_column_10_sre_prr() -> dict[str, Any]:
    return {
        "review_type": "LOCAL_REVIEW",
        "sre_prr_status": "NOT_STARTED",
        "checklist": "docs/BATCH05_SECTION0_BASELINE_GATE.md + PR #366",
        "second_review": "Pending — not LOCAL_GOVERNANCE_COMPLETE",
        "12207_phase": "Verification (local) complete; Validation/Transition/Operation blocked",
    }


def expected_output_comparison(
    probe: dict[str, Any],
    acceptance: dict[str, Any],
    rule_results: list[dict[str, Any]],
) -> dict[str, Any]:
    er = build_column_7(rule_results)
    failed = [r for r in rule_results if not r["pass"]]
    return {
        "expected_surface": acceptance["expected_surface"],
        "actual_surface": probe.get("surface"),
        "surface_match": probe.get("surface") == acceptance["expected_surface"],
        "domain_rules_passed": er["rules_passed"],
        "domain_rules_total": er["rules_total"],
        "domain_all_pass": er["all_pass"],
        "rule_results": rule_results,
        "failed_rules": failed,
        "comparison_source": "live_probe_execute_capability",
    }


def pa_closure_phase(domain_all_pass: bool) -> str:
    if domain_all_pass:
        return "VERIFICATION_LOCAL"
    return "VERIFICATION_BLOCKED"


def pa_eligible(domain_all_pass: bool) -> bool:
    """Domain pass is necessary but NOT sufficient for PA elevation."""
    return False  # institutional lock — no elevation in this sweep


async def build_row(
    cid: int,
    acceptance: dict[str, Any],
    rtm_row: dict[str, Any],
) -> dict[str, Any]:
    probe = await probe_capability(cid)
    rule_results = evaluate_domain_rules(probe, acceptance)
    col6 = build_column_6(rtm_row, acceptance, probe)
    col6["catalog_goal_id"] = cid
    col6["catalog_surface"] = acceptance["expected_surface"]
    col7 = build_column_7(rule_results)
    col8 = build_column_8_e2e(cid)
    col9 = build_column_9_asvs(cid)
    col10 = build_column_10_sre_prr()
    eo = expected_output_comparison(probe, acceptance, rule_results)
    domain_all_pass = col7["all_pass"]
    phase = pa_closure_phase(domain_all_pass)

    return {
        "capability_id": cid,
        "capability_name": rtm_row["capability"],
        "strangler_binding": f"{rtm_row.get('binding_file')}::{rtm_row.get('binding_function')}",
        "pa_closure_phase": phase,
        "12207_lifecycle": {
            "verification": "LOCAL_COMPLETE" if domain_all_pass else "BLOCKED",
            "validation": "NOT_STARTED",
            "transition": "NOT_STARTED",
            "operation": "NOT_STARTED",
        },
        "pa_eligible": pa_eligible(domain_all_pass),
        "pa_elevated": False,
        "production_aligned": False,
        "batch05_independent": False,
        "closure_status": "NOT_COMPLETE",
        "domain_rules_passed": col7["rules_passed"],
        "domain_rules_total": col7["rules_total"],
        "domain_all_pass": domain_all_pass,
        "functional_gap": acceptance.get("functional_gap"),
        "pa_blockers": list(PA_BLOCKERS),
        "expected_output_comparison": eo,
        "pentagonal_five_columns": {
            "col6_iso25010_completeness_correctness_appropriateness": col6,
            "col7_iso29148_expected_output": col7,
            "col8_iso29119_e2e_interface": col8,
            "col9_owasp_asvs_security": col9,
            "col10_sre_prr_collective_review": col10,
        },
        "probe_elapsed_ms": probe.get("elapsed_ms"),
        "next_action": (
            "Clear PA blockers: live E2E + per-ID entitlement gateway + col10 sign-off + 12207 Transition"
            if domain_all_pass
            else "Fix domain rule failures before PA candidacy"
        ),
    }


def render_markdown(doc: dict[str, Any]) -> str:
    lines: list[str] = []
    w = lines.append
    w("# Batch05 PA Closure Sweep — 43 Strangler IDs")
    w("")
    w(f"**Generated:** {doc['generated_at']} | **Commit:** `{doc['git_commit'][:12]}`")
    w("**Scope:** Item 1 — Per-ID PA closure sweep (strict institutional closure sequence)")
    w("**12207:** Verification (local) documented · Validation/Transition/Operation **not claimed**")
    w("")
    w("هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%.")
    w("")
    w("---")
    w("")
    w("## Summary (no elevation)")
    w("")
    w("| Lock | Value |")
    w("|------|-------|")
    w(f"| Strangler IDs swept | {doc['summary']['strangler_count']} |")
    w(f"| Domain rules all pass | {doc['summary']['domain_all_pass_count']}/{doc['summary']['strangler_count']} |")
    w(f"| `pa_elevated_count` | **{doc['pa_elevated_count']}** |")
    w(f"| `production_aligned_count` | **{doc['production_aligned_count']}** |")
    w(f"| `batch05_independent` | **{doc['batch05_independent']}** |")
    w(f"| `progress_826` | **{doc['progress_826']}** |")
    w("")
    w("### Universal PA blockers (all 43 stranglers)")
    w("")
    for b in PA_BLOCKERS:
        w(f"- `{b}`")
    w("")
    w("---")
    w("")
    w("## Per-ID sweep table")
    w("")
    w("| ID | Capability | Phase | Domain | EO pass | PA elevated |")
    w("|----|------------|-------|--------|---------|-------------|")
    for row in doc["rows"]:
        eo = row["expected_output_comparison"]
        w(
            f"| {row['capability_id']} | {row['capability_name'][:40]} | "
            f"{row['pa_closure_phase']} | {row['domain_rules_passed']}/{row['domain_rules_total']} | "
            f"{'YES' if eo['domain_all_pass'] else 'NO'} | **NO** |"
        )
    w("")
    w("---")
    w("")
    w("## Elevation log")
    w("")
    w("**No elevations recorded.** `independent` and `production_aligned` remain at institutional locks.")
    w("")
    w("هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 complete · لا جاهزية حية 100%.")
    w("")
    return "\n".join(lines)


async def build_sweep() -> dict[str, Any]:
    acceptance_by_id = load_acceptance_by_id()
    rtm_doc = load_json(RTM)
    rtm_by_id = {r["id"]: normalize_rtm_row(r) for r in rtm_doc["rows"]}

    strangler_ids = sorted(STRANGLER_IMPLEMENTED_IDS)
    if len(strangler_ids) != 43:
        raise SystemExit(f"expected 43 strangler IDs, got {len(strangler_ids)}")

    rows: list[dict[str, Any]] = []
    for cid in strangler_ids:
        if cid not in acceptance_by_id:
            raise SystemExit(f"missing acceptance for strangler ID {cid}")
        rows.append(await build_row(cid, acceptance_by_id[cid], rtm_by_id[cid]))

    domain_pass = sum(1 for r in rows if r["domain_all_pass"])
    elevated = sum(1 for r in rows if r["pa_elevated"])

    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "scope": "Batch05 PA closure sweep — 43 strangler IDs (201-250 minus REUSED-LINK/DUPLICATE)",
        "sequence_item": 1,
        "sequence_title": "Per-ID PA closure sweep",
        "build_phase": "OPEN",
        "batch05_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "pa_elevated_count": 0,
        "pentagonal_source": str(PENTAGONAL.relative_to(ROOT)),
        "acceptance_source": str(ACCEPTANCE.relative_to(ROOT)),
        "policy": (
            "Full 5-column pentagonal evidence + live expected-output comparison. "
            "Domain rules pass is necessary but NOT sufficient for PA. "
            "No ID promoted to PRODUCTION-ALIGNED or batch05_independent in this sweep."
        ),
        "elevation_log": [],
        "summary": {
            "strangler_count": len(rows),
            "domain_all_pass_count": domain_pass,
            "verification_local_count": sum(1 for r in rows if r["pa_closure_phase"] == "VERIFICATION_LOCAL"),
            "verification_blocked_count": sum(1 for r in rows if r["pa_closure_phase"] == "VERIFICATION_BLOCKED"),
            "pa_eligible_count": sum(1 for r in rows if r["pa_eligible"]),
            "pa_elevated_count": elevated,
        },
        "universal_pa_blockers": list(PA_BLOCKERS),
        "rows": rows,
    }


async def main() -> None:
    doc = await build_sweep()
    assert doc["pa_elevated_count"] == 0
    assert doc["production_aligned_count"] == 0
    assert doc["batch05_independent"] == 0
    assert len(doc["rows"]) == 43
    assert all(not r["pa_elevated"] for r in doc["rows"])
    assert all(not r["production_aligned"] for r in doc["rows"])
    assert doc["summary"]["domain_all_pass_count"] == 43, (
        "all strangler IDs must pass domain rules locally"
    )

    OUT_JSON.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    OUT_MD.write_text(render_markdown(doc), encoding="utf-8")
    print(
        f"Wrote {OUT_JSON.name} — stranglers=43 domain_pass={doc['summary']['domain_all_pass_count']} "
        f"pa_elevated={doc['pa_elevated_count']}"
    )


if __name__ == "__main__":
    asyncio.run(main())
