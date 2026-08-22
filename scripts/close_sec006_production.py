#!/usr/bin/env python3
"""Close SEC-006 using live production Auth0 SSO evidence; refresh RVM artifacts."""

from __future__ import annotations

import json
import re
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

PROD = "https://blackdark-production.up.railway.app"
ROOT = Path(__file__).resolve().parent.parent
RVM_PATH = ROOT / "docs" / "rvm" / "RVM.json"
SUMMARY_PATH = ROOT / "docs" / "rvm" / "RVM_SUMMARY.json"
BASELINE_PATH = ROOT / "docs" / "rvm" / "REQUIREMENTS_BASELINE.json"


def _fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=30) as resp:  # nosec B310
        return json.loads(resp.read().decode())


def _fetch_redirect_target(url: str) -> str:
    req = urllib.request.Request(url, method="GET")
    req.add_header("User-Agent", "BLACKDARK-SEC006-CLOSURE/1.0")
    with urllib.request.urlopen(req, timeout=30) as resp:  # nosec B310
        return str(resp.geturl())


def verify_production() -> dict:
    status = _fetch_json(f"{PROD}/api/institutional/sso/status")
    if not (status.get("configured") and status.get("oidc_ready") and status.get("idp") == "auth0"):
        raise SystemExit(f"production_sso_not_ready: {status}")
    if status.get("demo_mode"):
        raise SystemExit("production_sso_demo_mode_enabled")

    default_org = "blackdark-enterprise"
    authorize_url = (
        f"{PROD}/api/institutional/sso/authorize"
        f"?org_id={default_org}"
    )
    try:
        final_url = _fetch_redirect_target(authorize_url)
    except Exception as exc:
        raise SystemExit(f"authorize_redirect_failed: {exc}") from exc
    if "auth0.com" not in final_url:
        raise SystemExit(f"authorize_not_auth0: {final_url[:200]}")

    build = _fetch_json(f"{PROD}/api/build-info")
    return {
        "verified_at": datetime.now(UTC).isoformat(),
        "production_url": PROD,
        "build_commit": build.get("git_commit"),
        "sso_status": status,
        "authorize_final_url_host": re.match(r"https?://([^/]+)", final_url).group(1) if final_url else "",
        "callback_url": status.get("callback_url"),
        "evidence": [
            "production_sso_status_configured",
            "auth0_oidc_ready",
            "authorize_redirects_to_auth0",
            f"commit={str(build.get('git_commit', ''))[:12]}",
        ],
    }


def _patch_row(row: dict, evidence: dict) -> None:
    note = (
        f"Auth0 OIDC live on {PROD}; authorize→Auth0; "
        f"callback={evidence.get('callback_url')}"
    )
    detail = {
        "id": "SEC-006",
        "status": "VERIFIED_COMPLETE",
        "evidence": evidence["evidence"],
        "note": note,
    }
    row["verification_status"] = "PASS"
    row["validation_status"] = "PASS"
    row["final_status"] = "PASS"
    row["implementation_evidence"] = evidence["evidence"]
    row["runtime_evidence"] = evidence["evidence"]
    row["verification_detail"] = detail
    row["validation_detail"] = detail
    row["external_step"] = ""
    row["notes"] = evidence["verified_at"]


def _recompute_summary(rows: list[dict]) -> dict:
    pass_count = sum(1 for r in rows if r.get("final_status") == "PASS")
    fail_count = sum(1 for r in rows if r.get("final_status") == "FAIL")
    external_count = sum(1 for r in rows if r.get("final_status") == "EXTERNAL_EVIDENCE_REQUIRED")
    p0_external = [
        r["id"]
        for r in rows
        if r.get("final_status") == "EXTERNAL_EVIDENCE_REQUIRED"
        and r["id"] in {"CAP-644", "CAP-645", "SEC-006", "SEC-008", "REL-002", "COM-P0-EXT"}
    ]
    return {
        "pass_count": pass_count,
        "fail_count": fail_count,
        "external_count": external_count,
        "p0_external_remaining": p0_external,
    }


def main() -> int:
    evidence = verify_production()
    print(json.dumps(evidence, indent=2))

    rvm = json.loads(RVM_PATH.read_text(encoding="utf-8"))
    rows = rvm.get("requirements") or []
    patched = False
    for row in rows:
        if row.get("id") == "SEC-006":
            _patch_row(row, evidence)
            patched = True
            break
    if not patched:
        raise SystemExit("SEC-006 row missing in RVM.json")

    counts = _recompute_summary(rows)
    rvm["p0_external_remaining"] = counts["p0_external_remaining"]
    rvm["generated_at"] = evidence["verified_at"]
    RVM_PATH.write_text(json.dumps(rvm, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if SUMMARY_PATH.exists():
        summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
        summary.update(counts)
        summary["generated_at"] = evidence["verified_at"]
        if "SEC-006" in summary.get("p0_external_remaining", []):
            summary["p0_external_remaining"] = [
                x for x in summary["p0_external_remaining"] if x != "SEC-006"
            ]
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if BASELINE_PATH.exists():
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        for row in baseline.get("requirements") or []:
            if row.get("id") == "SEC-006":
                row["final_status"] = "PASS"
                row["verification_status"] = "PASS"
                row["validation_status"] = "PASS"
        BASELINE_PATH.write_text(json.dumps(baseline, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print("SEC-006 closed PASS in RVM artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
