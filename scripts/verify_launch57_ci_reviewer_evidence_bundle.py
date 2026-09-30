#!/usr/bin/env python3
"""§8.3 V-2 — validate LAUNCH57_CI_REVIEWER_EVIDENCE_BUNDLE structure (URLs optional in repo)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"
SPEC = ROOT / "governance/launch57/LAUNCH57_CROSS_WORKFLOW_ASSURANCE.json"
RECORDING = ROOT / "governance/launch57/LAUNCH57_QA_V2_CI_RECORDING.json"
BUNDLE = ROOT / "governance/launch57/LAUNCH57_CI_REVIEWER_EVIDENCE_BUNDLE.json"


def _valid_run_url(url: str, forbidden_hosts: list[str]) -> bool:
    if not url or not isinstance(url, str):
        return False
    parsed = urlparse(url.strip())
    if parsed.scheme != "https":
        return False
    host = (parsed.hostname or "").lower()
    if host in {h.lower() for h in forbidden_hosts}:
        return False
    if "/actions/runs/" not in parsed.path:
        return False
    return True


def main() -> int:
    errors: list[str] = []
    for path in (INDEX, SPEC, RECORDING, BUNDLE):
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
    if errors:
        print(json.dumps({"pass": False, "errors": errors}, indent=2))
        return 1

    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    cross = json.loads(SPEC.read_text(encoding="utf-8"))
    rec = json.loads(RECORDING.read_text(encoding="utf-8"))
    bundle = json.loads(BUNDLE.read_text(encoding="utf-8"))

    if bundle.get("cisa_certification_claimed") or bundle.get("program_complete"):
        errors.append("bundle must not claim certification or program complete")
    if bundle.get("schema") != "launch57_ci_reviewer_evidence_bundle_v1":
        errors.append("bundle schema mismatch")
    if bundle.get("remediation_sha") != idx.get("remediation_sha"):
        errors.append("bundle remediation_sha drift vs evidence index")
    if bundle.get("phase") != idx.get("phase"):
        errors.append("bundle phase drift vs evidence index")

    expected_keys = {
        "security_pytest_security": (
            ".github/workflows/security.yml",
            "pytest-security",
        ),
        "launch57_cisa_assurance": (
            ".github/workflows/launch57-cisa-assurance.yml",
            "engineering-baseline",
        ),
    }
    runs = bundle.get("workflow_runs") or {}
    for key, (wf, job) in expected_keys.items():
        entry = runs.get(key)
        if not isinstance(entry, dict):
            errors.append(f"missing workflow_runs.{key}")
            continue
        if entry.get("workflow") != wf or entry.get("job") != job:
            errors.append(f"workflow_runs.{key} workflow/job mismatch vs cross-workflow spec")
    for entry in cross.get("workflows") or []:
        wf = entry.get("path", "")
        job = entry.get("job", "")
        matched = any(
            r.get("workflow") == wf and r.get("job") == job for r in runs.values() if isinstance(r, dict)
        )
        if not matched:
            errors.append(f"cross-workflow entry not reflected in bundle: {wf} {job}")

    forbidden = list((rec.get("url_rules") or {}).get("forbidden_hosts") or [])
    urls_present = 0
    for entry in runs.values():
        if not isinstance(entry, dict):
            continue
        url = entry.get("green_run_url")
        if url:
            urls_present += 1
            if not _valid_run_url(str(url), forbidden):
                errors.append(f"invalid green_run_url in bundle: {url}")

    require_urls = os.getenv("LAUNCH57_REQUIRE_V2_CI_URLS", "").strip()
    if require_urls and urls_present < 2:
        errors.append("LAUNCH57_REQUIRE_V2_CI_URLS set but bundle lacks both green_run_url values")

    report = {
        "program_section": "§8.3 V-2",
        "repo_bundle_structure_pass": not errors,
        "cisa_certification_claimed": False,
        "qa_human_urls_recorded_in_bundle": urls_present,
        "require_v2_urls_env": bool(require_urls),
        "errors": errors,
    }
    print(json.dumps(report, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
