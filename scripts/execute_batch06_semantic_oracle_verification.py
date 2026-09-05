#!/usr/bin/env python3
"""Batch06 semantic oracle verification — actual vs expected for IDs 251-300."""

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
    evaluate_domain_rules,
    load_json,
)

ACCEPTANCE = ROOT / "docs/BATCH06_ACCEPTANCE_251_300.json"
OUT = ROOT / "docs/BATCH06_SEMANTIC_ORACLE_VERIFICATION.json"

WEAK_FIELDS = frozenset({"success"})


def git_commit() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def classify_rules(domain_rules: list[dict[str, Any]]) -> tuple[list[dict], list[dict]]:
    weak: list[dict] = []
    semantic: list[dict] = []
    for rule in domain_rules:
        if rule.get("field") in WEAK_FIELDS:
            weak.append(rule)
        else:
            semantic.append(rule)
    return weak, semantic


def classify_oracle_strength(semantic_results: list[dict[str, Any]]) -> str:
    if not semantic_results:
        return "WEAK_ONLY_NO_SEMANTIC_RULES"
    passed = sum(1 for r in semantic_results if r["pass"])
    if passed == len(semantic_results):
        return "SEMANTIC_VERIFIED_LOCAL"
    if passed == 0:
        return "SEMANTIC_FAIL"
    return "SEMANTIC_PARTIAL"


async def probe_id(cid: int) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    t0 = time.perf_counter()
    probe = await execute_capability(cid, params={"symbol": "BTC", "tier": "pro"}, skip_entitlement=True)
    elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
    probe["elapsed_ms"] = elapsed_ms
    probe["capability_id"] = cid
    return probe


async def main() -> None:
    if not ACCEPTANCE.is_file():
        raise SystemExit(f"Missing {ACCEPTANCE} — run generate_batch06_acceptance_251_300.py first")

    acceptance_doc = load_json(ACCEPTANCE)
    acceptance_by_id = {r["capability_id"]: r for r in acceptance_doc["rows"]}
    rows: list[dict[str, Any]] = []

    for cid in range(251, 301):
        acc = acceptance_by_id[cid]
        probe = await probe_id(cid)
        rule_results = evaluate_domain_rules(probe, acc)
        _, semantic_rules = classify_rules(acc["domain_rules"])
        semantic_results = [r for r in rule_results if r["field"] not in WEAK_FIELDS]
        all_pass = all(r["pass"] for r in rule_results)
        semantic_pass = all(r["pass"] for r in semantic_results) if semantic_results else False
        strength = classify_oracle_strength(semantic_results)

        functional_status = "PASS_ENGINEERING_LOCAL"
        if not semantic_results:
            functional_status = "DOWNGRADED_WEAK_ONLY"
        elif not semantic_pass:
            functional_status = "DOWNGRADED_SEMANTIC_FAIL"

        rows.append(
            {
                "capability_id": cid,
                "capability_name": acc.get("capability_name"),
                "expected_surface": acc["expected_surface"],
                "probe_success": probe.get("success"),
                "probe_surface": probe.get("surface"),
                "production_spine": probe.get("production_spine"),
                "closure_status": probe.get("closure_status"),
                "elapsed_ms": probe.get("elapsed_ms"),
                "domain_rules_total": len(rule_results),
                "domain_rules_passed": sum(1 for r in rule_results if r["pass"]),
                "semantic_rules_count": len(semantic_rules),
                "semantic_rules_passed": sum(1 for r in semantic_results if r["pass"]),
                "all_domain_rules_pass": all_pass,
                "semantic_oracle_pass": semantic_pass,
                "oracle_strength": strength,
                "functional_status": functional_status,
                "semantic_rule_results": semantic_results,
                "failed_semantic_rules": [r for r in semantic_results if not r["pass"]],
            }
        )

    semantic_verified = sum(1 for r in rows if r["semantic_oracle_pass"])
    downgraded = sum(1 for r in rows if r["functional_status"].startswith("DOWNGRADED"))

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": git_commit(),
        "standard": "Project Standards v2 — semantic oracle actual-vs-expected",
        "scope": "Batch06 IDs 251-300",
        "policy": "success=true alone is insufficient; semantic rules must pass for PASS_ENGINEERING",
        "batch06_independent": 0,
        "progress_826": 179,
        "production_aligned_count": 0,
        "summary": {
            "total_ids": 50,
            "semantic_verified_local": semantic_verified,
            "downgraded_count": downgraded,
            "all_domain_rules_pass": sum(1 for r in rows if r["all_domain_rules_pass"]),
            "reused_link_verified": sum(
                1 for r in rows if r["capability_id"] in acceptance_doc.get("reused_link_ids", []) and r["semantic_oracle_pass"]
            ),
        },
        "rows": rows,
    }
    OUT.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    print(
        f"Wrote {OUT.name} — semantic_verified={semantic_verified}/50 downgraded={downgraded}"
    )


if __name__ == "__main__":
    asyncio.run(main())
