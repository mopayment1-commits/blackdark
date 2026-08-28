#!/usr/bin/env python3
"""CI gate — reject build if float() appears in financial settlement functions (#1032)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    from bd_platform.financial_precision_policy_engine import scan_financial_paths

    result = scan_financial_paths()
    if result["ok"]:
        print(
            f"financial_precision_lint_ok files={result['files_scanned']} violations=0"
        )
        return 0
    print(f"financial_precision_lint_failed violations={result['violation_count']}", file=sys.stderr)
    for v in result["violations"]:
        print(f"  {v.get('file')}:{v.get('line', '?')} {v.get('function', '')} {v.get('violation')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
