"""Execute full RVM V&V and emit governing summary."""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from rvm.baseline import load_baseline, write_baseline
from rvm.build import build_rvm_matrix
from rvm.governing import write_governing_sources
from rvm.models import RVMSummary

_ROOT = Path(__file__).resolve().parent.parent
_RVM_OUT = _ROOT / "docs" / "rvm" / "RVM.json"
_SUMMARY_OUT = _ROOT / "docs" / "rvm" / "RVM_SUMMARY.json"


def _count_by_kind(rows: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    out: dict[str, Counter] = {}
    for row in rows:
        kind = row.get("kind", "unknown")
        status = row.get("final_status", "FAIL")
        out.setdefault(kind, Counter())[status] += 1
    return {k: dict(v) for k, v in out.items()}


async def run_rvm(*, concurrency: int = 40) -> dict[str, Any]:
    write_governing_sources()
    write_baseline()
    baseline = load_baseline()
    rows = await build_rvm_matrix(concurrency=concurrency)

    pass_count = sum(1 for r in rows if r["final_status"] == "PASS")
    fail_count = sum(1 for r in rows if r["final_status"] == "FAIL")
    external_count = sum(1 for r in rows if r["final_status"] == "EXTERNAL_EVIDENCE_REQUIRED")
    conflicts = sum(1 for r in rows if not r.get("reconciled", True))

    p0_external = [
        r["id"]
        for r in rows
        if r["final_status"] == "EXTERNAL_EVIDENCE_REQUIRED"
        and r["id"] in {"CAP-644", "CAP-645", "SEC-006", "SEC-008", "REL-002", "COM-P0-EXT"}
    ]

    commercial_ready = all(
        r["final_status"] == "PASS"
        for r in rows
        if r.get("kind") == "commercial" and r["id"] != "COM-P0-EXT"
    ) and "COM-P0-EXT" not in p0_external

    institutional_ready = all(
        r["final_status"] == "PASS" for r in rows if r.get("kind") == "institutional"
    )

    cap_pass = sum(1 for r in rows if r.get("kind") == "capability" and r["final_status"] == "PASS")
    cap_total = sum(1 for r in rows if r.get("kind") == "capability")

    if fail_count > 0:
        platform_verdict = "NOT YET A COMPLETE PLATFORM"
    elif external_count > 0:
        platform_verdict = "INTERNALLY COMPLETE — EXTERNAL EVIDENCE PENDING"
    else:
        platform_verdict = "VERIFIED COMPLETE PLATFORM"

    summary = RVMSummary(
        generated_at=datetime.now(UTC).isoformat(),
        governing_baseline_version=baseline.get("baseline_version", "blackdark-rvm-v1"),
        total_requirements=len(rows),
        pass_count=pass_count,
        fail_count=fail_count,
        external_count=external_count,
        by_kind=_count_by_kind(rows),
        platform_verdict=platform_verdict,
        commercial_ready=commercial_ready,
        institutional_ready=institutional_ready,
        conflicts_reconciled=conflicts,
        p0_external_remaining=p0_external,
    )

    output = {
        "generated_at": summary.generated_at,
        "baseline_version": summary.governing_baseline_version,
        "methodology": baseline.get("methodology", {}),
        "governing_sources": baseline.get("governing_sources", {}),
        "summary": summary.to_dict(),
        "capability_closure": {
            "pass": cap_pass,
            "total": cap_total,
            "percent": round(100.0 * cap_pass / cap_total, 2) if cap_total else 0,
        },
        "requirements": rows,
    }

    _RVM_OUT.parent.mkdir(parents=True, exist_ok=True)
    _RVM_OUT.write_text(json.dumps(output, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    _SUMMARY_OUT.write_text(json.dumps(summary.to_dict(), indent=2) + "\n", encoding="utf-8")
    return output


def load_rvm_summary() -> dict[str, Any]:
    if not _SUMMARY_OUT.is_file():
        return {}
    return json.loads(_SUMMARY_OUT.read_text(encoding="utf-8"))


def load_rvm() -> dict[str, Any]:
    if not _RVM_OUT.is_file():
        return {}
    return json.loads(_RVM_OUT.read_text(encoding="utf-8"))
