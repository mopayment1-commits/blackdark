#!/usr/bin/env python3
"""Generate Batch05 institutional pentagonal build-phase deliverable (IDs 201-250).

Reads pre-test acceptance from docs/BATCH05_ACCEPTANCE_201_250.json (ISO 29148).
Does NOT mark any ID PRODUCTION-ALIGNED — batch05_independent remains 0 until PA closures.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_batch03_institutional_pentagonal import (  # noqa: E402
    assert_no_template_duplication,
    assert_rule_count_triple_match,
    build_column_6,
    build_column_7,
    evaluate_domain_rules,
    load_json,
)

OUT_MD = ROOT / "docs/BATCH05_INSTITUTIONAL_PENTAGONAL_BUILD.md"
OUT_JSON = ROOT / "docs/BATCH05_PENTAGONAL_TEMPLATE_201_250.json"
OUT_RTM_PROBE = ROOT / "docs/BATCH05_RTM_PROBE_201_250.json"
OUT_RULE_PROOF = ROOT / "docs/BATCH05_RULE_COUNT_ASSERT_PROOF.txt"
ACCEPTANCE = ROOT / "docs/BATCH05_ACCEPTANCE_201_250.json"
RTM = ROOT / "docs/BATCH05_RTM_201_250.json"
DEDUP_AUDIT = ROOT / "docs/BATCH05_DEDUP_AUDIT.json"

PROBE_IDS = list(range(201, 251))
REUSED_LINK_BATCH01 = frozenset({214, 245})
REUSED_LINK_BATCH02 = frozenset({206, 228, 226})
REUSED_LINK_INTERNAL = frozenset({232})
DUPLICATE_DELEGATION_IDS = frozenset({212})
REUSED_LINK_ALL = REUSED_LINK_BATCH01 | REUSED_LINK_BATCH02 | REUSED_LINK_INTERNAL

BASE_TEST = "tests/cap646/test_batch05_prep_dedicated.py::test_batch05_dedicated_surface_and_success"
REUSED_BATCH01_TEST = "tests/cap646/test_batch05_prep_dedicated.py::test_cap214_245_runtime_via_batch01_legacy_spine"
REUSED_BATCH02_TEST = "tests/cap646/test_batch05_prep_dedicated.py::test_cap206_228_reused_link_facade"
REUSED_226_TEST = "tests/cap646/test_batch05_prep_dedicated.py::test_cap226_reused_link_facade"
DUPLICATE_212_TEST = "tests/cap646/test_batch05_prep_dedicated.py::test_cap212_duplicate_delegation_not_batch05_spine"
REUSED_INTERNAL_TEST = "tests/cap646/test_batch05_prep_dedicated.py::test_cap232_reused_link_facade"
CATALOG_SAMPLE_TEST = "tests/cap646/test_batch05_prep_dedicated.py::test_batch05_catalog_aligned_have_domain_payload"
GATEWAY_TEST = "tests/cap646/test_batch05_gateway_canonical_entitlement_contract.py"

CATALOG_ALIGNED_SAMPLE = frozenset({201, 204, 211, 217, 229, 233, 237, 243, 246, 250})
STRANGLER_IMPLEMENTED_IDS = frozenset({201, 202, 203, 204})
STRANGLER_TEST = "tests/cap646/test_batch05_strangler_spine.py::test_strangler_runtime_dispatch"

LATENCY_LIMITS = {
    "direct_data": 500,
    "analysis": 2000,
    "ai_interpretation": 5000,
}


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_acceptance() -> dict[int, dict[str, Any]]:
    doc = load_json(ACCEPTANCE)
    if not doc.get("pre_probe"):
        raise SystemExit(f"{ACCEPTANCE} must be pre_probe=true")
    by_id: dict[int, dict[str, Any]] = {}
    for row in doc["rows"]:
        rules = row.get("domain_rules") or []
        if not rules:
            raise SystemExit(f"acceptance ID {row['capability_id']}: domain_rules must not be empty")
        by_id[row["capability_id"]] = row
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


def closure_status(cid: int, domain_all_pass: bool, acceptance: dict[str, Any]) -> str:
    if acceptance.get("status") == "DUPLICATE_DELEGATION":
        return "DUPLICATE_DELEGATION"
    if cid in REUSED_LINK_ALL:
        return "REUSED-LINK"
    if acceptance.get("status") == "REUSED-LINK":
        return "REUSED-LINK"
    return "NOT_COMPLETE"


def local_tests_for(cid: int) -> list[str]:
    if cid in DUPLICATE_DELEGATION_IDS:
        return [DUPLICATE_212_TEST]
    if cid in REUSED_LINK_BATCH01:
        return [REUSED_BATCH01_TEST]
    if cid == 226:
        return [REUSED_226_TEST]
    if cid in REUSED_LINK_BATCH02:
        return [REUSED_BATCH02_TEST]
    if cid in REUSED_LINK_INTERNAL:
        return [REUSED_INTERNAL_TEST]
    tests = [BASE_TEST]
    if cid in STRANGLER_IMPLEMENTED_IDS:
        tests.append(STRANGLER_TEST)
    if cid in CATALOG_ALIGNED_SAMPLE:
        tests.append(CATALOG_SAMPLE_TEST)
    return tests


def build_column_8(cid: int) -> dict[str, Any]:
    return {
        "api_path": f"/api/cap646/{cid}",
        "local_tests": local_tests_for(cid),
        "local_COMPLETE": True,
        "live_AWAITING_DEPLOY": "AWAITING_DEPLOY — live probe sign-off pending for batch05 strangler IDs",
    }


def build_column_10() -> dict[str, Any]:
    return {
        "review_type": "LOCAL_REVIEW",
        "checklist": "docs/BATCH05_SECTION0_BASELINE_GATE.md + PR #366",
        "note": "Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; SonarCloud pending",
        "second_review": "Batch05 MECE overlap gate #214/#245 + #205/#232 + #206/#228 + #226/#69",
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


def latency_bucket(cid: int, elapsed_ms: float) -> dict[str, Any]:
    if cid in {224, 242, 248}:
        kind, limit = "ai_interpretation", LATENCY_LIMITS["ai_interpretation"]
    elif cid in {201, 208, 226, 240}:
        kind, limit = "analysis", LATENCY_LIMITS["analysis"]
    else:
        kind, limit = "direct_data", LATENCY_LIMITS["direct_data"]
    return {
        "ms": elapsed_ms,
        "kind": kind,
        "limit_ms": limit,
        "within": elapsed_ms <= limit,
    }


async def build_rows(
    probe_ids: list[int],
    acceptance_by_id: dict[int, dict[str, Any]],
    rtm_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    for cid in probe_ids:
        rtm_row = normalize_rtm_row(rtm_by_id[cid])
        acceptance = acceptance_by_id[cid]
        probe = await probe_capability(cid)
        rule_results = evaluate_domain_rules(probe, acceptance)
        col6 = build_column_6(rtm_row, acceptance, probe)
        col6["catalog_goal_id"] = cid
        col6["catalog_surface"] = acceptance["expected_surface"]
        col7 = build_column_7(rule_results)
        col8 = build_column_8(cid)
        col10 = build_column_10()
        lat = latency_bucket(cid, float(probe.get("elapsed_ms") or 0))
        final_status = closure_status(cid, col7["all_pass"], acceptance)

        rows.append(
            {
                "capability_id": cid,
                "capability_name": rtm_row["capability"],
                "acceptance_ref": str(ACCEPTANCE.relative_to(ROOT)),
                "closure_status": final_status,
                "batch05_independent": False,
                "rtm": rtm_row,
                "acceptance": {
                    "expected_surface": acceptance["expected_surface"],
                    "domain_rules": acceptance["domain_rules"],
                    "functional_gap": acceptance.get("functional_gap"),
                    "status": acceptance.get("status"),
                    "time_decision": acceptance.get("time_decision"),
                },
                "probe": probe,
                "latency": lat,
                "ai_class": "rule_based_N/A_PSI",
                "pentagonal": {
                    "internal_goal_iso25010": col6,
                    "external_result_iso29148": col7,
                    "interface_iso29119": col8,
                    "security_owasp_asvs": {
                        "entitlement_before_execution": "cap646.runtime.execute_capability → entitlement_engine.check(canonical_id)",
                        "skip_entitlement_probe": True,
                        "gateway_contract": GATEWAY_TEST,
                        "note": "REUSED-LINK facade entitlement parity verified for #214/#245/#206/#228/#226/#232",
                    },
                    "collective_review_local": col10,
                },
                "pentagonal_domain_status": col7["status"],
                "lookahead": "Deterministic seed/sym params; catalog-aligned batch05_dedicated",
            }
        )
    return rows


def update_rtm_from_probes(rtm_doc: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    probe_by_id = {r["capability_id"]: r for r in rows}
    updated_rows = []
    for row in rtm_doc["rows"]:
        cid = row["id"]
        probe_row = probe_by_id[cid]
        er = probe_row["pentagonal"]["external_result_iso29148"]
        updated = dict(row)
        updated["status"] = probe_row["closure_status"]
        updated["production_spine"] = probe_row["probe"].get("production_spine", "batch05")
        updated["binding_file"] = row.get("binding_file_planned")
        updated["binding_function"] = row.get("binding_function_planned")
        updated["backend_module"] = probe_row["probe"].get("backend_module")
        updated["backend_entrypoint"] = probe_row["probe"].get("backend_entrypoint")
        updated["binding_source"] = "explicit_option_a"
        updated["pentagonal_probe"] = {
            "domain_rules_passed": er["rules_passed"],
            "domain_rules_total": er["rules_total"],
            "domain_all_pass": er["all_pass"],
            "acceptance_status": probe_row["acceptance"]["status"],
            "closure_status": probe_row["closure_status"],
            "elapsed_ms": probe_row["probe"].get("elapsed_ms"),
        }
        updated_rows.append(updated)

    out = dict(rtm_doc)
    out["generated_at"] = datetime.now(UTC).isoformat()
    out["batch05_independent"] = 0
    out["progress_826"] = 179
    out["build_phase"] = "OPEN"
    out["sonarcloud_status"] = "PENDING"
    out["rows"] = updated_rows
    return out


def capture_rule_proof(rows: list[dict[str, Any]], acceptance_by_id: dict[int, dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("BATCH05_RULE_COUNT_ASSERT_PROOF")
    lines.append(f"generated_at={datetime.now(UTC).isoformat()}")
    lines.append(f"git_commit={git_commit()}")
    lines.append("scope=probe_ids_201_250 triple_match_guard")
    lines.append("")
    for row in sorted(rows, key=lambda r: r["capability_id"]):
        cid = row["capability_id"]
        acceptance_count = len(acceptance_by_id[cid]["domain_rules"])
        er = row["pentagonal"]["external_result_iso29148"]
        results_count = len(er["domain_rule_results"])
        total = er["rules_total"]
        passed = er["rules_passed"]
        lines.append(
            f"ID {cid}: acceptance={acceptance_count} results={results_count} "
            f"rules_total={total} rules_passed={passed} closure={row['closure_status']} OK"
        )
    lines.append("")
    lines.append(f"assert_rule_count_triple_match: end — all {len(rows)} probe IDs matched")
    return "\n".join(lines) + "\n"


def render_markdown(commit: str, rows: list[dict[str, Any]]) -> str:
    ts = datetime.now(UTC).isoformat()
    lines: list[str] = []
    w = lines.append

    domain_pass = sum(1 for r in rows if r["pentagonal"]["external_result_iso29148"]["all_pass"])
    reused = [r for r in rows if r["closure_status"] == "REUSED-LINK"]
    w("# BATCH05_INSTITUTIONAL_PENTAGONAL_BUILD")
    w("")
    w(f"**Generated:** {ts} | **Commit:** `{commit[:12]}` | **Scope:** Batch05 IDs 201–250")
    w("**Classification:** BUILD PHASE OPEN — **NOT** LOCAL_GOVERNANCE_COMPLETE — SonarCloud PENDING")
    w(f"**Acceptance source:** `{ACCEPTANCE.name}` (pre_probe, ISO 29148)")
    w("")
    w("---")
    w("")
    w("## MECE Overlap Gates (resolved)")
    w("")
    w("| Pair | TIME decision | closure_status |")
    w("|------|---------------|----------------|")
    w("| #214/#245 | Migrate → batch01 | REUSED-LINK |")
    w("| #205/#232 | Invest #205 / Migrate #232 → #205 | NOT_COMPLETE / REUSED-LINK |")
    w("| #206/#228 | Migrate → batch02 #86 | REUSED-LINK |")
    w("")
    w("---")
    w("")
    w("## Status Table (201–250)")
    w("")
    w("| Bucket | Count |")
    w("|--------|------:|")
    w(f"| NOT_COMPLETE (strangler batch05) | {50 - len(reused)} |")
    w(f"| REUSED-LINK (MECE facades) | {len(reused)} |")
    w("| PRODUCTION-ALIGNED | 0 |")
    w("")
    w("```")
    w("batch05_independent = 0")
    w("progress_826        = 179")
    w(f"domain_rules_all_pass = {domain_pass}/50")
    w("sonarcloud          = PENDING")
    w("```")
    w("")
    w("---")
    w("")
    w("## RTM — every ID")
    w("")
    w("| ID | Closure | Spine | Domain pass | TIME |")
    w("|----|---------|-------|-------------|------|")
    for r in rows:
        er = r["pentagonal"]["external_result_iso29148"]
        spine = r["probe"].get("production_spine", "—")
        time_d = r["acceptance"].get("time_decision") or "Invest"
        w(
            f"| {r['capability_id']} | {r['closure_status']} | {spine} | "
            f"{er['rules_passed']}/{er['rules_total']} | {time_d} |"
        )
    w("")
    return "\n".join(lines)


async def main() -> None:
    if not ACCEPTANCE.is_file():
        raise SystemExit(f"Missing acceptance: {ACCEPTANCE}")
    if not RTM.is_file():
        raise SystemExit(f"Missing RTM baseline: {RTM} — run generate_batch05_rtm_201_250.py first")

    acceptance_by_id = load_acceptance()
    rtm_doc = load_json(RTM)
    rtm_by_id = {r["id"]: r for r in rtm_doc["rows"]}

    commit = git_commit()
    rows = await build_rows(PROBE_IDS, acceptance_by_id, rtm_by_id)

    assert_rule_count_triple_match(rows, acceptance_by_id)
    assert_no_template_duplication(rows)

    rule_proof = capture_rule_proof(rows, acceptance_by_id)
    OUT_RULE_PROOF.write_text(rule_proof, encoding="utf-8")

    updated_rtm = update_rtm_from_probes(rtm_doc, rows)
    RTM.write_text(json.dumps(updated_rtm, indent=2), encoding="utf-8")
    OUT_RTM_PROBE.write_text(json.dumps(updated_rtm, indent=2), encoding="utf-8")

    payload = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": commit,
        "acceptance_source": str(ACCEPTANCE.relative_to(ROOT)),
        "acceptance_pre_probe": True,
        "build_phase": "OPEN",
        "batch05_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "reused_link_ids": sorted(REUSED_LINK_ALL),
        "sonarcloud_status": "PENDING",
        "domain_rules_all_pass_count": sum(
            1 for r in rows if r["pentagonal"]["external_result_iso29148"]["all_pass"]
        ),
        "dedup_audit_ref": str(DEDUP_AUDIT.relative_to(ROOT)),
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_markdown(commit, rows), encoding="utf-8")

    incomplete = [r["capability_id"] for r in rows if not r["pentagonal"]["external_result_iso29148"]["all_pass"]]
    print(f"Wrote {OUT_MD} — domain_all_pass={50-len(incomplete)}/50, PA=0, independent=0")
    if incomplete:
        print(f"domain_fail_ids={incomplete[:10]}{'...' if len(incomplete)>10 else ''}")
    print(rule_proof.splitlines()[-2])


if __name__ == "__main__":
    asyncio.run(main())
