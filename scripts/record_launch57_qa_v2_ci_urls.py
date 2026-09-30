#!/usr/bin/env python3
"""§8.3 V-2 — record GitHub Actions green run URLs (gitignored E-TEST; no index closure)."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
RECORDING = ROOT / "governance/launch57/LAUNCH57_QA_V2_CI_RECORDING.json"
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"

RUN_ID_RE = re.compile(r"/actions/runs/(\d+)")


def _git_head() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        return ""


def _validate_url(url: str, rules: dict) -> str | None:
    parsed = urlparse(url.strip())
    if parsed.scheme != str(rules.get("scheme", "https")):
        return "URL must use https"
    host = (parsed.hostname or "").lower()
    for bad in rules.get("forbidden_hosts") or []:
        if host == str(bad).lower():
            return f"forbidden host {host}"
    needle = str(rules.get("path_must_contain", "/actions/runs/"))
    if needle not in parsed.path:
        return f"URL path must contain {needle}"
    if not RUN_ID_RE.search(parsed.path):
        return "URL must include numeric GitHub Actions run id"
    return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Record §8.3 V-2 CI run URLs (gitignored evidence).")
    parser.add_argument("--security-run-url", required=True, help="Green run URL for security.yml pytest-security")
    parser.add_argument("--launch57-run-url", required=True, help="Green run URL for launch57-cisa-assurance")
    parser.add_argument("--recorded-by", required=True, help="QA operator id or name")
    args = parser.parse_args()

    if not RECORDING.is_file() or not INDEX.is_file():
        print("MISSING institutional recording spec or evidence index", file=sys.stderr)
        return 1
    rec = json.loads(RECORDING.read_text(encoding="utf-8"))
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    rules = rec.get("url_rules") or {}
    for label, url in (
        ("security", args.security_run_url),
        ("launch57", args.launch57_run_url),
    ):
        err = _validate_url(url, rules)
        if err:
            print(f"{label}: {err}", file=sys.stderr)
            return 1

    out_dir = ROOT / str(rec.get("gitignored_evidence_dir", "governance/launch57/evidence/V-2"))
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    out_path = out_dir / f"QA_V2_CI_RUNS_{stamp}.json"
    record = {
        "kind": "launch57_qa_v2_ci_run_urls",
        "program_section": rec.get("program_section"),
        "evidence_class": rec.get("evidence_class"),
        "human_signoff_field": rec.get("human_signoff_field"),
        "recorded_at": datetime.now(UTC).isoformat(),
        "recorded_by": args.recorded_by.strip(),
        "remediation_sha_at_record": idx.get("remediation_sha"),
        "phase_at_record": idx.get("phase"),
        "git_head": _git_head(),
        "workflow_runs": {
            "security_pytest_security": {
                "workflow": ".github/workflows/security.yml",
                "job": "pytest-security",
                "green_run_url": args.security_run_url.strip(),
            },
            "launch57_cisa_assurance": {
                "workflow": ".github/workflows/launch57-cisa-assurance.yml",
                "job": "engineering-baseline",
                "green_run_url": args.launch57_run_url.strip(),
            },
        },
        "honesty": {
            "cisa_certification_claimed": False,
            "program_complete": False,
            "finding_index_auto_close": False,
            "does_not_replace_iv_signoff": True,
        },
    }
    out_path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    print(
        json.dumps(
            {
                "program_complete": False,
                "optional": "Also call record_launch57_independent_verification_signoff.py --step V-2",
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
