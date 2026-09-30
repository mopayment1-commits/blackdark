#!/usr/bin/env python3
"""Program §8.3 V-1 — Security Lead inventory re-run (repo gate bundle; human attestation separate)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json"

EXTRA_GATES = (
    "verify_launch57_sbom_ntia_scope.py",
    "verify_launch57_release_attestation_82.py",
    "verify_launch57_evidence_class_register.py",
    "verify_launch57_independent_verification.py",
)


def _run(script: str) -> tuple[bool, str]:
    path = ROOT / "scripts" / script
    if not path.is_file():
        return False, "missing"
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return False, tail[-1] if tail else f"exit {proc.returncode}"
    return True, "ok"


def main() -> int:
    if not REGISTER.is_file():
        print("MISSING independent verification register", file=sys.stderr)
        return 1
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    v1_gates = list((reg.get("steps", {}).get("V-1", {}).get("repo_gates") or []))
    scripts = [g.replace("scripts/", "") for g in v1_gates if g.endswith(".py")]
    scripts.extend(EXTRA_GATES)
    failures: list[str] = []
    results: list[dict] = []
    for script in scripts:
        ok, msg = _run(script)
        results.append({"script": script, "pass": ok, "detail": msg})
        if not ok:
            failures.append(f"{script}: {msg}")
    report = {
        "program_section": "§8.3 V-1",
        "executor_role": "Security Lead (human sign-off still required)",
        "gates_run": len(scripts),
        "results": results,
        "repo_inventory_rerun_pass": not failures,
        "cisa_certification_claimed": False,
    }
    print(json.dumps(report, indent=2))
    if failures:
        print("SECURITY_LEAD_INVENTORY_RERUN_FAIL", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
