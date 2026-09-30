#!/usr/bin/env python3
"""Program §8.3 V-3 — Ops production smoke bundle (L57-P7-WP5 + prod surface when URL set)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json"


def _run(script: str, *args: str) -> int:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
    ).returncode


def main() -> int:
    if not REGISTER.is_file():
        return 1
    v3 = json.loads(REGISTER.read_text(encoding="utf-8"))["steps"]["V-3"]
    errors: list[str] = []
    for script in v3.get("operator_scripts") or []:
        if not (ROOT / script).is_file():
            errors.append(f"missing {script}")
    p7 = ROOT / "scripts/verify_launch57_p7_wp5_production_smoke.py"
    if not p7.is_file():
        errors.append("missing verify_launch57_p7_wp5_production_smoke.py")
    prod = (os.getenv(str(v3.get("environment", {}).get("prod_url_var", "LAUNCH57_PROD_URL"))) or "").strip()
    live: dict = {"skipped": True}
    if prod:
        code = _run("verify_launch57_p7_wp5_production_smoke.py")
        live = {"exit_code": code, "pass": code == 0}
        if code not in (0,):
            errors.append(f"L57-P7-WP5 smoke exit {code}")
    report = {
        "program_section": "§8.3 V-3",
        "operator_scripts_present": not any("missing" in e for e in errors),
        "live_p7_wp5": live,
        "repo_bundle_pass": not errors,
        "human_signoff_still_required": True,
        "cisa_certification_claimed": False,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    if errors:
        return 1
    return 0 if not prod or live.get("pass") else 2


if __name__ == "__main__":
    raise SystemExit(main())
