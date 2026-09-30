#!/usr/bin/env python3
"""Program §8.3 V-2 — QA repo bundle (workflows + denial-header test marker; CI URL is human)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REGISTER.json"


def main() -> int:
    if not REGISTER.is_file():
        return 1
    v2 = json.loads(REGISTER.read_text(encoding="utf-8"))["steps"]["V-2"]
    errors: list[str] = []
    for wf in v2.get("repo_gates") or []:
        if not (ROOT / wf).is_file():
            errors.append(f"missing workflow {wf}")
    mod = ROOT / str((v2.get("test_markers") or {}).get("module", ""))
    if not mod.is_file():
        errors.append("missing test module")
    else:
        text = mod.read_text(encoding="utf-8")
        for name in (v2.get("test_markers") or {}).get("required_test_names") or []:
            if f"def {name}" not in text:
                errors.append(f"missing test {name}")
    for gate in v2.get("repo_automation") or []:
        if not (ROOT / gate).is_file():
            errors.append(f"missing repo_automation {gate}")
    recorder = v2.get("signoff_recorder", "")
    if recorder and not (ROOT / recorder).is_file():
        errors.append(f"missing signoff_recorder {recorder}")
    report = {
        "program_section": "§8.3 V-2",
        "repo_bundle_pass": not errors,
        "qa_ci_green_run_url_required": True,
        "cisa_certification_claimed": False,
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
