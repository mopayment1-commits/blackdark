#!/usr/bin/env python3
"""Verify security workflow register entries have passing tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REGISTER = ROOT / "docs/security/SECURITY_WORKFLOW_REGISTER.json"


def main() -> int:
    data = json.loads(REGISTER.read_text(encoding="utf-8"))
    remediated = [w for w in data["workflows"] if w.get("status") == "REMEDIATED"]
    tests = []
    for w in remediated:
        ver = w.get("verification", "")
        if ver.startswith("tests/"):
            path = ver.split("::")[0].split()[0].strip()
            if path.endswith(".py"):
                tests.append(path)

    unique_tests = sorted(set(tests))
    if not unique_tests:
        print(json.dumps({"ok": True, "message": "no pytest targets"}))
        return 0

    cmd = [sys.executable, "-m", "pytest", *unique_tests, "-q", "--tb=no"]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    out = {
        "ok": proc.returncode == 0,
        "tests": unique_tests,
        "exit_code": proc.returncode,
        "tail": (proc.stdout + proc.stderr)[-500:],
    }
    print(json.dumps(out, indent=2))
    return 0 if out["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
