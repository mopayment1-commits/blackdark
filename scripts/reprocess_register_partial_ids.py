#!/usr/bin/env python3
"""Re-process specific REGISTER rows after ui_pages /execute fix — no full 826 rebuild."""
from __future__ import annotations

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.capability_build_826_executor import (  # noqa: E402
    BUILD_DIR,
    PROGRESS_LOG,
    PYTHON,
    REGISTER_PATH,
    _core_gates_clean,
    _git_sha,
    audit_ids,
    load_register,
    runtime_probe,
    write_heroes_binding_index,
)

DEFAULT_IDS = [129, 175, 214, 245, 338, 500, 507, 534, 584]


def _now() -> str:
    return datetime.now(UTC).isoformat()


def build_batch_for_id(cid: int) -> int:
    return (cid - 1) // 25 + 1


async def reprocess_ids(ids: list[int]) -> dict[str, Any]:
    from cap646.build826_heroes import enrich_binding_row, hero_binding_for

    reg = load_register()
    rows_by_id = {r["id"]: r for r in reg["rows"]}
    runtime = await runtime_probe(ids)
    audits = await audit_ids(ids)

    results: list[dict[str, Any]] = []
    complete = engineering = partial = failed = unbound = 0

    for cid in ids:
        row = rows_by_id[cid]
        aud = audits[cid]
        rt = runtime[cid]
        failures = aud.get("failure_columns", [])
        binding = hero_binding_for(cid)
        row.update(binding)
        enrich_binding_row(cid, row)

        prior = row.get("status")
        if aud.get("fully_v6_compliant") and rt.get("success") and binding["hero_binding_status"] == "BOUND":
            row["status"] = "COMPLETE_V6"
            row["v6_fully_compliant"] = True
            row["blocker"] = None
            complete += 1
        elif not rt.get("success"):
            row["status"] = "FAILED_GATE"
            row["v6_fully_compliant"] = False
            row["blocker"] = rt.get("error") or "runtime_fail"
            failed += 1
        elif binding["hero_binding_status"] == "UNBOUND":
            row["status"] = "PARTIAL"
            row["v6_fully_compliant"] = False
            row["blocker"] = ["hero_binding:UNBOUND", *failures[:4]]
            partial += 1
            unbound += 1
        elif _core_gates_clean(failures):
            row["status"] = "ENGINEERING_READY"
            row["v6_fully_compliant"] = False
            row["blocker"] = failures[:6]
            engineering += 1
        else:
            row["status"] = "PARTIAL"
            row["v6_fully_compliant"] = False
            row["blocker"] = failures[:6]
            partial += 1

        row["runtime_success"] = rt.get("success")
        row["updated_at"] = _now()
        results.append(
            {
                "id": cid,
                "prior_status": prior,
                "status": row["status"],
                "hero_binding_status": row.get("hero_binding_status"),
                "failures": failures[:6],
            }
        )

    reg["generated_at"] = _now()
    REGISTER_PATH.write_text(json.dumps(reg, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_heroes_binding_index(reg)

    complete_total = sum(1 for r in reg["rows"] if r["status"] == "COMPLETE_V6")
    eng_total = sum(1 for r in reg["rows"] if r["status"] == "ENGINEERING_READY")
    partial_total = sum(1 for r in reg["rows"] if r["status"] == "PARTIAL")
    failed_total = sum(1 for r in reg["rows"] if r["status"] == "FAILED_GATE")
    unbound_total = sum(
        1 for r in reg["rows"] if r.get("hero_binding_status") == "UNBOUND" and r["id"] <= 826
    )

    log_line = (
        f"{_now()} PARTIAL_REPROCESS | ids={','.join(str(i) for i in ids)} | "
        f"complete_v6={complete}/{len(ids)} (total {complete_total}/826) | "
        f"engineering_ready={engineering} (total {eng_total}) | partial={partial} (total {partial_total}) | "
        f"failed={failed} (total {failed_total}) | unbound={unbound} (total {unbound_total}) | sha={_git_sha()}"
    )
    with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(log_line + "\n")

    report = BUILD_DIR / "PARTIAL_REPROCESS_REPORT.json"
    report.write_text(
        json.dumps(
            {
                "generated_at": _now(),
                "ids": ids,
                "results": results,
                "summary": {
                    "promoted_complete_v6": complete,
                    "promoted_engineering_ready": engineering,
                    "still_partial": partial,
                    "failed_gate": failed,
                    "complete_v6_total": complete_total,
                    "engineering_ready_total": eng_total,
                    "partial_total": partial_total,
                    "failed_gate_total": failed_total,
                    "unbound_total": unbound_total,
                },
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return {"log_line": log_line, "results": results, "summary": json.loads(report.read_text())["summary"]}


def run_pytests(ids: list[int]) -> dict[str, Any]:
    batches = sorted({build_batch_for_id(cid) for cid in ids})
    ev_dir = BUILD_DIR / "EVIDENCE"
    ev_dir.mkdir(parents=True, exist_ok=True)
    log_path = ev_dir / "partial_reprocess_pytest.log"
    test_files = [
        ROOT / f"tests/cap646/test_capability_build_batch{b:02d}.py"
        for b in batches
        if (ROOT / f"tests/cap646/test_capability_build_batch{b:02d}.py").is_file()
    ]
    if not test_files:
        return {"passed": False, "log": str(log_path.relative_to(ROOT)), "exit_code": 1}
    rel = [str(p.relative_to(ROOT)) for p in test_files]
    proc = subprocess.run(
        [PYTHON, "-m", "pytest", *rel, "-q", "--tb=short"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return {"passed": proc.returncode == 0, "log": str(log_path.relative_to(ROOT)), "exit_code": proc.returncode}


async def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", default=",".join(str(i) for i in DEFAULT_IDS))
    ap.add_argument("--skip-tests", action="store_true")
    args = ap.parse_args()
    ids = [int(x.strip()) for x in args.ids.split(",") if x.strip()]

    if not args.skip_tests:
        tests = run_pytests(ids)
        print(f"pytest exit={tests['exit_code']} log={tests['log']}")
        if not tests["passed"]:
            return 1

    out = await reprocess_ids(ids)
    print(out["log_line"])
    for r in out["results"]:
        print(f"  {r['id']}: {r['prior_status']} -> {r['status']} failures={r['failures'][:3]}")
    return 0 if out["summary"]["failed_gate"] == 0 and out["summary"]["unbound_total"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
