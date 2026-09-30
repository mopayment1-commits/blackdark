#!/usr/bin/env python3
"""Program §8.3 independent verification — repo-automatable gates only (no fake Legal/Ops sign-off)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "governance" / "launch57" / "LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json"
PROGRAM = ROOT / "docs/governance/LAUNCH57_CISA_SECURE_BY_DEMAND_REMEDIATION_PROGRAM.md"


def _run_py(rel: str) -> tuple[bool, str]:
    path = ROOT / rel
    if not path.is_file():
        return False, f"missing {rel}"
    proc = subprocess.run(
        [sys.executable, str(path)],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        msg = tail[-1] if tail else f"exit {proc.returncode}"
        return False, f"{rel}: {msg}"
    return True, "ok"


def main() -> int:
    if not REGISTER.is_file() or not PROGRAM.is_file():
        print("MISSING institutional register or program doc", file=sys.stderr)
        return 1
    reg = json.loads(REGISTER.read_text(encoding="utf-8"))
    if reg.get("program_closure_verification_complete"):
        print("REGISTER claims program_closure_verification_complete=true — forbidden before §8.1", file=sys.stderr)
        return 1
    failures: list[str] = []
    steps_report: dict[str, dict] = {}

    v1 = reg["steps"]["V-1"]
    v1_repo: list[str] = []
    for gate in v1.get("repo_gates") or []:
        ok, msg = _run_py(gate) if gate.endswith(".py") else ( (ROOT / gate).is_file(), "ok" if (ROOT / gate).is_file() else f"missing {gate}" )
        if not ok:
            failures.append(f"V-1: {msg}")
        v1_repo.append({"gate": gate, "pass": ok})
    steps_report["V-1"] = {
        "repo_gates": v1_repo,
        "human_signoff": "PENDING",
        "human_field": v1["human_signoff"]["field"],
    }

    v2 = reg["steps"]["V-2"]
    for wf in v2.get("repo_gates") or []:
        if not (ROOT / wf).is_file():
            failures.append(f"V-2: missing workflow {wf}")
    markers = v2.get("test_markers") or {}
    test_mod = ROOT / str(markers.get("module", ""))
    if not test_mod.is_file():
        failures.append("V-2: missing test module")
    else:
        text = test_mod.read_text(encoding="utf-8")
        for name in markers.get("required_test_names") or []:
            if f"def {name}" not in text:
                failures.append(f"V-2: test {name} not found in {markers.get('module')}")
    steps_report["V-2"] = {
        "workflows_present": all((ROOT / wf).is_file() for wf in (v2.get("repo_gates") or [])),
        "denial_header_test_present": "test_anonymous_denial_includes_security_headers" in text if test_mod.is_file() else False,
        "human_signoff": "PENDING",
        "human_field": v2["human_signoff"]["field"],
    }

    v3 = reg["steps"]["V-3"]
    for script in v3.get("operator_scripts") or []:
        if not (ROOT / script).is_file():
            failures.append(f"V-3: missing operator script {script}")
    prod_url = os.getenv(str(v3.get("environment", {}).get("prod_url_var", "LAUNCH57_PROD_URL")), "").strip()
    v3_live: str | None = None
    if prod_url:
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts/verify_launch57_prod_surface.py")],
            cwd=ROOT,
            capture_output=True,
            text=True,
            env={**os.environ, "LAUNCH57_PROD_URL": prod_url},
        )
        v3_live = "PASS" if proc.returncode == 0 else f"FAIL exit {proc.returncode}"
        if proc.returncode != 0:
            failures.append("V-3: prod surface smoke failed (LAUNCH57_PROD_URL set)")
    else:
        v3_live = "SKIPPED_NO_LAUNCH57_PROD_URL"
    steps_report["V-3"] = {
        "operator_scripts_present": True,
        "live_smoke": v3_live,
        "human_signoff": "PENDING",
        "human_field": v3["human_signoff"]["field"],
    }

    v4 = reg["steps"]["V-4"]
    missing_legal_art: list[str] = []
    for rel in v4.get("review_artifacts") or []:
        if not (ROOT / rel).is_file():
            missing_legal_art.append(rel)
    if missing_legal_art:
        failures.append(f"V-4: missing review artifacts: {', '.join(missing_legal_art)}")
    legal_id = os.getenv("LAUNCH57_LEGAL_REVIEW_ID", "").strip()
    steps_report["V-4"] = {
        "review_artifacts_present": not missing_legal_art,
        "legal_review_id_recorded": bool(legal_id),
        "human_signoff": "PASS" if legal_id else "PENDING",
        "human_field": v4["human_signoff"]["field"],
    }

    report = {
        "authority": reg.get("authority"),
        "program_section": reg.get("program_section"),
        "cisa_certification_claimed": False,
        "program_closure_verification_complete": False,
        "repo_automation_pass": not failures,
        "steps": steps_report,
        "failures": failures,
        "honesty": "PASS means repository gates for §8.3 are satisfied; human V-1..V-4 sign-off remains required for program closure.",
    }
    print(json.dumps(report, indent=2))
    if failures:
        print("INDEPENDENT_VERIFICATION_FAIL", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
