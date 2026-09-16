#!/usr/bin/env python3
"""Run 826 — continuous v6 orchestrator (batches 1–17, no stop except CS/SB/ledger).

Governing standard: institutional_due_diligence_2026/BLACKDARK_Institutional_Capability_Standard_2026_v6.md
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

from scripts.batch_rbas_config import BatchRbasConfig  # noqa: E402
from scripts.run021_master_orchestrator import (  # noqa: E402
    LEDGER_PATH,
    STATUS_LOG,
    V6_STANDARD,
    five_line_report,
    generate_infrastructure,
    git_tag_batch,
    log_status,
    rebuild_ledger,
    three_way,
)

PYTHON = str(ROOT / ".venv" / "bin" / "python")
STATE_PATH = ROOT / "institutional_due_diligence_2026/00_V6_826_EXECUTION_STATE.json"
PROGRESS_LOG = ROOT / "institutional_due_diligence_2026/RUN826_V6_CONTINUOUS.log"


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_state() -> dict[str, Any]:
    if STATE_PATH.is_file():
        return json.loads(STATE_PATH.read_text(encoding="utf-8"))
    return {"started_at": datetime.now(UTC).isoformat(), "batches_completed": [], "current_batch": None}


def regenerate_path_a(cfg: BatchRbasConfig) -> None:
    """Explicit Path A handlers for batch04+ ; batch13 uses overrides preserved."""
    if cfg.batch_num >= 4:
        subprocess.run(
            [PYTHON, str(ROOT / "scripts/codegen_explicit_path_a_handlers.py"), str(cfg.batch_num)],
            check=True,
            cwd=ROOT,
        )


async def live_verify_batch(cfg: BatchRbasConfig) -> dict[str, Any]:
    from cap646.runtime import execute_capability

    ok = fail = 0
    fails: list[dict[str, Any]] = []
    params = {
        "symbol": "BTC",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "tier": "pro",
    }
    for cid in cfg.id_range:
        try:
            r = await execute_capability(cid, skip_entitlement=True, params=dict(params))
            if r.get("success"):
                ok += 1
            else:
                fail += 1
                fails.append({"id": cid, "error": r.get("error")})
        except Exception as exc:
            fail += 1
            fails.append({"id": cid, "error": str(exc)})
    return {"ok": ok, "fail": fail, "fails": fails[:10]}


async def process_batch(batch_num: int, *, skip_non_regression: bool = False, force_reopen: bool = True) -> int:
    cfg = BatchRbasConfig(batch_num)
    state = load_state()
    state["current_batch"] = batch_num
    save_state(state)

    log_status(f"=== V6 START Batch {batch_num:02d} ({cfg.id_start}-{cfg.id_end}) ===")
    PROGRESS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now(UTC).isoformat()} START batch{batch_num:02d}\n")

    if batch_num >= 4 or force_reopen:
        pass  # explicit Path A after infrastructure generation

    generate_infrastructure(cfg)

    if batch_num >= 4 or force_reopen:
        regenerate_path_a(cfg)

    lv = await live_verify_batch(cfg)
    log_status(f"Batch{batch_num:02d} live_verify ok={lv['ok']} fail={lv['fail']}")
    if lv["fail"] > 0:
        log_status(f"WARN Batch{batch_num:02d}: live failures (continuing audit): {lv['fails'][:3]}")

    proc = subprocess.run([PYTHON, str(ROOT / "scripts/run_batch_rbas_opening.py"), "--batch", str(batch_num)], cwd=ROOT)
    if proc.returncode != 0:
        log_status(f"ABORT Batch{batch_num:02d}: opening failed exit={proc.returncode}")
        return proc.returncode

    args = [PYTHON, str(ROOT / "scripts/run_batch_final_closure.py"), "--batch", str(batch_num)]
    if skip_non_regression:
        args.append("--skip-non-regression")
    proc = subprocess.run(args, cwd=ROOT, timeout=7200)
    if proc.returncode != 0:
        log_status(f"ABORT Batch{batch_num:02d}: closure failed exit={proc.returncode}")
        return proc.returncode

    ev_path = cfg.audit_dir / f"RUN021_BATCH{cfg.batch_num:02d}_CLOSURE_EVIDENCE.json"
    closure_evidence = json.loads(ev_path.read_text(encoding="utf-8")) if ev_path.is_file() else {}
    counts = closure_evidence.get("status_counts", {})
    cs = counts.get("CONCEPTUALLY-UNSOUND", 0)
    sb = counts.get("SPLIT-BRAIN-UNVERIFIED", 0)
    if cs or sb:
        log_status(f"STOP Batch{batch_num:02d}: Type A blockers CS={cs} SB={sb} — v6 halt rule")
        return 1

    ledger = rebuild_ledger(batch_num)
    tw = three_way(ledger, batch_num)
    if not tw.get("ledger_match") or not tw.get("rtm_match"):
        log_status(f"STOP Batch{batch_num:02d}: three-way FAIL {tw}")
        return 1

    five_line_report(cfg, closure_evidence, tw)
    state = load_state()
    state["batches_completed"] = list(dict.fromkeys(state.get("batches_completed", []) + [batch_num]))
    state["current_batch"] = None
    state["last_completed_at"] = datetime.now(UTC).isoformat()
    save_state(state)

    stage_paths = [
        "cap646/",
        "scripts/",
        str(cfg.rtm_path.relative_to(ROOT)),
        str(cfg.audit_dir.relative_to(ROOT)),
        str(STATE_PATH.relative_to(ROOT)),
        str(PROGRESS_LOG.relative_to(ROOT)),
        str(LEDGER_PATH.relative_to(ROOT)),
    ]
    subprocess.run(["git", "add", *stage_paths], cwd=ROOT)
    subprocess.run(
        ["git", "commit", "-m", f"Run 826 v6: Batch{batch_num:02d} ({cfg.id_start}-{cfg.id_end}) Path A + closure"],
        cwd=ROOT,
    )
    git_tag_batch(cfg)
    log_status(f"=== V6 DONE Batch {batch_num:02d} tag={cfg.closure_tag} ===")
    with PROGRESS_LOG.open("a", encoding="utf-8") as fh:
        fh.write(f"{datetime.now(UTC).isoformat()} DONE batch{batch_num:02d}\n")
    return 0


async def main(start: int = 1, end: int = 17) -> int:
    log_status(f"=== RUN826 V6 CONTINUOUS start={start} end={end} governing={V6_STANDARD.name} ===")
    state = load_state()
    state["run826_started_at"] = datetime.now(UTC).isoformat()
    state["range"] = [start, end]
    save_state(state)

    for n in range(start, end + 1):
        rc = await process_batch(n, skip_non_regression=(n < end))
        if rc != 0:
            log_status(f"=== RUN826 HALTED at batch {n:02d} exit={rc} ===")
            return rc

    ledger = rebuild_ledger(end)
    tw = three_way(ledger, end)
    report = ROOT / "institutional_due_diligence_2026/MASTER_826_V6_COMPLETION_REPORT.md"
    report.write_text(
        f"# MASTER 826 v6 Completion Report\n\n"
        f"**Generated:** {datetime.now(UTC).isoformat()}\n"
        f"**Governing:** `{V6_STANDARD.relative_to(ROOT)}`\n"
        f"**PASS_LIVE:** {ledger['summary']['pass_live_count']}/826 (honest — local_dev_vm)\n"
        f"**PASS_ENGINEERING:** {ledger['summary']['pass_engineering_count']}/826\n"
        f"**Closed batches:** 1–{end}\n"
        f"**Three-way:** {json.dumps(tw, indent=2)}\n\n"
        f"See `{PROGRESS_LOG.relative_to(ROOT)}` for continuous log.\n",
        encoding="utf-8",
    )
    log_status("=== RUN826 V6 COMPLETE all batches processed ===")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=17)
    ap.add_argument("--batch", type=int, default=0)
    args = ap.parse_args()
    if args.batch:
        raise SystemExit(asyncio.run(process_batch(args.batch)))
    raise SystemExit(asyncio.run(main(args.start, args.end)))
