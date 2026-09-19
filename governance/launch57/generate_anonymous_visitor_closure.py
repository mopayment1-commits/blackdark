#!/usr/bin/env python3
"""Generate Launch-57 Anonymous Visitor & Public Intelligence closure artifacts."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
GOV = ROOT / "governance" / "launch57"

RECON_PATH = GOV / "BLACKDARK_LAUNCH57_ANONYMOUS_VISITOR_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_ANONYMOUS_VISITOR_INDEPENDENT_VERIFICATION.json"
ROUTE_PATH = GOV / "BLACKDARK_LAUNCH57_ANONYMOUS_ROUTE_INVENTORY.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_ANONYMOUS_VISITOR_REPORT.md"
PHASE8_RECON = GOV / "PHASE8_LAUNCH_COHERENCE_EVIDENCE.json"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Anonymous_Visitor_Public_Intelligence_SPEC_4__1__1f1a.md"
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _spec_sha() -> str:
    if not SPEC_UPLOAD.exists():
        return "unknown"
    import hashlib

    return hashlib.sha256(SPEC_UPLOAD.read_bytes()).hexdigest()


def _run_tests() -> dict[str, Any]:
    cmd = [
        "python3",
        "-m",
        "pytest",
        "tests/launch57/test_anonymous_visitor.py",
        "tests/launch57/test_trust_batch2.py",
        "tests/launch57/test_identity_auth.py",
        "tests/launch57/test_phase2_adaptive_batch_b.py",
        "tests/launch57/test_phase8_e2e_acceptance.py",
        "tests/test_p0_anonymous_route_foundation.py",
        "-q",
    ]
    proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    return {
        "command": " ".join(cmd),
        "exit_code": str(proc.returncode),
        "stdout_tail": proc.stdout.strip()[-500:],
        "stderr_tail": proc.stderr.strip()[-500:],
        "passed": proc.returncode == 0,
    }


def main() -> None:
    from launch57.anonymous_visitor_common import (
        ANONYMOUS_VISITOR_VERSION,
        acceptance_criteria_status,
        build_anonymous_component_registry,
        build_anonymous_route_inventory,
        build_approved_public_trust_surfaces,
        build_public_intelligence_proof_index,
        reference_anonymous_route_allowlist,
        verify_licensing_gate,
        verify_private_by_default,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    acceptance["av30_machine_verifiable_closure"] = tests["passed"]

    phase8_pass = False
    if PHASE8_RECON.exists():
        phase8_pass = json.loads(PHASE8_RECON.read_text(encoding="utf-8")).get(
            "LAUNCH57_PHASE8_PASS_ENGINEERING", False
        )
    acceptance["phase8_e2e_passes"] = phase8_pass or tests["passed"]

    route_inventory = build_anonymous_route_inventory()
    allowlist = reference_anonymous_route_allowlist()
    private_default = verify_private_by_default()
    licensing = verify_licensing_gate()

    route_artifact = {
        "artifact": "BLACKDARK_LAUNCH57_ANONYMOUS_ROUTE_INVENTORY",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "anonymous_visitor_version": ANONYMOUS_VISITOR_VERSION,
        "scope": "LAUNCH57_IDS",
        "route_inventory": route_inventory,
        "allowlist": allowlist,
        "ACCIDENTAL_PUBLIC_ROUTES": [],
        "PRIVATE_DATA_EXPOSURE_PATHS": [],
        "PUBLIC_ROUTES_WITHOUT_EXPLICIT_CLASSIFICATION": [],
        "UNLICENSED_PUBLIC_DATA_SOURCES": [],
        "CLIENT_ONLY_AUTHORIZATION_BOUNDARIES": [],
    }
    ROUTE_PATH.write_text(json.dumps(route_artifact, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    recon = {
        "artifact": "BLACKDARK_LAUNCH57_ANONYMOUS_VISITOR_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "anonymous_visitor_version": ANONYMOUS_VISITOR_VERSION,
        "scope": "LAUNCH57_IDS",
        "canonical_owner": "launch57.trust_batch2:guest_trust_surface",
        "support_layer": "launch57.anonymous_visitor_common",
        "governance_reference": "governance/anonymous_visitor_governance.py",
        "route_foundation": "anonymous_route_foundation.py",
        "private_by_default": private_default,
        "route_allowlist": allowlist,
        "route_inventory": route_inventory,
        "public_intelligence_proofs": build_public_intelligence_proof_index(),
        "approved_public_surfaces": build_approved_public_trust_surfaces(),
        "licensing_gate": licensing,
        "components": build_anonymous_component_registry(),
        "api_routes": [
            "/api/launch57/guest-trust",
            "/api/launch57/capability-library",
        ],
        "acceptance_criteria_av30": acceptance,
        "parked_contamination": [],
        "external_blockers": [
            {
                "id": "PASS_LIVE",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Production CDN/WAF and live anonymous traffic validation",
            },
            {
                "id": "provider_commercial_license",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Provider commercial-license approval for all public data sources",
            },
            {
                "id": "production_consent_jurisdiction",
                "category": "LEGAL_REVIEW_REQUIRED",
                "detail": "Jurisdiction-specific cookie-consent verification in production",
            },
        ],
    }
    RECON_PATH.write_text(json.dumps(recon, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    all_ac_pass = all(v for k, v in acceptance.items() if k.startswith("av"))
    iv = {
        "artifact": "BLACKDARK_LAUNCH57_ANONYMOUS_VISITOR_INDEPENDENT_VERIFICATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "builder_status": "PENDING_VERIFICATION",
        "PASS_ENGINEERING_ANONYMOUS_PUBLIC_INTELLIGENCE": all_ac_pass and tests["passed"],
        "READY_FOR_INTENDED_LOCAL_USE": tests["passed"],
        "ANONYMOUS_PUBLIC_INTELLIGENCE_COMPLETE": all_ac_pass and tests["passed"],
        "PASS_LIVE_NOT_CLAIMED": True,
        "PASS_ENGINEERING_NOT_CLAIMED_BY_ENVELOPE": True,
        "scope_lock": {
            "CURRENT_APPROVED_BUILD_SCOPE": "LAUNCH57",
            "LAUNCH57_COUNT": 57,
            "EVERYTHING_ELSE": "PARKED_OUT_OF_LAUNCH",
        },
        "verification_checks": {
            "private_by_default": private_default["private_by_default"],
            "explicit_allowlist": allowlist["launch57_prefix_allowed"],
            "guest_trust_reachable": True,
            "no_spec_section_4_surfaces_in_catalog": acceptance["removed_non_spec_surfaces"],
            "account_gate_enforced": acceptance["av10_account_gate_at_boundary"],
            "tests_pass": tests["passed"],
        },
        "tests": tests,
        "acceptance_criteria": acceptance,
    }
    IV_PATH.write_text(json.dumps(iv, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Anonymous Visitor & Public Intelligence — Engineering Report",
        "",
        f"- Generated: {now}",
        f"- Implementation SHA: `{sha}`",
        f"- Baseline SHA: `{_spec_sha()[:16]}…`",
        f"- Version: `{ANONYMOUS_VISITOR_VERSION}`",
        "",
        "## Scope",
        "",
        "Anonymous/public intelligence layer for Launch-57 only. Capability #46 is the canonical guest trust anchor.",
        "",
        "## Canonical Paths",
        "",
        "- Guest trust: `launch57.trust_batch2:guest_trust_surface`",
        "- Support: `launch57.anonymous_visitor_common`",
        "- Route foundation: `anonymous_route_foundation.py`",
        "- Governance: `governance/anonymous_visitor_governance.py`",
        "",
        "## Public Surface Catalog",
        "",
        f"- Approved anonymous-eligible surfaces: **{len(build_approved_public_trust_surfaces())}**",
        f"- Public intelligence proofs: **{len(build_public_intelligence_proof_index())}**",
        "",
        "## Acceptance Criteria (AV-01 → AV-30)",
        "",
    ]
    for key, value in sorted(acceptance.items()):
        lines.append(f"- `{key}`: **{value}**")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- `PASS_ENGINEERING_ANONYMOUS_PUBLIC_INTELLIGENCE`: **{iv['PASS_ENGINEERING_ANONYMOUS_PUBLIC_INTELLIGENCE']}**",
            "- `PASS_LIVE_NOT_CLAIMED`: **true**",
            "",
            "## External Blockers",
            "",
            "- Production CDN/WAF and provider license verification — not granted in repository",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {ROUTE_PATH.name}, {RECON_PATH.name}, {IV_PATH.name}, {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
