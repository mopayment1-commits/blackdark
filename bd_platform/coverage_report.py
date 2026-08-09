"""Code coverage report for due diligence."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from typing import Any


def coverage_report() -> dict[str, Any]:
    root = Path(__file__).resolve().parent.parent
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--cov=.", "--cov-report=term-missing", "--cov-config=.coveragerc"],
            cwd=str(root),
            check=False,
            capture_output=True,
            text=True,
            timeout=120,
        )
        lines = (proc.stdout or "").splitlines()
        total_line = next((line for line in lines if "TOTAL" in line), "")
        pct = 0.0
        if total_line:
            parts = total_line.split()
            for p in parts:
                if p.endswith("%"):
                    try:
                        pct = float(p.strip("%"))
                    except ValueError:
                        pass
        return {
            "coverage_percent": pct,
            "gate_percent": 80,
            "passed": proc.returncode == 0,
            "summary_tail": lines[-15:],
        }
    except (subprocess.TimeoutExpired, OSError):
        return {
            "coverage_percent": 0,
            "error": "coverage_unavailable",
            "note": "Run pytest --cov locally",
        }
