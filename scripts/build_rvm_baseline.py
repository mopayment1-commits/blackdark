#!/usr/bin/env python3
"""Build the fixed Requirements Baseline from governing sources."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rvm.baseline import write_baseline
from rvm.governing import write_governing_sources


def main() -> int:
    gov = write_governing_sources()
    if not gov.get("all_present") or not gov.get("all_hashes_ok"):
        print("ERROR: governing source files missing or hash mismatch", file=sys.stderr)
        print(json.dumps(gov, indent=2), file=sys.stderr)
        return 1
    baseline = write_baseline()
    print(json.dumps({"baseline_version": baseline["baseline_version"], "total": baseline["total_requirements"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
