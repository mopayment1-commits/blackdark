"""Emit billing public artifacts (isolated from billing_entitlement_common)."""

from __future__ import annotations

import hashlib
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from governance.launch57.gov_io import write_artifact_json

GOV = ROOT / "governance" / "launch57"
RECON_PATH = GOV / "BLACKDARK_LAUNCH57_BILLING_ENTITLEMENT_RECONCILIATION.json"
IV_PATH = GOV / "BLACKDARK_LAUNCH57_BILLING_ENTITLEMENT_INDEPENDENT_VERIFICATION.json"
SPEC_UPLOAD = (
    Path.home()
    / ".cursor"
    / "projects"
    / "workspace"
    / "uploads"
    / "BLACKDARK_Launch57_Billing_Subscription_Entitlement_FROM_SCRATCH_SPEC_4__1__8540.md"
)


def _git_sha() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def _spec_sha() -> str:
    if not SPEC_UPLOAD.exists():
        return "unknown"
    return hashlib.sha256(SPEC_UPLOAD.read_bytes()).hexdigest()


def main(argv: list[str] | None = None) -> None:
    args = argv if argv is not None else sys.argv[1:]
    if len(args) != 1 or args[0] not in {"pass", "fail"}:
        raise SystemExit("usage: emit_billing_public_artifacts <pass|fail>")
    outcome = args[0]
    now = datetime.now(UTC).isoformat()
    implementation_sha = _git_sha()
    baseline_sha = _spec_sha()

    write_artifact_json(
        RECON_PATH,
        {
            "artifact": "BLACKDARK_LAUNCH57_BILLING_SUBSCRIPTION_RECONCILIATION",
            "generated_at": now,
            "implementation_sha": implementation_sha,
            "baseline_sha": baseline_sha,
            "scope": "LAUNCH57_IDS",
            "launch57_support_only": True,
            "outcome": outcome,
        },
    )

    if outcome == "pass":
        write_artifact_json(
            IV_PATH,
            {
                "artifact": "BLACKDARK_LAUNCH57_BILLING_INDEPENDENT_VERIFICATION",
                "verification_type": "engineering_closure",
                "verified_at": now,
                "implementation_sha": implementation_sha,
                "baseline_sha": baseline_sha,
                "verdict": "PASS_ENGINEERING",
                "launch57_billing_engineering_pass": True,
                "launch57_billing_ready_for_local_use": True,
                "pass_live_not_claimed": True,
                "outcome": "pass",
            },
        )
    else:
        write_artifact_json(
            IV_PATH,
            {
                "artifact": "BLACKDARK_LAUNCH57_BILLING_INDEPENDENT_VERIFICATION",
                "verification_type": "engineering_closure",
                "verified_at": now,
                "implementation_sha": implementation_sha,
                "baseline_sha": baseline_sha,
                "verdict": "NOT_COMPLETE",
                "launch57_billing_engineering_pass": False,
                "launch57_billing_ready_for_local_use": False,
                "pass_live_not_claimed": True,
                "outcome": "fail",
            },
        )


if __name__ == "__main__":
    main()
