#!/usr/bin/env python3
"""Run SAST gate — blocks on critical/high findings (CI/CD merge gate).

Usage:
  python scripts/run_sast_gate.py
  python scripts/run_sast_gate.py --no-bandit   # fast secrets/custom rules only
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-bandit", action="store_true", help="Skip Bandit (faster local dev)")
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    args = parser.parse_args()

    from sast_gate import run_sast_scan, trigger_production_vulnerability_incident

    result = run_sast_scan(actor="ci", root=ROOT, include_bandit=not args.no_bandit)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        counts = result.get("finding_counts") or {}
        print(
            f"SAST gate ok={result.get('ok')} "
            f"critical={counts.get('critical', 0)} high={counts.get('high', 0)} "
            f"medium={counts.get('medium', 0)} low={counts.get('low', 0)} "
            f"duration={result.get('duration_seconds')}s"
        )
        if result.get("blocked"):
            for f in (result.get("findings") or [])[:20]:
                if f.get("severity") in {"critical", "high"}:
                    print(f"  BLOCK {f['severity']} {f['rule_id']} {f['file']}:{f['line']} {f['message']}")

    if result.get("blocked"):
        trigger_production_vulnerability_incident(result)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
