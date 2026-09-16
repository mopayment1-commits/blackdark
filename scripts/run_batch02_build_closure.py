#!/usr/bin/env python3
"""Run 021 — Batch 02 build closure evidence (build batches 03–04 on official batch02 spine).

Adds non_regression + BCBS remediation evidence to batch02 closure SSOT.
"""
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

OUT = ROOT / "institutional_due_diligence_2026" / "batch02_independent_audit"
RTM_PATH = ROOT / "docs" / "BATCH02_OFFICIAL_RTM_51_100.json"
BUILD_DIR = ROOT / "institutional_due_diligence_2026" / "CAPABILITY_BUILD_826" / "EVIDENCE"
CLOSURE_PATH = OUT / "RUN021_BATCH02_BUILD_CLOSURE_EVIDENCE.json"
PYTHON = str(ROOT / ".venv" / "bin" / "python")

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run021-build@blackdark.local",
    "tier": "pro",
}

BUILD_SCOPES: dict[int, dict[str, Any]] = {
    3: {
        "ids": list(range(51, 76)),
        "pytest_modules": [
            "tests/cap646/test_capability_build_batch01.py",
            "tests/cap646/test_capability_build_batch02.py",
            "tests/cap646/test_capability_build_batch03.py",
        ],
        "log": BUILD_DIR / "batch03_pytest.log",
        "scope_label": "build_batch_03_ids_51_75",
        "rtm_flag": "build_batch_03_remediated",
        "rtm_max_id": 75,
    },
    4: {
        "ids": list(range(76, 101)),
        "pytest_modules": [
            "tests/cap646/test_capability_build_batch01.py",
            "tests/cap646/test_capability_build_batch02.py",
            "tests/cap646/test_capability_build_batch03.py",
            "tests/cap646/test_capability_build_batch04.py",
        ],
        "log": BUILD_DIR / "batch04_pytest.log",
        "scope_label": "build_batch_04_ids_76_100",
        "rtm_flag": "build_batch_04_remediated",
        "rtm_max_id": 100,
    },
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
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=900)
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
        "fix": "cap646.batch02_production._stamp_batch02 (Run 021 build batch 03)",
        "per_id": {},
    }
    for cid in ids:
        result = await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
        src = bool(result.get("data_source") or result.get("source"))
        ts = bool(
            result.get("timestamp")
            or result.get("created_at")
            or result.get("updated_at")
        )
        qual = bool(result.get("quality"))
        evidence["per_id"][str(cid)] = {
            "data_source": src,
            "timestamp": ts,
            "quality": qual,
            "runtime_success": bool(result.get("success")),
            "bcbs_remediated": src and ts,
        }
    return evidence


def run_independent_audit(ids: list[int]) -> dict[str, Any]:
    proc = subprocess.run(
        [PYTHON, str(ROOT / "scripts/independent_batch02_nine_phase_audit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    rows = json.loads((OUT / "BATCH02_INDEPENDENT_NINE_PHASE.json").read_text(encoding="utf-8"))
    build_rows = [r for r in rows if int(r["id"]) in ids]
    return {
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout.strip()[-400:] if proc.stdout else "",
        "build_batch_rows": build_rows,
    }


def patch_rtm_engineering_status(audit_rows: list[dict[str, Any]], scope: dict[str, Any]) -> dict[str, Any]:
    doc = json.loads(RTM_PATH.read_text(encoding="utf-8"))
    per_id = doc.get("per_id") or {}
    for row in audit_rows:
        cid = str(row["id"])
        entry = dict(per_id.get(cid) or {})
        entry["engineering_status"] = "PASS_ENGINEERING" if row.get("status") != "CONCEPTUALLY-UNSOUND" else "NOT_COMPLETE"
        entry["live_status"] = "awaiting_deploy"
        entry[scope["rtm_flag"]] = int(row["id"]) <= scope["rtm_max_id"]
        per_id[cid] = entry
    doc["per_id"] = per_id
    doc[f"{scope['rtm_flag']}_at"] = datetime.now(UTC).isoformat()
    RTM_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-batch", type=int, default=3, choices=[3, 4])
    args = parser.parse_args()
    scope = BUILD_SCOPES[args.build_batch]
    ids = scope["ids"]

    nr = run_build_regression(scope)
    bcbs = await bcbs_remediation_evidence(ids)
    audit = run_independent_audit(ids)
    patch_rtm_engineering_status(audit["build_batch_rows"], scope)

    prior: dict[str, Any] = {}
    run007 = OUT / "RUN007_BATCH02_CLOSURE_EVIDENCE.json"
    if run007.is_file():
        prior = json.loads(run007.read_text(encoding="utf-8"))

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run": f"021_batch02_build_closure_batch{args.build_batch:02d}",
        "scope": scope["scope_label"],
        "non_regression": {
            "met": nr["met"],
            f"batch{args.build_batch:02d}_build_pytest": nr,
            "affected_batches": ["batch02"],
            "evidence_mapping": f"tests/cap646/test_capability_build_batch{args.build_batch:02d}.py → IDs {ids[0]}–{ids[-1]}",
        },
        "bcbs_remediation": bcbs,
        "bcbs": bcbs,
        "prior_run007": prior.get("remediation"),
        "independent_audit_exit_code": audit["exit_code"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    CLOSURE_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {CLOSURE_PATH}")
    print(f"non_regression.met={nr['met']} exit_code={nr['exit_code']}")
    print(f"bcbs remediated={sum(1 for v in bcbs['per_id'].values() if v['bcbs_remediated'])}/{len(ids)}")
    return 0 if nr["met"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
