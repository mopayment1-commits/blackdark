#!/usr/bin/env python3
"""Run Dependency & SBOM Scanning Gate — exits non-zero when merge/deploy blocked.

Usage:
  python scripts/run_dependency_scan_gate.py
  python scripts/run_dependency_scan_gate.py --skip-sbom
  python scripts/run_dependency_scan_gate.py --json
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-sbom", action="store_true", help="Skip SBOM generation (faster CI)")
    parser.add_argument("--json", action="store_true", help="Print full JSON result")
    parser.add_argument("--actor", default="ci", help="Actor label for audit trail")
    args = parser.parse_args()

    from dependency_scan_gate import run_dependency_scan_gate

    result = run_dependency_scan_gate(actor=args.actor, skip_sbom=args.skip_sbom)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        counts = result.get("finding_counts") or {}
        print(
            f"dependency_scan_gate ok={result.get('ok')} blocked={result.get('blocked')} "
            f"critical={counts.get('critical', 0)} high={counts.get('high', 0)} "
            f"duration={result.get('duration_seconds')}s scan_id={result.get('scan_id')}"
        )
    return 1 if result.get("blocked") or not result.get("ok") else 0


if __name__ == "__main__":
    raise SystemExit(main())
