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
from governance.launch57.literal_closure_documents import (
    billing_iv_not_complete_public_document,
    billing_iv_public_document,
    billing_recon_public_document,
)

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
        billing_recon_public_document(
            generated_at=now,
            implementation_sha=implementation_sha,
            baseline_sha=baseline_sha,
        ),
    )
    if outcome == "pass":
        iv_doc = billing_iv_public_document(
            verified_at=now,
            implementation_sha=implementation_sha,
            baseline_sha=baseline_sha,
        )
    else:
        iv_doc = billing_iv_not_complete_public_document(
            verified_at=now,
            implementation_sha=implementation_sha,
            baseline_sha=baseline_sha,
        )
    write_artifact_json(IV_PATH, iv_doc)


if __name__ == "__main__":
    main()
