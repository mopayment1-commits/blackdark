#!/usr/bin/env python3
"""Generic batch RBAS opening audit (Run 021)."""
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

from scripts.batch_rbas_config import BatchRbasConfig, WF027_UNRESOLVED  # noqa: E402
from scripts.rbas001_scoping import write_batch_tier_table  # noqa: E402

PYTHON = str(ROOT / ".venv" / "bin" / "python")


def wf027_preflight(cfg: BatchRbasConfig) -> dict[str, Any]:
    overlap = WF027_UNRESOLVED & set(cfg.id_range)
    return {
        "batch": cfg.batch_num,
        "id_range": f"{cfg.id_start}-{cfg.id_end}",
        "wf027_overlap": sorted(overlap),
        "met": len(overlap) == 0,
    }


def cross_spine_preflight(cfg: BatchRbasConfig) -> dict[str, Any]:
    from cap646.batch_registry import routing_overlap_map

    overlaps = {cid: lists for cid, lists in routing_overlap_map().items() if cid in cfg.id_range}
    return {"overlaps_in_range": overlaps, "met": len(overlaps) == 0}


def run_audit(cfg: BatchRbasConfig) -> dict[str, Any]:
    script = ROOT / f"scripts/independent_batch{cfg.batch_num:02d}_rbas_audit.py"
    proc = subprocess.run([PYTHON, str(script)], cwd=ROOT, capture_output=True, text=True, timeout=3600)
    audit_path = cfg.audit_dir / f"BATCH{cfg.batch_num:02d}_INDEPENDENT_RBAS_AUDIT.json"
    rows = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.is_file() else []
    from collections import Counter

    counts = Counter(r["status"] for r in rows)
    return {
        "exit_code": proc.returncode,
        "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
        "stderr_tail": proc.stderr[-2000:] if proc.stderr else "",
        "status_counts": dict(counts),
        "conceptually_unsound": counts.get("CONCEPTUALLY-UNSOUND", 0),
        "split_brain_unverified": counts.get("SPLIT-BRAIN-UNVERIFIED", 0),
    }


def write_opening_report(cfg: BatchRbasConfig, wf027: dict, cross: dict, audit: dict) -> Path:
    cfg.audit_dir.mkdir(parents=True, exist_ok=True)
    path = cfg.audit_dir / f"BATCH{cfg.batch_num:02d}_RUN_OPENING_REPORT.md"
    lines = [
        f"# Batch {cfg.batch_num:02d} RBAS Opening Report (Run 021)\n\n",
        f"**Generated:** {datetime.now(UTC).isoformat()}  \n",
        f"**Scope:** IDs {cfg.id_start}–{cfg.id_end}  \n\n",
        "## WF-027 Preflight\n\n",
        f"- **Overlap with unresolved legacy IDs:** `{wf027['wf027_overlap']}` — **{'MET ✅' if wf027['met'] else 'FAIL ❌'}**\n\n",
        "## CROSS-SPINE-001 Preflight\n\n",
        f"- **Routing overlaps in range:** `{cross['overlaps_in_range']}` — **{'MET ✅' if cross['met'] else 'FAIL ❌'}**\n\n",
        "## RBAS Audit Summary\n\n",
        f"- **Status counts:** `{audit['status_counts']}`\n",
        f"- **CONCEPTUALLY-UNSOUND:** {audit['conceptually_unsound']}\n",
        f"- **SPLIT-BRAIN-UNVERIFIED:** {audit['split_brain_unverified']}\n\n",
        "**Batch NOT closed at opening** — closure follows remediation gate.\n",
    ]
    path.write_text("".join(lines), encoding="utf-8")
    return path


async def main(batch_num: int) -> int:
    cfg = BatchRbasConfig(batch_num)
    cfg.audit_dir.mkdir(parents=True, exist_ok=True)
    tier_path = cfg.audit_dir / "RBAS001_TIER_CLASSIFICATION.json"
    write_batch_tier_table(batch_num, tier_path)
    wf027 = wf027_preflight(cfg)
    cross = cross_spine_preflight(cfg)
    if not wf027["met"]:
        print("WF-027 FAIL", wf027)
        return 1
    audit = run_audit(cfg)
    write_opening_report(cfg, wf027, cross, audit)
    print(f"Opening batch{cfg.batch_num:02d}: CS={audit['conceptually_unsound']} SB={audit['split_brain_unverified']}")
    return 0 if audit["exit_code"] == 0 else audit["exit_code"]


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--batch", type=int, required=True)
    args = p.parse_args()
    raise SystemExit(asyncio.run(main(args.batch)))
