#!/usr/bin/env python3
"""Post-deploy ops gate for Launch-57 CISA closure (honest matrix)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(script: str, *args: str) -> int:
    return subprocess.run([sys.executable, str(ROOT / "scripts" / script), *args], cwd=ROOT).returncode


def main() -> int:
    prod = (os.getenv("LAUNCH57_PROD_URL") or os.getenv("APP_BASE_URL") or "").strip()
    matrix: dict[str, dict] = {}

    matrix["engineering_baseline"] = {
        "ok": _run("collect_engineering_security_baseline.py") == 0,
        "artifact": "governance/launch57/evidence/ENGINEERING_SECURITY_BASELINE.json",
    }
    matrix["security_txt_repo"] = {"ok": _run("verify_well_known_security_txt.py") == 0}
    matrix["security_txt_prod"] = {
        "ok": _run("verify_well_known_security_txt.py", "--url", prod) == 0 if prod else False,
        "skipped": not bool(prod),
        "url": prod or None,
    }
    waf_code = _run("verify_edge_waf_cdn.py")
    matrix["waf_cdn"] = {"ok": waf_code == 0, "exit_code": waf_code}
    sys.path.insert(0, str(ROOT))
    from pentest_attestation import verify_pentest_attestation

    matrix["pentest_attestation"] = {"ok": verify_pentest_attestation()}

    print(json.dumps({"matrix": matrix}, indent=2))
    blockers = [k for k, v in matrix.items() if not v.get("ok") and not v.get("skipped")]
    if blockers:
        print(f"BLOCKERS: {', '.join(blockers)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
