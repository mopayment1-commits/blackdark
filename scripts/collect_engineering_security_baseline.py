#!/usr/bin/env python3
"""
Collect engineering security baseline evidence (NOT a penetration test).

Normative: NIST SSDF PW/RV practices; supplements FINDING-18 ops closure.
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "governance" / "launch57" / "evidence" / "ENGINEERING_SECURITY_BASELINE.json"


def _run(cmd: list[str]) -> dict:
    try:
        proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=300)
        return {"exit_code": proc.returncode, "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-2000:]}
    except Exception as exc:
        return {"exit_code": -1, "error": str(exc)}


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "engineering_security_baseline",
        "not_a_pentest": True,
        "generated_at": datetime.now(UTC).isoformat(),
        "launch_line": "Launch-57",
        "checks": {
            "pip_audit": _run([sys.executable, "-m", "pip_audit", "-r", "requirements.hashes.txt", "--desc"]),
            "pytest_cisa": _run(
                [sys.executable, "-m", "pytest", "tests/test_cisa_launch57_remediation.py", "-q", "--tb=no"]
            ),
            "security_txt_repo": _run([sys.executable, "scripts/verify_well_known_security_txt.py"]),
            "edge_waf_readiness": _run([sys.executable, "scripts/verify_edge_waf_cdn.py"]),
        },
        "honesty": "This artifact documents automated engineering checks only. Independent pentest remains required for FINDING-18.",
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
