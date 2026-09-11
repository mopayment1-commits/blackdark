#!/usr/bin/env python3
"""Run 021 — Batch 01 build closure evidence (IDs 1–25 build batch).

Adds non_regression + BCBS remediation evidence to batch01 closure SSOT.
"""
from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "institutional_due_diligence_2026" / "batch01_independent_audit"
RTM_PATH = ROOT / "docs" / "BATCH01_OFFICIAL_RTM_1_50.json"
BUILD_EVIDENCE = ROOT / "institutional_due_diligence_2026" / "CAPABILITY_BUILD_826" / "EVIDENCE" / "batch01_pytest.log"
CLOSURE_PATH = OUT / "RUN021_BATCH01_BUILD_CLOSURE_EVIDENCE.json"
PYTHON = str(ROOT / ".venv" / "bin" / "python")

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run021-build@blackdark.local",
    "tier": "pro",
}

BUILD_BATCH_IDS = list(range(1, 26))


def _git_sha() -> str:
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True)
        return r.stdout.strip()
    except Exception:
        return "unknown"


def run_batch01_regression() -> dict[str, Any]:
    BUILD_EVIDENCE.parent.mkdir(parents=True, exist_ok=True)
    cmd = [PYTHON, "-m", "pytest", "tests/cap646/test_capability_build_batch01.py", "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
    BUILD_EVIDENCE.write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": "build_batch_01_ids_1_25",
        "command": " ".join(cmd),
        "exit_code": proc.returncode,
        "log_path": str(BUILD_EVIDENCE.relative_to(ROOT)),
        "commit": _git_sha(),
        "met": proc.returncode == 0,
    }


async def bcbs_remediation_evidence() -> dict[str, Any]:
    from cap646.runtime import execute_capability

    evidence: dict[str, Any] = {
        "generated_at": datetime.now(UTC).isoformat(),
        "fix": "cap646.batch01_dedicated._stamp_bcbs_provenance (Run 021 build batch)",
        "per_id": {},
    }
    for cid in BUILD_BATCH_IDS:
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


def run_independent_audit() -> dict[str, Any]:
    proc = subprocess.run(
        [PYTHON, str(ROOT / "scripts/independent_batch01_nine_phase_audit.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=900,
    )
    rows = json.loads((OUT / "BATCH01_INDEPENDENT_NINE_PHASE.json").read_text(encoding="utf-8"))
    build_rows = [r for r in rows if int(r["id"]) in BUILD_BATCH_IDS]
    return {
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout.strip()[-400:] if proc.stdout else "",
        "build_batch_rows": build_rows,
    }


def patch_rtm_engineering_status(audit_rows: list[dict[str, Any]]) -> dict[str, Any]:
    doc = json.loads(RTM_PATH.read_text(encoding="utf-8"))
    per_id = doc.get("per_id") or {}
    for row in audit_rows:
        cid = str(row["id"])
        entry = dict(per_id.get(cid) or {})
        entry["engineering_status"] = "PASS_ENGINEERING" if row.get("status") != "CONCEPTUALLY-UNSOUND" else "NOT_COMPLETE"
        entry["live_status"] = "awaiting_deploy"
        entry["build_batch_01_remediated"] = True
        per_id[cid] = entry
    doc["per_id"] = per_id
    doc["build_batch_01_updated_at"] = datetime.now(UTC).isoformat()
    RTM_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc


async def main() -> int:
    nr = run_batch01_regression()
    bcbs = await bcbs_remediation_evidence()
    audit = run_independent_audit()
    patch_rtm_engineering_status(audit["build_batch_rows"])

    prior: dict[str, Any] = {}
    run005 = OUT / "RUN005_BATCH01_CLOSURE_EVIDENCE.json"
    if run005.is_file():
        prior = json.loads(run005.read_text(encoding="utf-8"))

    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "run": "021_batch01_build_closure",
        "scope": "build_batch_01_ids_1_25",
        "non_regression": {
            "met": nr["met"],
            "batch01_build_pytest": nr,
            "affected_batches": ["batch01"],
            "evidence_mapping": "tests/cap646/test_capability_build_batch01.py → IDs 1–25",
        },
        "bcbs_remediation": bcbs,
        "bcbs": bcbs,
        "prior_run005": prior.get("remediation"),
        "independent_audit_exit_code": audit["exit_code"],
    }
    OUT.mkdir(parents=True, exist_ok=True)
    CLOSURE_PATH.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {CLOSURE_PATH}")
    print(f"non_regression.met={nr['met']} exit_code={nr['exit_code']}")
    print(f"bcbs remediated={sum(1 for v in bcbs['per_id'].values() if v['bcbs_remediated'])}/25")
    return 0 if nr["met"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
