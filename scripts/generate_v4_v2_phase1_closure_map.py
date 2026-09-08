#!/usr/bin/env python3
"""Generate v4_v2 Phase-1 closure map for all locally-buildable partial requirements."""

from __future__ import annotations

import json
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
    resolve_closure_domain,
)

LEDGER_PATH = ROOT / "docs/THREE_SPEC_INCREMENTAL_IMPLEMENTATION_LEDGER.json"
OUT_PATH = ROOT / "docs/V4_V2_PHASE1_CLOSURE_MAP.json"


def git_head() -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()


def load_partial_v4_v2() -> list[dict[str, Any]]:
    ledger = json.loads(LEDGER_PATH.read_text(encoding="utf-8"))
    return [
        r
        for r in ledger.get("requirements", [])
        if r.get("spec") == "v4_v2" and r.get("current_state") == "PARTIALLY_BUILT_VALID"
    ]


def main() -> None:
    partial = load_partial_v4_v2()
    rows: list[dict[str, Any]] = []
    domain_counts: Counter[str] = Counter()
    duplicate_ids: list[str] = []
    seen: set[str] = set()

    for req in partial:
        rid = str(req["requirement_id"])
        if rid in seen:
            duplicate_ids.append(rid)
            continue
        seen.add(rid)
        domain = resolve_closure_domain(req)
        domain_counts[domain] += 1
        closure = close_requirement(req)
        rows.append(
            {
                "requirement_id": rid,
                "source_sections": req.get("source_sections") or [],
                "source_text_summary": req.get("source_text_summary"),
                "requirement_type": req.get("requirement_type"),
                "implementation_nature": req.get("implementation_nature"),
                "shared_canonical_implementation": req.get("shared_canonical_implementation"),
                "closure_domain": domain,
                "closure_state": closure.get("closure_state"),
                "implementation_paths": closure.get("implementation_paths"),
                "cross_spec_overlap": closure.get("cross_spec_overlap"),
                "maturity_gate": rid in MATURITY_GATED_REQUIREMENT_IDS or bool(req.get("maturity_gate")),
                "remaining_delta_after_closure": closure.get("remaining_delta", ""),
            }
        )

    payload = {
        "artifact": "V4_V2_PHASE1_CLOSURE_MAP",
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "git_head": git_head(),
        "closure_universe_count": len(rows),
        "domain_distribution": dict(domain_counts),
        "maturity_gated_ids": sorted(MATURITY_GATED_REQUIREMENT_IDS),
        "V4_V2_CLOSURE_UNIVERSE_COMPLETE": len(rows) == 498,
        "V4_V2_DUPLICATE_REQUIREMENT_IDS": duplicate_ids,
        "V4_V2_REQUIREMENTS_WITHOUT_REMAINING_DELTA": [
            r["requirement_id"] for r in rows if not r.get("remaining_delta_after_closure") and r["closure_state"] == "LOCAL_ENGINEERING_COMPLETE"
        ][:5],
        "rows": rows,
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"written": str(OUT_PATH), "count": len(rows), "domains": dict(domain_counts)}, indent=2))


if __name__ == "__main__":
    main()
