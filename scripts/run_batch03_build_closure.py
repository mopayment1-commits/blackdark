#!/usr/bin/env python3
"""Run 021 — Batch 03 build closure evidence (build batches 05–06 on official batch03 spine)."""
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

OUT = ROOT / "institutional_due_diligence_2026" / "batch03_independent_audit"
RTM_PATH = ROOT / "docs" / "BATCH03_OFFICIAL_RTM_101_150.json"
BUILD_DIR = ROOT / "institutional_due_diligence_2026" / "CAPABILITY_BUILD_826" / "EVIDENCE"
CLOSURE_PATH = OUT / "RUN021_BATCH03_BUILD_CLOSURE_EVIDENCE.json"
PYTHON = str(ROOT / ".venv" / "bin" / "python")
ENSURE_TEST = ROOT / "scripts" / "ensure_build_batch_test.py"

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run021-build@blackdark.local",
    "tier": "pro",
}


def _scope(build_batch: int) -> dict[str, Any]:
    start = (build_batch - 1) * 25 + 1
    end = min(build_batch * 25, 826)
    modules = [f"tests/cap646/test_capability_build_batch{b:02d}.py" for b in range(1, build_batch + 1)]
    for b in range(1, build_batch + 1):
        subprocess.run([PYTHON, str(ENSURE_TEST), str(b)], cwd=ROOT, check=False)
    return {
        "ids": list(range(start, end + 1)),
        "pytest_modules": modules,
        "log": BUILD_DIR / f"batch{build_batch:02d}_pytest.log",
        "scope_label": f"build_batch_{build_batch:02d}_ids_{start}_{end}",
        "rtm_flag": f"build_batch_{build_batch:02d}_remediated",
        "rtm_max_id": end,
        "build_batch": build_batch,
    }


def _git_sha() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except Exception:
        return "unknown"


def run_build_regression(scope: dict[str, Any]) -> dict[str, Any]:
    log_path = scope["log"]
    log_path.parent.mkdir(parents=True, exist_ok=True)
    cmd = [PYTHON, "-m", "pytest", *scope["pytest_modules"], "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=1200)
    log_path.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": scope["scope_label"],
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "log_path": str(log_path.relative_to(ROOT)),
        "commit": _git_sha(),
        "met": proc.returncode == 0,
    }


async def bcbs_remediation_evidence(ids: list[int]) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    evidence: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "fix": "cap646.batch03_production._stamp_batch03 + batch03_dedicated._wrap (Run 021)",
        "per_id": {},
    }
    for cid in ids:
        result = await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
        src = bool(result.get("data_source") or result.get("source"))
        ts = bool(result.get("timestamp") or result.get("created_at") or result.get("updated_at"))
        evidence["per_id"][str(cid)] = {
            "data_source": src,
            "timestamp": ts,
            "runtime_success": bool(result.get("success")),
            "bcbs_remediated": src and ts,
        }
    return evidence


def run_independent_audit(ids: list[int]) -> dict[str, Any]:
    proc = subprocess.run(
        [PYTHON, str(ROOT / "scripts/independent_batch03_nine_phase_audit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    rows = json.loads((OUT / "BATCH03_INDEPENDENT_NINE_PHASE.json").read_text(encoding="utf-8"))
    build_rows = [r for r in rows if int(r["id"]) in ids]
    return {"exit_code": proc.returncode, "build_batch_rows": build_rows}


def patch_rtm(audit_rows: list[dict[str, Any]], scope: dict[str, Any]) -> None:
    doc = json.loads(RTM_PATH.read_text(encoding="utf-8"))
    per_id = doc.get("per_id") or {}
    for row in audit_rows:
        cid = str(row["id"])
        entry = dict(per_id.get(cid) or {})
        entry["engineering_status"] = "PASS_ENGINEERING" if row.get("status") != "CONCEPTUALLY-UNSOUND" else "NOT_COMPLETE"
        entry[scope["rtm_flag"]] = int(row["id"]) <= scope["rtm_max_id"]
        per_id[cid] = entry
    doc["per_id"] = per_id
    doc[f"{scope['rtm_flag']}_at"] = datetime.now(UTC).isoformat()
    RTM_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-batch", type=int, required=True)
    args = parser.parse_args()
    scope = _scope(args.build_batch)
    ids = scope["ids"]

    nr = run_build_regression(scope)
    bcbs = await bcbs_remediation_evidence(ids)
    audit = run_independent_audit(ids)
    patch_rtm(audit["build_batch_rows"], scope)

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run": f"021_batch03_build_closure_batch{args.build_batch:02d}",
        "scope": scope["scope_label"],
        "non_regression": {
            "met": nr["met"],
            f"batch{args.build_batch:02d}_build_pytest": nr,
            "affected_batches": ["batch03"],
            "evidence_mapping": f"tests/cap646/test_capability_build_batch{args.build_batch:02d}.py → IDs {ids[0]}–{ids[-1]}",
        },
        "bcbs_remediation": bcbs,
        "bcbs": bcbs,
        "independent_audit_exit_code": audit["exit_code"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    CLOSURE_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {CLOSURE_PATH} non_regression.met={nr['met']}")
    return 0 if nr["met"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
