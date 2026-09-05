#!/usr/bin/env python3
"""Release engineering gate — orchestrates SOP #30 + #31 before deploy."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
REPORT_PATH = ROOT / "data" / "release_engineering" / "release_gate_latest.json"


def _run(script: str, extra: list[str] | None = None) -> int:
    cmd = [sys.executable, str(ROOT / "scripts" / script), *(extra or [])]
    print("=" * 64)
    print("$", " ".join(cmd))
    return subprocess.call(cmd, cwd=ROOT)


def main() -> int:
    parser = argparse.ArgumentParser(description="BLACKDARK release engineering gate (#30 + #31)")
    parser.add_argument("--base", default="http://127.0.0.1:8000")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-capacity", action="store_true")
    args = parser.parse_args()

    extra = ["--dry-run"] if args.dry_run else []
    capacity_extra = extra + ([] if args.dry_run else ["--base", args.base])

    chaos_rc = _run("release_chaos_gate.py", extra)
    capacity_rc = 0 if args.skip_capacity else _run("release_capacity_evidence.py", capacity_extra)

    from blackdark.data.circuit_breaker import snapshot

    report = {
        "gate": "release_engineering",
        "timestamp": datetime.now(UTC).isoformat(),
        "sops": ["#30_capacity", "#31_chaos", "#32_circuit_breakers"],
        "chaos_pass": chaos_rc == 0,
        "capacity_pass": capacity_rc == 0 or args.skip_capacity,
        "circuit_breakers": snapshot(),
        "release_pass": chaos_rc == 0 and (capacity_rc == 0 or args.skip_capacity),
        "dry_run": args.dry_run,
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("\n" + "=" * 64)
    print(f"Release gate: {'PASS' if report['release_pass'] else 'FAIL'}")
    print(f"Report: {REPORT_PATH}")
    return 0 if report["release_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
