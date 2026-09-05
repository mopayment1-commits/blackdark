#!/usr/bin/env python3
"""Prove HMAC closure guard fails without valid owner token (CLOSURE-REJECT-04 item 24)."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    code = """
from cap646.closure_guard import assert_owner_approval_for_closure, ClosureGuardError
try:
    assert_owner_approval_for_closure(requested_status="INSTITUTIONAL_CLOSED")
except ClosureGuardError as e:
    print(f"BLOCKED:{e}")
    raise SystemExit(42)
raise SystemExit(0)
"""
    proc = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
    print(proc.stdout.strip() or proc.stderr.strip())
    if proc.returncode != 42:
        print(f"Expected exit 42, got {proc.returncode}", file=sys.stderr)
        return 1
    print("HMAC guard failure proof: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
