#!/usr/bin/env python3
"""Validate (and optionally apply) ops/executive finding status transitions — no fake closure."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"


def _run_verify(script: str, *args: str) -> int:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
    ).returncode


def _verify_finding(finding_id: str, pledge_url: str, prod_url: str) -> list[str]:
    errors: list[str] = []
    if finding_id == "FINDING-01":
        if not pledge_url.strip():
            errors.append("FINDING-01 requires --pledge-url (CISA portal submission URL)")
    elif finding_id == "FINDING-14":
        if not prod_url.strip():
            errors.append("FINDING-14 requires LAUNCH57_PROD_URL or --prod-url")
        elif _run_verify("verify_well_known_security_txt.py", "--url", prod_url) != 0:
            errors.append("FINDING-14: prod security.txt verification failed")
    elif finding_id == "FINDING-18":
        sys.path.insert(0, str(ROOT))
        from pentest_attestation import verify_pentest_attestation

        if not verify_pentest_attestation():
            errors.append("FINDING-18: verify_pentest_attestation() is false")
    elif finding_id == "FINDING-19":
        if _run_verify("verify_edge_waf_cdn.py") != 0:
            errors.append("FINDING-19: verify_edge_waf_cdn.py failed (set CDN_WAF_ACTIVE=1)")
    elif finding_id == "FINDING-11":
        path = ROOT / "governance" / "launch57" / "evidence" / "syft-prod-lock.cyclonedx.json"
        if not path.is_file() and not os.getenv("LAUNCH57_CONTAINER_SBOM_PATH"):
            errors.append("FINDING-11: missing Syft SBOM artifact (CI or LAUNCH57_CONTAINER_SBOM_PATH)")
    else:
        errors.append(f"transition not supported for {finding_id} via ops gate (update index manually with change control)")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--finding", required=True, help="e.g. FINDING-14")
    parser.add_argument("--to", default="CLOSED", help="Target status (default CLOSED)")
    parser.add_argument("--pledge-url", default="", help="Required for FINDING-01")
    parser.add_argument("--prod-url", default="", help="Prod base URL (default LAUNCH57_PROD_URL)")
    parser.add_argument("--apply", action="store_true", help="Write index after verification")
    parser.add_argument("--dry-run", action="store_true", help="Verify only (default if no --apply)")
    args = parser.parse_args()
    prod = (args.prod_url or os.getenv("LAUNCH57_PROD_URL") or "").strip()
    if not INDEX.is_file():
        print("missing evidence index", file=sys.stderr)
        return 1
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    findings = data.get("findings") or {}
    fid = args.finding.strip().upper()
    if fid not in findings:
        print(f"unknown finding {fid}", file=sys.stderr)
        return 1
    current = findings[fid].get("status")
    target = args.to.strip().upper()
    if target != "CLOSED":
        print("only transition to CLOSED is supported via this tool", file=sys.stderr)
        return 1
    errors = _verify_finding(fid, args.pledge_url, prod)
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 2
    note = {
        "transition_at": datetime.now(UTC).isoformat(),
        "from_status": current,
        "to_status": target,
        "verified_by": "scripts/transition_launch57_finding_status.py",
    }
    if fid == "FINDING-01" and args.pledge_url:
        note["pledge_url"] = args.pledge_url.strip()
    print(json.dumps({"ok": True, "finding": fid, "transition": note}, indent=2))
    if not args.apply:
        print("dry-run: pass --apply to update evidence index", file=sys.stderr)
        return 0
    findings[fid]["status"] = target
    findings[fid]["ops_transition"] = note
    data["findings"] = findings
    data["last_ops_transition"] = note
    INDEX.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(f"Updated {INDEX} — run generate_launch57_completion_status.py and generate_launch57_engineering_closure.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
