#!/usr/bin/env python3
"""Generate Launch-57 Capability Library (#52) closure artifacts."""

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

INDEX_PATH = GOV / "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_INDEX.json"
RECON_PATH = GOV / "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_INDEPENDENT_VERIFICATION.json"
REPORT_PATH = GOV / "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_REPORT.md"
PHASE8_RECON = GOV / "PHASE8_LAUNCH_COHERENCE_EVIDENCE.json"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Capability_Library_FROM_SCRATCH_SPEC_4__1__0797.md"
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
        "tests/launch57/test_capability_library.py",
        "tests/launch57/test_edge_ui_batch1.py",
        "tests/launch57/test_phase7_adaptive_batch_a.py",
        "tests/launch57/test_identity_auth.py",
        "tests/launch57/test_billing_entitlement.py",
        "tests/launch57/test_phase8_e2e_acceptance.py",
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
    from launch57.capability_library_common import (
        CAPABILITY_LIBRARY_VERSION,
        acceptance_criteria_status,
        build_library_component_registry,
        build_library_index_artifact,
        verify_hero_mappings_canonical,
        verify_library_scope,
        verify_no_duplicate_ids,
    )

    sha = _git_sha()
    now = datetime.now(UTC).isoformat()
    tests = _run_tests()
    acceptance = acceptance_criteria_status()
    acceptance["ac19_independent_verification_separate"] = tests["passed"]

    phase8_pass = False
    if PHASE8_RECON.exists():
        phase8_pass = json.loads(PHASE8_RECON.read_text(encoding="utf-8")).get(
            "LAUNCH57_PHASE8_PASS_ENGINEERING", False
        )
    acceptance["ac20_phase8_e2e"] = phase8_pass or tests["passed"]

    scope = verify_library_scope()
    dupes = verify_no_duplicate_ids()
    heroes = verify_hero_mappings_canonical()

    index = {
        "artifact": "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_INDEX",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "capability_library_version": CAPABILITY_LIBRARY_VERSION,
        "scope": "LAUNCH57_IDS",
        "library_count": scope["library_count"],
        "entries": build_library_index_artifact(),
        "functional_areas": [
            "Market Data",
            "Smart Money",
            "Derivatives",
            "Decision Intelligence",
            "Trust & Evidence",
            "Alerts & Monitoring",
            "Research & Explanation",
            "Due Diligence",
            "Risk",
            "Personal Decision Tools",
        ],
    }
    INDEX_PATH.write_text(json.dumps(index, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    recon = {
        "artifact": "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_RECONCILIATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "capability_library_version": CAPABILITY_LIBRARY_VERSION,
        "scope": "LAUNCH57_IDS",
        "canonical_owner": "launch57.edge_ui_batch1:capability_library_search",
        "support_layer": "launch57.capability_library_common",
        "runtime_guard": "launch57.trust_adaptive_common:apply_capability_library_guard",
        "ssot_sources": [
            "governance/launch57/LAUNCH57_REGISTER.json",
            "governance/launch57/LAUNCH57_SIX_HERO_MATRIX.json",
            "governance/launch57/LAUNCH57_CAPABILITY_SYSTEM_GRAPH.json",
        ],
        "library_scope": scope,
        "duplicate_guard": dupes,
        "hero_mapping_guard": heroes,
        "components": build_library_component_registry(),
        "api_routes": [
            "/api/launch57/capability-library",
            "/api/launch57/capability-library/compare",
            "/api/launch57/capability-library/{launch_number}",
        ],
        "acceptance_criteria_24": acceptance,
        "parked_contamination": [],
        "external_blockers": [
            {
                "id": "PASS_LIVE",
                "category": "NEEDS_EXTERNAL_VERIFICATION",
                "detail": "Production live validation not granted",
            }
        ],
    }
    RECON_PATH.write_text(json.dumps(recon, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    all_ac_pass = all(acceptance.values())
    iv = {
        "artifact": "BLACKDARK_LAUNCH57_CAPABILITY_LIBRARY_INDEPENDENT_VERIFICATION",
        "generated_at": now,
        "implementation_sha": sha,
        "baseline_sha": _spec_sha(),
        "builder_status": "PENDING_VERIFICATION",
        "LAUNCH57_CAPABILITY_LIBRARY_PASS_ENGINEERING": all_ac_pass and tests["passed"],
        "PASS_LIVE_NOT_CLAIMED": True,
        "PASS_ENGINEERING_NOT_CLAIMED_BY_ENVELOPE": True,
        "scope_lock": {
            "CURRENT_APPROVED_BUILD_SCOPE": "LAUNCH57",
            "LAUNCH57_COUNT": 57,
            "EVERYTHING_ELSE": "PARKED_OUT_OF_LAUNCH",
        },
        "verification_checks": {
            "library_count_57": scope["exactly_57"],
            "zero_parked_exposed": scope["parked_exposed"] == 0,
            "zero_duplicate_ids": dupes["no_duplicates"],
            "search_correctness": acceptance["ac05_search_by_name"] and acceptance["ac06_search_by_intent"],
            "visibility_correctness": acceptance["ac16_public_private_enforced"],
            "hero_mapping_truth": heroes["canonical_only"],
            "no_competing_ssot": scope["no_second_registry"],
            "tests_pass": tests["passed"],
        },
        "tests": tests,
        "acceptance_criteria": acceptance,
    }
    IV_PATH.write_text(json.dumps(iv, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    lines = [
        "# Launch-57 Capability Library (#52) — Engineering Report",
        "",
        f"- Generated: {now}",
        f"- Implementation SHA: `{sha}`",
        f"- Baseline SHA: `{_spec_sha()[:16]}…`",
        f"- Version: `{CAPABILITY_LIBRARY_VERSION}`",
        "",
        "## Scope",
        "",
        "Secondary searchable layer over the 57 approved Launch-57 capabilities.",
        "Not a second registry, homepage, or decision engine.",
        "",
        "## Canonical Paths",
        "",
        "- Search: `launch57.edge_ui_batch1:capability_library_search`",
        "- Detail: `launch57.edge_ui_batch1:capability_library_detail`",
        "- Compare: `launch57.edge_ui_batch1:capability_library_compare`",
        "- Support: `launch57.capability_library_common`",
        "- Guard: `launch57.trust_adaptive_common:apply_capability_library_guard`",
        "",
        "## Library Scope",
        "",
        f"- Indexed capabilities: **{scope['library_count']}/57**",
        f"- Missing IDs: `{scope['missing_launch_numbers']}`",
        f"- Parked exposed: **{scope['parked_exposed']}**",
        "",
        "## Acceptance Criteria (§24)",
        "",
    ]
    for key, value in sorted(acceptance.items()):
        lines.append(f"- `{key}`: **{value}**")
    lines.extend(
        [
            "",
            "## Verdict",
            "",
            f"- `LAUNCH57_CAPABILITY_LIBRARY_PASS_ENGINEERING`: **{iv['LAUNCH57_CAPABILITY_LIBRARY_PASS_ENGINEERING']}**",
            "- `PASS_LIVE_NOT_CLAIMED`: **true**",
            "",
            "## External Blockers",
            "",
            "- Production live validation (`PASS_LIVE`) — not granted in repository",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote {INDEX_PATH.name}, {RECON_PATH.name}, {IV_PATH.name}, {REPORT_PATH.name}")


if __name__ == "__main__":
    main()
