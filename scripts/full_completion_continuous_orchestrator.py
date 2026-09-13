#!/usr/bin/env python3
"""Continuous full-completion orchestrator — run until gates improve."""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OUT = ROOT / "FULL_COMPLETION_CONTINUOUS_STATUS.json"


def _run(cmd: list[str]) -> dict:
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {"cmd": cmd, "exit_code": proc.returncode, "tail": (proc.stdout + proc.stderr)[-800:]}


def main() -> int:
    status = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "steps": [],
    }
    py = str(ROOT / ".venv" / "bin" / "python3")

    steps = [
        [py, "scripts/batch_closure_verify.py"],
        [py, "scripts/full_completion_bootstrap.py"],
        [py, "scripts/war_room_24h_orchestrator.py"],
        [py, "-m", "pytest", "tests/test_split_brain_unification.py", "tests/test_data_governance_reconciliation.py", "-q", "--tb=no"],
    ]
    for cmd in steps:
        status["steps"].append(_run(cmd))

    if (ROOT / "BATCH_CLOSURE_VERIFY_REPORT.json").exists():
        status["batch_closure"] = json.loads((ROOT / "BATCH_CLOSURE_VERIFY_REPORT.json").read_text())
    if (ROOT / "FULL_COMPLETION_PHASE_SUMMARY.json").exists():
        status["phase_summary"] = json.loads((ROOT / "FULL_COMPLETION_PHASE_SUMMARY.json").read_text())

    all_ok = all(s["exit_code"] == 0 for s in status["steps"])
    status["all_green"] = all_ok
    OUT.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
