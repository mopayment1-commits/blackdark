#!/usr/bin/env python3
"""Identity source-driven final closure."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from bd_platform.identity_source_driven_engineering import identity_source_driven_status  # noqa: E402


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    subprocess.run([sys.executable, str(ROOT / "scripts/build_identity_implementation_index.py")], check=True)
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_identity_p0_test_matrix.py",
            "tests/test_auth_identity_profile.py",
            "tests/test_spine_database_auth.py",
            "-q",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    status = identity_source_driven_status(head=head, pytest_ok=proc.returncode == 0)
    ledger = {
        "schema_version": "1.0",
        "spec_file": "docs/BLACKDARK_INSTITUTIONAL_IDENTITY_AUTH_PROFILE_SPEC_v1.md",
        "generated_at": datetime.now(UTC).isoformat(),
        "material_sha": head,
        "spec_sha256": sha256_file(ROOT / "docs/BLACKDARK_INSTITUTIONAL_IDENTITY_AUTH_PROFILE_SPEC_v1.md"),
        "ledger_sha256": "",
        "requirements": status["requirements"],
    }
    ledger_path = ROOT / "docs" / "IDENTITY_IMPLEMENTATION_LEDGER.json"
    ledger_path.write_text(json.dumps(ledger, indent=2) + "\n", encoding="utf-8")
    ledger["ledger_sha256"] = sha256_file(ledger_path)
    closure_path = ROOT / "docs" / "IDENTITY_72_CLOSURE.json"
    artifact = {**status, **ledger, "pytest_output": proc.stdout[-5000:], "pytest_stderr": proc.stderr[-2000:]}
    closure_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: artifact[k] for k in sorted(artifact) if k.startswith(("PASS_", "SOURCE_", "LOCAL_", "KNOWN_", "EMAIL_", "GOOGLE_", "ARGON2", "P0_"))}, indent=2))
    return 0 if artifact["PASS_ENGINEERING_IDENTITY"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
