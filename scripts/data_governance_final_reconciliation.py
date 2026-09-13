#!/usr/bin/env python3
"""DIG-059 — data governance final reconciliation runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "data_storage_runtime_truth_audit.py")],
        cwd=ROOT,
    )
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
