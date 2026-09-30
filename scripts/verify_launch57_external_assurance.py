#!/usr/bin/env python3
"""Honest Launch-57 external assurance gate (pentest + WAF + security.txt)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from launch57_assurance_closure import launch57_closure_status

    report = launch57_closure_status()
    print(json.dumps(report, indent=2))
    open_items = [
        k
        for k, v in report["findings"].items()
        if str(v.get("status", "")).startswith("OPEN")
    ]
    if open_items:
        print(f"\nOPEN (ops/legal): {', '.join(open_items)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
