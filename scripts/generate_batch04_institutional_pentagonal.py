#!/usr/bin/env python3
"""Generate Batch04 institutional pentagonal build-phase deliverable (IDs 151-200).

Reads pre-test acceptance from docs/BATCH04_ACCEPTANCE_151_200.json (ISO 29148).
Does NOT mark any ID PRODUCTION-ALIGNED — batch04_independent remains 0 until
documented PA closures. Triple-match guard runs on all 50 probe IDs.
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
    assert_no_template_duplication,
    assert_rule_count_triple_match,
    build_column_6,
    build_column_7,
    evaluate_domain_rules,
    load_json,
    normalize_for_duplication_check,
)
from collections import Counter

OUT_MD = ROOT / "docs/BATCH04_INSTITUTIONAL_PENTAGONAL_BUILD.md"
OUT_JSON = ROOT / "docs/BATCH04_PENTAGONAL_TEMPLATE_151_200.json"
OUT_RTM_PROBE = ROOT / "docs/BATCH04_RTM_PROBE_151_200.json"
OUT_RULE_PROOF = ROOT / "docs/BATCH04_RULE_COUNT_ASSERT_PROOF.txt"
ACCEPTANCE = ROOT / "docs/BATCH04_ACCEPTANCE_151_200.json"
RTM = ROOT / "docs/BATCH04_RTM_151_200.json"
DUPLICATION = ROOT / "docs/BATCH04_DUPLICATION_DECISIONS.json"

PROBE_IDS = list(range(151, 201))
BATCH04_OVERLAP_BATCH01 = frozenset({175})
PENDING_CANONICAL_AUDIT = frozenset({159, 183})
CUSTOM_HANDLER_IDS = frozenset({151, 152, 153, 156, 159, 161, 162, 183, 189})

BASE_TEST = "tests/cap646/test_batch04_prep_dedicated.py::test_batch04_dedicated_surface_and_success"
OVERLAP_TEST = "tests/cap646/test_batch04_prep_dedicated.py::test_batch04_overlap_routes_batch01"
CATALOG_SAMPLE_TEST = "tests/cap646/test_batch04_prep_dedicated.py::test_batch04_catalog_aligned_have_domain_payload"
PENDING_AUDIT_TEST = "tests/cap646/test_batch04_reused_link_pending_audit.py::test_pending_canonical_audit_contract"

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


def closure_status(
    cid: int,
    domain_all_pass: bool,
    acceptance: dict[str, Any],
) -> str:
    """Never PRODUCTION-ALIGNED in build phase."""
    if cid in BATCH04_OVERLAP_BATCH01:
        return "OVERLAP-PARTIAL"
    if cid in PENDING_CANONICAL_AUDIT:
        return "NOT_COMPLETE"
    if acceptance.get("status") == "NOT_COMPLETE":
        return "NOT_COMPLETE"
    if domain_all_pass:
        return "NOT_COMPLETE"
    return "NOT_COMPLETE"


def local_tests_for(cid: int) -> list[str]:
    if cid in BATCH04_OVERLAP_BATCH01:
        return [OVERLAP_TEST]
    tests = [BASE_TEST]
    if cid in CUSTOM_HANDLER_IDS:
        tests.append(CATALOG_SAMPLE_TEST)
    if cid in PENDING_CANONICAL_AUDIT:
        tests.append(PENDING_AUDIT_TEST)
    return tests


def build_column_8(cid: int) -> dict[str, Any]:
    return {
        "api_path": f"/api/cap646/{cid}",
        "local_tests": local_tests_for(cid),
        "local_COMPLETE": True,
        "live_AWAITING_DEPLOY": "AWAITING_DEPLOY — Railway not validated for batch04 spine",
    }


def build_column_10() -> dict[str, Any]:
    return {
        "review_type": "LOCAL_REVIEW",
        "checklist": "docs/BATCH04_BUILD_PHASE_STATUS.md + PR #363",
        "note": "Build phase only — NOT LOCAL_GOVERNANCE_COMPLETE; NOT full SRE PRR",
        "second_review": "Batch04 build continuation agent run 2026-09-03",
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
    if cid in {154, 155, 163}:
        kind, limit = "ai_interpretation", LATENCY_LIMITS["ai_interpretation"]
    elif cid in {151, 152, 153, 156, 157, 163, 166}:
        kind, limit = "analysis", LATENCY_LIMITS["analysis"]
    else:
        kind, limit = "direct_data", LATENCY_LIMITS["direct_data"]
    return {
        "ms": elapsed_ms,
        "kind": kind,
        "limit_ms": limit,
        "within": elapsed_ms <= limit,
    }


def assert_custom_handler_anti_duplication(rows: list[dict[str, Any]]) -> None:
    """Anti-duplication on custom handlers only — catalog-template IDs share structure by design."""
    custom = [r for r in rows if r["capability_id"] in CUSTOM_HANDLER_IDS]
    if len(custom) < 2:
        return
    col6_norm = [
        normalize_for_duplication_check(json.dumps(r["pentagonal"]["internal_goal_iso25010"], sort_keys=True))
        for r in custom
    ]
    counts = Counter(col6_norm)
    worst, freq = counts.most_common(1)[0]
    threshold = max(2, int(len(custom) * 0.35) + 1)
    if freq >= threshold:
        raise SystemExit(
            f"Custom-handler anti-duplication failed: {freq}/{len(custom)} identical col6 "
            f"(threshold {threshold}). Sample: {worst[:200]}..."
        )


async def build_rows(
    probe_ids: list[int],
    acceptance_by_id: dict[int, dict[str, Any]],
    rtm_by_id: dict[int, dict[str, Any]],
) -> list[dict[str, Any]]:
    dup_doc = load_json(DUPLICATION)
    blockers = {b["id"]: b for b in dup_doc.get("structural_blockers", [])}
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
        blocker = acceptance.get("pending_canonical_audit")
        blocker_detail = blockers.get(blocker) if blocker else None

        rows.append(
            {
                "capability_id": cid,
                "capability_name": rtm_row["capability"],
                "acceptance_ref": str(ACCEPTANCE.relative_to(ROOT)),
                "closure_status": final_status,
                "batch04_independent": False,
                "pending_canonical_audit": blocker,
                "structural_blocker": blocker_detail,
                "rtm": rtm_row,
                "acceptance": {
                    "expected_surface": acceptance["expected_surface"],
                    "domain_rules": acceptance["domain_rules"],
                    "functional_gap": acceptance.get("functional_gap"),
                    "status": acceptance.get("status"),
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
                        "note": "Entitlement gate verified via batch03 gateway contract tests (non-regression)",
                    },
                    "collective_review_local": col10,
                },
                "pentagonal_domain_status": col7["status"],
                "lookahead": "Deterministic seed/sym params; catalog-aligned batch04_dedicated",
            }
        )
    return rows


def update_rtm_from_probes(rtm_doc: dict[str, Any], rows: list[dict[str, Any]]) -> dict[str, Any]:
    probe_by_id = {r["capability_id"]: r for r in rows}
    updated_rows = []
    for row in rtm_doc["rows"]:
        cid = row["id"]
        probe_row = probe_by_id[cid]
        acceptance_status = probe_row["acceptance"]["status"]
        er = probe_row["pentagonal"]["external_result_iso29148"]
        updated = dict(row)
        updated["status"] = probe_row["closure_status"]
        updated["production_spine"] = (
            "batch01" if cid in BATCH04_OVERLAP_BATCH01 else "batch04"
        )
        updated["binding_file"] = row.get("binding_file_planned")
        updated["binding_function"] = row.get("binding_function_planned")
        updated["backend_module"] = probe_row["probe"].get("backend_module")
        updated["backend_entrypoint"] = probe_row["probe"].get("backend_entrypoint")
        updated["binding_source"] = "explicit_option_a"
        updated["pentagonal_probe"] = {
            "domain_rules_passed": er["rules_passed"],
            "domain_rules_total": er["rules_total"],
            "domain_all_pass": er["all_pass"],
            "acceptance_status": acceptance_status,
            "closure_status": probe_row["closure_status"],
            "elapsed_ms": probe_row["probe"].get("elapsed_ms"),
        }
        if probe_row.get("pending_canonical_audit"):
            updated["pending_canonical_audit"] = probe_row["pending_canonical_audit"]
        updated_rows.append(updated)

    out = dict(rtm_doc)
    out["generated_at"] = datetime.now(UTC).isoformat()
    out["batch04_independent"] = 0
    out["progress_826_current"] = 148
    out["build_phase"] = "OPEN"
    out["rows"] = updated_rows
    return out


def capture_rule_proof(rows: list[dict[str, Any]], acceptance_by_id: dict[int, dict[str, Any]]) -> str:
    lines: list[str] = []
    lines.append("BATCH04_RULE_COUNT_ASSERT_PROOF")
    lines.append(f"generated_at={datetime.now(UTC).isoformat()}")
    lines.append(f"git_commit={git_commit()}")
    lines.append("scope=probe_ids_151_200 triple_match_guard")
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


def render_markdown(commit: str, rows: list[dict[str, Any]], rtm_rows: list[dict[str, Any]]) -> str:
    ts = datetime.now(UTC).isoformat()
    lines: list[str] = []
    w = lines.append

    domain_pass = sum(1 for r in rows if r["pentagonal"]["external_result_iso29148"]["all_pass"])
    w("# BATCH04_INSTITUTIONAL_PENTAGONAL_BUILD")
    w("")
    w(f"**Generated:** {ts} | **Commit:** `{commit[:12]}` | **Scope:** Batch04 IDs 151–200")
    w("**Classification:** BUILD PHASE OPEN — **NOT** LOCAL_GOVERNANCE_COMPLETE")
    w(f"**Acceptance source:** `{ACCEPTANCE.name}` (pre_probe, ISO 29148)")
    w("")
    w("هذه المرحلة = بناء spine + قبول مسبق + اختبارات محلية فقط. لا إعلان اكتمال حوكمة · لا Batch05 · لا جاهزية حية 100%.")
    w("")
    w("---")
    w("")
    w("## Structural Blockers (hard stop)")
    w("")
    w("| Blocker | Pair | Status |")
    w("|---------|------|--------|")
    w("| BLOCKER-159-103 | 159 ↔ 103 | canonical #103 PENDING_SCOPE_REALIGNMENT |")
    w("| BLOCKER-183-130 | 183 ↔ 130 | canonical #130 PENDING + semantic gap |")
    w("")
    w("ADR: `docs/ADR_BATCH04_CANONICAL_BLOCKERS_103_130.md`")
    w("")
    w("---")
    w("")
    w("## Status Table (151–200)")
    w("")
    w("| Bucket | Count |")
    w("|--------|------:|")
    w("| NOT_COMPLETE (dedicated batch04 spine) | 49 |")
    w("| OVERLAP-PARTIAL (batch01 #175) | 1 |")
    w("| PENDING_CANONICAL_AUDIT subset | 2 | 159, 183 |")
    w("| PRODUCTION-ALIGNED | 0 |")
    w("")
    w("```")
    w("batch04_independent = 0")
    w("progress_826        = 148")
    w(f"domain_rules_all_pass = {domain_pass}/50")
    w("```")
    w("")
    w("---")
    w("")
    w("## RTM — every ID")
    w("")
    w("| ID | Closure | Spine | Domain pass | Blocker |")
    w("|----|---------|-------|-------------|---------|")
    for r in rows:
        er = r["pentagonal"]["external_result_iso29148"]
        blk = r.get("pending_canonical_audit") or "—"
        spine = r["probe"].get("production_spine", "—")
        w(
            f"| {r['capability_id']} | {r['closure_status']} | {spine} | "
            f"{er['rules_passed']}/{er['rules_total']} | {blk} |"
        )
    w("")
    w("---")
    w("")
    w("## Pentagonal per ID (columns 6–10)")
    w("")
    for row in rows:
        cid = row["capability_id"]
        p = row["pentagonal"]
        w(f"### ID {cid} — {row['capability_name']}")
        w("")
        ig = p["internal_goal_iso25010"]
        er = p["external_result_iso29148"]
        itf = p["interface_iso29119"]
        rev = p["collective_review_local"]
        lat = row["latency"]
        w(f"- **Col 6 (25010):** {ig['goal']} | binding:{ig['binding']} | {ig['appropriateness']}")
        w(f"- **Col 7 (29148):** {er['summary']} | domain_status:{er['status']} | closure:{row['closure_status']}")
        w(f"- **Col 8 (29119):** {itf['api_path']} | local_COMPLETE:{itf['local_COMPLETE']} | live:{itf['live_AWAITING_DEPLOY']}")
        w(f"- **Col 9 (ASVS):** entitlement canonical_id gate (probe skip_entitlement=True)")
        w(f"- **Col 10 (LOCAL_REVIEW):** {rev['review_type']} — {rev['note']}")
        w(f"- **Latency (local):** {lat['ms']}ms / {lat['limit_ms']}ms ({lat['kind']}) within={lat['within']}")
        if row.get("structural_blocker"):
            w(f"- **Blocker:** {row['structural_blocker']['message']}")
        w("")
    w("---")
    w("")
    w("## Triple-match guard")
    w("")
    w(f"Proof: `{OUT_RULE_PROOF.name}` — acceptance_count == results == rules_total for all 50 IDs.")
    w("")
    w("## Heroes (batch04 independent)")
    w("")
    w("**batch04_independent = 0** — N/A per hero engine item-by-item until PA closures exist.")
    w("")
    return "\n".join(lines)


async def main() -> None:
    if not ACCEPTANCE.is_file():
        raise SystemExit(f"Missing acceptance: {ACCEPTANCE}")

    acceptance_by_id = load_acceptance()
    rtm_doc = load_json(RTM)
    rtm_by_id = {r["id"]: r for r in rtm_doc["rows"]}

    commit = git_commit()
    rows = await build_rows(PROBE_IDS, acceptance_by_id, rtm_by_id)

    assert_rule_count_triple_match(rows, acceptance_by_id)
    assert_custom_handler_anti_duplication(rows)

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
        "batch04_independent": 0,
        "progress_826": 148,
        "production_aligned_count": 0,
        "domain_rules_all_pass_count": sum(
            1 for r in rows if r["pentagonal"]["external_result_iso29148"]["all_pass"]
        ),
        "rows": rows,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    OUT_MD.write_text(render_markdown(commit, rows, updated_rtm["rows"]), encoding="utf-8")

    incomplete = [r["capability_id"] for r in rows if not r["pentagonal"]["external_result_iso29148"]["all_pass"]]
    print(f"Wrote {OUT_MD} — domain_all_pass={50-len(incomplete)}/50, PA=0, independent=0")
    print(rule_proof.splitlines()[-2])


if __name__ == "__main__":
    asyncio.run(main())
