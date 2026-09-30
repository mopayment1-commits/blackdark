#!/usr/bin/env python3
"""Run institutional §8.3 repo verification bundle (program register JSON)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REPO_BUNDLE.json"


def main() -> int:
    if not BUNDLE.is_file():
        print("MISSING IV repo bundle register", file=sys.stderr)
        return 1
    spec = json.loads(BUNDLE.read_text(encoding="utf-8"))
    if spec.get("program_closure_verification_complete"):
        print("bundle must not claim program_closure_verification_complete", file=sys.stderr)
        return 1
    failures: list[str] = []
    results: list[dict] = []
    for entry in spec.get("repo_scripts") or []:
        rel = str(entry.get("script", ""))
        expect = int(entry.get("expect_exit", 0))
        path = ROOT / rel
        if not path.is_file():
            failures.append(f"{entry.get('id')}: missing {rel}")
            continue
        proc = subprocess.run([sys.executable, str(path)], cwd=ROOT, capture_output=True, text=True)
        ok = proc.returncode == expect
        results.append(
            {
                "id": entry.get("id"),
                "script": rel,
                "expect_exit": expect,
                "actual_exit": proc.returncode,
                "pass": ok,
                "maps_to": entry.get("maps_to"),
            }
        )
        if not ok:
            failures.append(f"{entry.get('id')}: expected exit {expect}, got {proc.returncode}")
    report = {
        "authority": spec.get("authority"),
        "program_section": spec.get("program_section"),
        "cisa_certification_claimed": False,
        "program_closure_verification_complete": False,
        "repo_bundle_pass": not failures,
        "results": results,
        "failures": failures,
    }
    print(json.dumps(report, indent=2))
    if failures:
        print("IV_REPO_BUNDLE_FAIL", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
