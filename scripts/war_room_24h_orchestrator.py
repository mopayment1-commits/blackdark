#!/usr/bin/env python3
"""24/7 war room orchestrator — runs critical-path checks and writes tracker."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
TRACKER = ROOT / "WAR_ROOM_EXECUTION_TRACKER.json"
PHANTOM_IDS = [704, 708, 725, 812, 813, 814, 815]


def _run_pytest(target: str) -> dict:
    cmd = [str(ROOT / ".venv" / "bin" / "python3"), "-m", "pytest", target, "-q", "--tb=no"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {"target": target, "exit_code": proc.returncode, "tail": (proc.stdout + proc.stderr)[-500:]}


def _check_packages_exist() -> dict:
    return {
        "decision_truth": (ROOT / "decision_truth" / "pipeline.py").exists(),
        "data_governance": (ROOT / "data_governance" / "registry.py").exists(),
    }


def _check_phantom_catalog() -> dict:
    from cap646.catalog import catalog_by_id

    catalog = catalog_by_id()
    missing = [i for i in PHANTOM_IDS if i not in catalog]
    return {"missing": missing, "ok": not missing}


def main() -> int:
    checks = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "packages": _check_packages_exist(),
        "phantom_catalog": _check_phantom_catalog(),
        "tests": {
            "decision_truth": _run_pytest("tests/test_decision_truth_pipeline.py"),
            "data_governance": _run_pytest("tests/test_data_governance_p0_test_matrix.py"),
            "extension_registry": _run_pytest("tests/test_war_room_extension_registry.py"),
        },
    }
    checks["all_green"] = all(
        t["exit_code"] == 0 for t in checks["tests"].values()
    ) and checks["phantom_catalog"]["ok"] and all(checks["packages"].values())

    TRACKER.write_text(json.dumps(checks, indent=2), encoding="utf-8")
    print(json.dumps(checks, indent=2))
    return 0 if checks["all_green"] else 1


if __name__ == "__main__":
    sys.exit(main())
