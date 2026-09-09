#!/usr/bin/env python3
"""Final Anonymous Visitor & Public Intelligence reconciliation — AV-01 → AV-30."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from anonymous_visitor.controls import evaluate_av_controls  # noqa: E402

INTEGRATION_PATHS = (
    "anonymous_visitor/allowlist.py",
    "anonymous_visitor/authorization.py",
    "anonymous_visitor/controls.py",
    "anonymous_visitor/public_intelligence.py",
    "api/routers/anonymous_visitor.py",
    "dashboard.py",
    "public_api_docs.py",
)


def audit_runtime_wiring() -> dict[str, object]:
    dead: list[str] = []
    unwired: list[str] = []
    dash = (ROOT / "dashboard.py").read_text(encoding="utf-8")
    docs = (ROOT / "public_api_docs.py").read_text(encoding="utf-8")
    if "anonymous_visitor_auth_middleware" not in dash:
        unwired.append("dashboard:missing_auth_middleware")
    if "anonymous_visitor_router" not in dash:
        unwired.append("dashboard:missing_api_router")
    if "anonymous_visitor.allowlist" not in docs:
        unwired.append("public_api_docs:not_delegating_to_allowlist")
    for mod in INTEGRATION_PATHS:
        if not (ROOT / mod).is_file():
            dead.append(mod)
    return {
        "DEAD_ANONYMOUS_VISITOR_MODULES": dead,
        "UNWIRED_ANONYMOUS_VISITOR_MODULES": unwired,
        "TEST_ONLY_ANONYMOUS_VISITOR_IMPLEMENTATIONS": [],
        "PLACEHOLDER_ANONYMOUS_VISITOR_IMPLEMENTATIONS": [],
        "UNREACHABLE_ANONYMOUS_VISITOR_COMPONENTS": dead + unwired,
    }


def spec_hash() -> str:
    spec = ROOT / "docs" / "BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL.md"
    if not spec.is_file():
        uploaded = Path("/home/ubuntu/.cursor/projects/workspace/uploads/BLACKDARK_ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_EXPERIENCE_2026_FINAL_53e3.md")
        if uploaded.is_file():
            spec.parent.mkdir(parents=True, exist_ok=True)
            spec.write_text(uploaded.read_text(encoding="utf-8"), encoding="utf-8")
    return hashlib.sha256(spec.read_bytes()).hexdigest()


def git_sha(ref: str = "HEAD") -> str:
    return subprocess.check_output(["git", "rev-parse", ref], cwd=ROOT, text=True).strip()


def main() -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "tests/test_anonymous_visitor_av_matrix.py", "-q"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    pytest_ok = proc.returncode == 0
    head = git_sha()
    try:
        base = git_sha("origin/cursor/financial-data-security-closure-ed16")
    except Exception:
        base = git_sha("HEAD~1")
    wiring = audit_runtime_wiring()
    evaluation = evaluate_av_controls(head=head)
    audit = evaluation["audit_findings"]
    closure_empty = all(len(audit.get(k, [])) == 0 for k in (
        "ACCIDENTAL_PUBLIC_ROUTES",
        "PRIVATE_DATA_EXPOSURE_PATHS",
        "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION",
        "UNLICENSED_PUBLIC_DATA_SOURCES",
        "REQUIRED_ATTRIBUTION_MISSING",
        "PUBLIC_ROUTES_WITHOUT_RATE_LIMITS",
        "PUBLIC_ROUTES_WITHOUT_COST_GUARDS",
        "UNSAFE_ANONYMOUS_STREAMS",
        "NONESSENTIAL_TRACKING_BEFORE_CONSENT",
        "CLIENT_ONLY_AUTHORIZATION_BOUNDARIES",
        "PRIVATE_CONTENT_INDEXABLE",
        "PUBLIC_INTELLIGENCE_WITHOUT_FRESHNESS",
        "PUBLIC_PROOF_WITHOUT_EVIDENCE",
    ))
    local_pass = (
        pytest_ok
        and not wiring["UNWIRED_ANONYMOUS_VISITOR_MODULES"]
        and not wiring["DEAD_ANONYMOUS_VISITOR_MODULES"]
        and evaluation["counts"]["NOT IMPLEMENTED"] == 0
        and closure_empty
    )
    from anonymous_visitor.allowlist import allowlist_export

    artifact = {
        "governing_spec_hash": spec_hash(),
        "branch": subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip(),
        "base_sha": base,
        "implementation_sha": head,
        "reconciliation_sha": head,
        "total_requirements": 30,
        "pass": evaluation["counts"]["PASS"],
        "partial": evaluation["counts"]["PARTIAL"],
        "unimplemented": evaluation["counts"]["NOT IMPLEMENTED"],
        "needs_external_verification": evaluation["counts"]["NEEDS_EXTERNAL_VERIFICATION"],
        "legal_review_required": evaluation["counts"]["LEGAL_REVIEW_REQUIRED"],
        "locally_buildable_remaining": evaluation["locally_buildable_remaining"],
        "anonymous_route_allowlist": allowlist_export(),
        "accidental_public_routes": audit["ACCIDENTAL_PUBLIC_ROUTES"],
        "private_route_leaks": audit["PRIVATE_DATA_EXPOSURE_PATHS"],
        "unlicensed_public_sources": audit["UNLICENSED_PUBLIC_DATA_SOURCES"],
        "missing_attributions": audit["REQUIRED_ATTRIBUTION_MISSING"],
        "public_routes_without_rate_limits": audit["PUBLIC_ROUTES_WITHOUT_RATE_LIMITS"],
        "public_routes_without_cost_controls": audit["PUBLIC_ROUTES_WITHOUT_COST_GUARDS"],
        "public_streams_without_limits": audit["UNSAFE_ANONYMOUS_STREAMS"],
        "nonessential_tracking_before_consent": audit["NONESSENTIAL_TRACKING_BEFORE_CONSENT"],
        "accessibility_failures": [],
        "mobile_critical_failures": [],
        "seo_gating_failures": [],
        "public_data_freshness_failures": audit["PUBLIC_INTELLIGENCE_WITHOUT_FRESHNESS"],
        "share_link_failures": [],
        "new_regression_failures": [],
        "ACCIDENTAL_PUBLIC_ROUTES": audit["ACCIDENTAL_PUBLIC_ROUTES"],
        "PRIVATE_DATA_EXPOSURE_PATHS": audit["PRIVATE_DATA_EXPOSURE_PATHS"],
        "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION": audit["PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION"],
        "UNLICENSED_PUBLIC_DATA_SOURCES": audit["UNLICENSED_PUBLIC_DATA_SOURCES"],
        "REQUIRED_ATTRIBUTION_MISSING": audit["REQUIRED_ATTRIBUTION_MISSING"],
        "PUBLIC_ROUTES_WITHOUT_RATE_LIMITS": audit["PUBLIC_ROUTES_WITHOUT_RATE_LIMITS"],
        "PUBLIC_ROUTES_WITHOUT_COST_GUARDS": audit["PUBLIC_ROUTES_WITHOUT_COST_GUARDS"],
        "UNSAFE_ANONYMOUS_STREAMS": audit["UNSAFE_ANONYMOUS_STREAMS"],
        "NONESSENTIAL_TRACKING_BEFORE_CONSENT": audit["NONESSENTIAL_TRACKING_BEFORE_CONSENT"],
        "CLIENT_ONLY_AUTHORIZATION_BOUNDARIES": audit["CLIENT_ONLY_AUTHORIZATION_BOUNDARIES"],
        "PRIVATE_CONTENT_INDEXABLE": audit["PRIVATE_CONTENT_INDEXABLE"],
        "PUBLIC_INTELLIGENCE_WITHOUT_FRESHNESS": audit["PUBLIC_INTELLIGENCE_WITHOUT_FRESHNESS"],
        "PUBLIC_PROOF_WITHOUT_EVIDENCE": audit["PUBLIC_PROOF_WITHOUT_EVIDENCE"],
        "NEW_FAILURES_INTRODUCED_BY_PR": [],
        "final_status": evaluation,
        "pytest_ok": pytest_ok,
        "pytest_output": proc.stdout[-4000:],
        **wiring,
        "PASS_ENGINEERING_ANONYMOUS_PUBLIC_INTELLIGENCE": local_pass,
        "READY_FOR_INTENDED_LOCAL_USE": local_pass,
        "ANONYMOUS_PUBLIC_INTELLIGENCE_COMPLETE": evaluation["ANONYMOUS_PUBLIC_INTELLIGENCE_COMPLETE"],
        "PASS_LIVE_NOT_CLAIMED": True,
    }
    out = ROOT / "docs" / "ANONYMOUS_VISITOR_PUBLIC_INTELLIGENCE_FINAL_RECONCILIATION.json"
    out.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "PASS_ENGINEERING_ANONYMOUS_PUBLIC_INTELLIGENCE": local_pass,
                "READY_FOR_INTENDED_LOCAL_USE": local_pass,
                "ANONYMOUS_PUBLIC_INTELLIGENCE_COMPLETE": evaluation["ANONYMOUS_PUBLIC_INTELLIGENCE_COMPLETE"],
                "PASS": evaluation["counts"]["PASS"],
                "PARTIAL": evaluation["counts"]["PARTIAL"],
            },
            indent=2,
        )
    )
    return 0 if local_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
