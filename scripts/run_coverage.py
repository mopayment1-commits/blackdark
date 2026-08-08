#!/usr/bin/env python3
"""
Run pytest coverage for core modules (.coveragerc).

Usage:
  python scripts/run_coverage.py
  python scripts/run_coverage.py --html
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", action="store_true", help="Also write htmlcov/")
    args = parser.parse_args()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-q",
        "--cov",
        "--cov-config=.coveragerc",
        "--cov-report=term-missing",
    ]
    if args.html:
        cmd.append("--cov-report=html")

    print("Running:", " ".join(cmd))
    result = subprocess.run(cmd, cwd=str(ROOT))
    return int(result.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
