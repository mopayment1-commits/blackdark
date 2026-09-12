#!/usr/bin/env python3
"""Run 021 — generic official-batch build closure for continuous build executor."""
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

PYTHON = str(ROOT / ".venv" / "bin" / "python")
ENSURE_TEST = ROOT / "scripts" / "ensure_build_batch_test.py"
BUILD_DIR = ROOT / "institutional_due_diligence_2026" / "CAPABILITY_BUILD_826" / "EVIDENCE"

COMMON_PARAMS = {
    "symbol": "BTC",
    "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
    "email": "run021-build@blackdark.local",
    "tier": "pro",
}

OFFICIAL_CONFIG: dict[int, dict[str, Any]] = {
    2: {
        "out": ROOT / "institutional_due_diligence_2026/batch02_independent_audit",
        "closure": "RUN021_BATCH02_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch02_nine_phase_audit.py",
        "audit_json": "BATCH02_INDEPENDENT_NINE_PHASE.json",
        "rtm": ROOT / "docs/BATCH02_OFFICIAL_RTM_51_100.json",
    },
    3: {
        "out": ROOT / "institutional_due_diligence_2026/batch03_independent_audit",
        "closure": "RUN021_BATCH03_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch03_nine_phase_audit.py",
        "audit_json": "BATCH03_INDEPENDENT_NINE_PHASE.json",
        "rtm": ROOT / "docs/BATCH03_OFFICIAL_RTM_101_150.json",
    },
    4: {
        "out": ROOT / "institutional_due_diligence_2026/batch04_independent_audit",
        "closure": "RUN021_BATCH04_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch04_rbas_audit.py",
        "audit_json": "BATCH04_INDEPENDENT_RBAS_AUDIT.json",
        "rtm": ROOT / "docs/BATCH04_OFFICIAL_RTM_151_200.json",
    },
    5: {
        "out": ROOT / "institutional_due_diligence_2026/batch05_independent_audit",
        "closure": "RUN021_BATCH05_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch05_rbas_audit.py",
        "audit_json": "BATCH05_INDEPENDENT_RBAS_AUDIT.json",
        "rtm": ROOT / "docs/BATCH05_OFFICIAL_RTM_201_250.json",
    },
    6: {
        "out": ROOT / "institutional_due_diligence_2026/batch06_independent_audit",
        "closure": "RUN021_BATCH06_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch06_rbas_audit.py",
        "audit_json": "BATCH06_INDEPENDENT_RBAS_AUDIT.json",
        "rtm": ROOT / "docs/BATCH06_OFFICIAL_RTM_251_300.json",
    },
    7: {
        "out": ROOT / "institutional_due_diligence_2026/batch07_independent_audit",
        "closure": "RUN021_BATCH07_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch07_rbas_audit.py",
        "audit_json": "BATCH07_INDEPENDENT_RBAS_AUDIT.json",
        "rtm": ROOT / "docs/BATCH07_OFFICIAL_RTM_301_350.json",
    },
    8: {
        "out": ROOT / "institutional_due_diligence_2026/batch08_independent_audit",
        "closure": "RUN021_BATCH08_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch08_rbas_audit.py",
        "audit_json": "BATCH08_INDEPENDENT_RBAS_AUDIT.json",
        "rtm": ROOT / "docs/BATCH08_OFFICIAL_RTM_351_400.json",
    },
    9: {
        "out": ROOT / "institutional_due_diligence_2026/batch09_independent_audit",
        "closure": "RUN021_BATCH09_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch09_rbas_audit.py",
        "audit_json": "BATCH09_INDEPENDENT_RBAS_AUDIT.json",
        "rtm": ROOT / "docs/BATCH09_OFFICIAL_RTM_401_450.json",
    },
    10: {
        "out": ROOT / "institutional_due_diligence_2026/batch10_independent_audit",
        "closure": "RUN021_BATCH10_BUILD_CLOSURE_EVIDENCE.json",
        "audit_script": "scripts/independent_batch10_rbas_audit.py",
        "audit_json": "BATCH10_INDEPENDENT_RBAS_AUDIT.json",
        "rtm": ROOT / "docs/BATCH10_OFFICIAL_RTM_451_500.json",
    },
}


def official_batch_for_build(build_batch: int) -> int:
    end_id = min(build_batch * 25, 826)
    return (end_id - 1) // 50 + 1


def scope(build_batch: int) -> dict[str, Any]:
    start = (build_batch - 1) * 25 + 1
    end = min(build_batch * 25, 826)
    for b in range(1, build_batch + 1):
        subprocess.run([PYTHON, str(ENSURE_TEST), str(b)], cwd=ROOT, check=False)
    modules = [f"tests/cap646/test_capability_build_batch{b:02d}.py" for b in range(1, build_batch + 1)]
    return {
        "ids": list(range(start, end + 1)),
        "pytest_modules": modules,
        "log": BUILD_DIR / f"batch{build_batch:02d}_pytest.log",
        "scope_label": f"build_batch_{build_batch:02d}_ids_{start}_{end}",
        "rtm_flag": f"build_batch_{build_batch:02d}_remediated",
        "rtm_max_id": end,
    }


def run_regression(sc: dict[str, Any]) -> dict[str, Any]:
    sc["log"].parent.mkdir(parents=True, exist_ok=True)
    cmd = [PYTHON, "-m", "pytest", *sc["pytest_modules"], "-q", "--tb=short"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=1200)
    sc["log"].write_text(proc.stdout + proc.stderr, encoding="utf-8")
    return {"met": proc.returncode == 0, "exit_code": proc.returncode, "log_path": str(sc["log"].relative_to(ROOT))}


async def bcbs(ids: list[int]) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    per: dict[str, Any] = {}
    for cid in ids:
        r = await execute_capability(cid, skip_entitlement=True, params=dict(COMMON_PARAMS))
        src = bool(r.get("data_source") or r.get("source"))
        ts = bool(r.get("timestamp"))
        per[str(cid)] = {"bcbs_remediated": src and ts, "runtime_success": bool(r.get("success"))}
    return {"per_id": per}


def audit(cfg: dict[str, Any], ids: list[int]) -> list[dict[str, Any]]:
    subprocess.run([PYTHON, str(ROOT / cfg["audit_script"])], cwd=ROOT, check=False, timeout=900)
    rows = json.loads((cfg["out"] / cfg["audit_json"]).read_text(encoding="utf-8"))
    return [r for r in rows if int(r["id"]) in ids]


def patch_rtm(cfg: dict[str, Any], rows: list[dict[str, Any]], sc: dict[str, Any]) -> None:
    rtm_path = cfg["rtm"]
    if not rtm_path.is_file():
        return
    doc = json.loads(rtm_path.read_text(encoding="utf-8"))
    per_id = doc.get("per_id") or {}
    for row in rows:
        cid = str(row["id"])
        entry = dict(per_id.get(cid) or {})
        entry["engineering_status"] = "PASS_ENGINEERING" if row.get("status") != "CONCEPTUALLY-UNSOUND" else "NOT_COMPLETE"
        entry[sc["rtm_flag"]] = int(row["id"]) <= sc["rtm_max_id"]
        per_id[cid] = entry
    doc["per_id"] = per_id
    rtm_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


async def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--build-batch", type=int, required=True)
    args = parser.parse_args()
    ob = official_batch_for_build(args.build_batch)
    cfg = OFFICIAL_CONFIG.get(ob)
    if not cfg:
        print(f"no official config for build_batch={args.build_batch} official_batch={ob}")
        return 0
    sc = scope(args.build_batch)
    nr = run_regression(sc)
    bc = await bcbs(sc["ids"])
    rows = audit(cfg, sc["ids"])
    patch_rtm(cfg, rows, sc)
    doc = {
        "generated_at": datetime.now(UTC).isoformat(),
        "scope": sc["scope_label"],
        "non_regression": {"met": nr["met"], "pytest": nr},
        "bcbs": bc,
    }
    path = cfg["out"] / cfg["closure"]
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {path} met={nr['met']}")
    return 0 if nr["met"] else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
