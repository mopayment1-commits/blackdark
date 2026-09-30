#!/usr/bin/env python3
"""Ensure CISA evidence index still matches locked FINDING-01..19 inventory."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
LOCK = ROOT / "governance" / "launch57" / "FINDING_INVENTORY_LOCK.json"


def main() -> int:
    if not INDEX.is_file() or not LOCK.is_file():
        print("MISSING index or lock file", file=sys.stderr)
        return 1
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    lock = json.loads(LOCK.read_text(encoding="utf-8"))
    expected = list(lock.get("expected_ids") or [])
    actual = sorted((index.get("findings") or {}).keys())
    expected_sorted = sorted(expected)
    errors: list[str] = []
    if len(actual) != int(lock.get("expected_count") or 19):
        errors.append(f"count: index has {len(actual)}, lock expects {lock.get('expected_count')}")
    if actual != expected_sorted:
        missing = sorted(set(expected_sorted) - set(actual))
        extra = sorted(set(actual) - set(expected_sorted))
        if missing:
            errors.append(f"missing_ids: {missing}")
        if extra:
            errors.append(f"extra_ids: {extra}")
    baseline = index.get("baseline_sha")
    if baseline and lock.get("baseline_sha") and baseline != lock.get("baseline_sha"):
        errors.append(f"baseline_sha mismatch index={baseline} lock={lock.get('baseline_sha')}")
    if errors:
        print("INVENTORY_LOCK_FAIL:", file=sys.stderr)
        for line in errors:
            print(f"  - {line}", file=sys.stderr)
        return 1
    print(f"PASS: finding inventory locked at {len(actual)} IDs (FINDING-01..19)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
