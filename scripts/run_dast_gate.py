#!/usr/bin/env python3
"""Run DAST gate — dynamic security scan on live/staging or local ASGI app.

Usage:
  python scripts/run_dast_gate.py                    # CI: local ASGI smoke
  DAST_TARGET_URL=https://staging.example.com python scripts/run_dast_gate.py
  DAST_TARGET_URL=https://prod.example.com DAST_PRODUCTION_READ_ONLY=true python scripts/run_dast_gate.py
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


async def _main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", default=None, choices=["ci", "weekly", "monthly", "ad_hoc"])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    from dast_gate import run_dast_gate

    result = await run_dast_gate(mode=args.mode, actor="ci")
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        counts = result.get("finding_counts") or {}
        print(
            f"DAST gate ok={result.get('ok')} target={result.get('target')} "
            f"critical={counts.get('critical', 0)} high={counts.get('high', 0)} "
            f"medium={counts.get('medium', 0)} duration={result.get('duration_seconds')}s"
        )
        if result.get("blocked"):
            for f in (result.get("findings") or [])[:15]:
                if f.get("severity") in {"critical", "high"}:
                    print(f"  BLOCK {f['severity']} {f['rule_id']} {f['endpoint']} {f['message'][:60]}")

    return 1 if result.get("blocked") else 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(_main()))
