#!/usr/bin/env python3
"""Master institutional closure gate — batch01 + batch02 final verification."""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _run(script: str) -> dict:
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / script)], capture_output=True, text=True)
    return {"script": script, "exit_code": proc.returncode, "stdout": proc.stdout.strip(), "stderr": proc.stderr[-500:] if proc.stderr else ""}


async def main() -> None:
    scripts = [
        "audit_official_batch01_rtm.py",
        "audit_official_batch02_rtm.py",
        "verify_batch01_production.py",
        "verify_batch01_http_all50.py",
        "verify_batch01_http_11_fixed.py",
        "verify_entitlement_gateway_proof.py",
        "verify_official_batch02_production.py",
        "verify_entitlement_batch02_gateway_proof.py",
    ]
    results = [_run(s) for s in scripts]
    failed = [r for r in results if r["exit_code"] != 0]

    out = {
        "verified_at": datetime.now(UTC).isoformat(),
        "closure_status": "INSTITUTIONAL_CLOSED" if not failed else "BLOCKED",
        "batches": {
            "batch01": {"scope": "1–50", "status": "INSTITUTIONAL_CLOSED" if not failed else "BLOCKED"},
            "batch02": {"scope": "51–100", "status": "INSTITUTIONAL_CLOSED" if not failed else "BLOCKED"},
        },
        "critical_gate_workflow": ".github/workflows/ci.yml",
        "critical_gate_job": "critical",
        "scripts": results,
        "all_verified": len(failed) == 0,
    }
    path = ROOT / "docs/INSTITUTIONAL_CLOSURE_FINAL.json"
    path.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"all_verified": out["all_verified"], "failed": [f["script"] for f in failed]}, indent=2))
    print(f"Wrote {path}")
    if failed:
        raise SystemExit(f"Institutional closure gate failed: {[f['script'] for f in failed]}")


if __name__ == "__main__":
    asyncio.run(main())
