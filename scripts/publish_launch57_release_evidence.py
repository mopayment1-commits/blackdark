#!/usr/bin/env python3
"""Publish Launch-57 release SBOM manifest for data-room (FINDING-10/11)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
MANIFEST = ROOT / "docs" / "data-room" / "sbom" / "LAUNCH57_RELEASE_MANIFEST.json"
PYTHON_SBOM = ROOT / "docs" / "data-room" / "sbom" / "cyclonedx-python.json"
SYFT_DEFAULT = ROOT / "governance" / "launch57" / "evidence" / "syft-prod-lock.cyclonedx.json"


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


def main() -> int:
    subprocess.check_call([sys.executable, str(ROOT / "scripts" / "generate_sbom.py")], cwd=ROOT)
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.is_file() else {}
    syft_path = Path(os.getenv("LAUNCH57_SYFT_SBOM_PATH", str(SYFT_DEFAULT)))
    manifest = {
        "release_line": "launch-57",
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_head(),
        "remediation_sha": index.get("remediation_sha"),
        "cisa_certification_claimed": False,
        "artifacts": {
            "python_cyclonedx": str(PYTHON_SBOM.relative_to(ROOT)),
            "python_cyclonedx_present": PYTHON_SBOM.is_file(),
            "syft_prod_lock_cyclonedx": str(syft_path.relative_to(ROOT)) if syft_path.is_file() else None,
        },
        "ci_artifact_names": [
            "launch57-engineering-baseline",
            "launch57-syft-prod-lock-sbom",
        ],
        "release_notes_template": "docs/templates/LAUNCH57_RELEASE_NOTES_SBOM.md",
        "honesty": "Manifest indexes SBOM files; does not imply full container SBOM without image digest.",
    }
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
