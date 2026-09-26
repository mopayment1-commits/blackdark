#!/usr/bin/env python3
"""Generate institutional Evidence Room snapshot (reproducible DD artifact)."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _git_sha() -> str:
    proc = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True)
    return proc.stdout.strip() if proc.returncode == 0 else "unknown"


async def main() -> int:
    parser = argparse.ArgumentParser(description="Build CAP978 institutional evidence room snapshot")
    parser.add_argument("--out", default=str(ROOT / "docs" / "cap978" / "EVIDENCE_ROOM_SNAPSHOT.json"))
    parser.add_argument(
        "--external-out",
        default=str(ROOT / "docs" / "cap978" / "EXTERNAL_REGISTRY.json"),
        help="Write machine-readable external registry JSON",
    )
    parser.add_argument("--full", action="store_true", help="Include external registry rows and full closure detail")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Use CI structural closure (no live network) for reproducible inventory counts",
    )
    args = parser.parse_args()

    if args.ci:
        os.environ["BLACKDARK_CI_DETERMINISTIC_CLOSURE"] = "1"

    import database

    await database.init_db()

    from cap978.evidence_room import build_evidence_room_snapshot
    from cap978.external_registry import external_registry_report

    from cap978.evidence_room import _sha256

    snapshot = await build_evidence_room_snapshot(include_rows=args.full, ci_deterministic=True if args.ci else None)
    snapshot["repository_head_sha"] = _git_sha()
    snapshot["evidence_generation_mode"] = "ci_structural_no_network" if args.ci else "live_functional"
    snapshot["snapshot_hash"] = _sha256({k: v for k, v in snapshot.items() if k != "snapshot_hash"})
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, ensure_ascii=False, indent=2), encoding="utf-8")

    external = external_registry_report()
    external["repository_head_sha"] = _git_sha()
    ext_out = Path(args.external_out)
    ext_out.write_text(json.dumps(external, ensure_ascii=False, indent=2), encoding="utf-8")

    checklist_path = ROOT / "docs" / "cap978" / "COMMERCIAL_LAUNCH_CHECKLIST.json"
    from cap978.institutional_gate import commercial_launch_checklist

    checklist = commercial_launch_checklist()
    checklist["repository_head_sha"] = _git_sha()
    checklist_path.write_text(json.dumps(checklist, ensure_ascii=False, indent=2), encoding="utf-8")

    print(
        json.dumps(
            {
                "verdict": snapshot["verdict"],
                "snapshot_hash": snapshot["snapshot_hash"],
                "path": str(out),
                "external_registry_path": str(ext_out),
            },
            indent=2,
        )
    )
    from cap978.gate_verdict import INSTITUTIONAL_GATE_PASS

    return 0 if snapshot["verdict"] == INSTITUTIONAL_GATE_PASS else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
