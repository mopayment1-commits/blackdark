#!/usr/bin/env python3
"""Generate LAUNCH57_REMEDIATION_GATE_INDEX.json from evidence index (institutional navigation)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance/launch57/CISA_REMEDIATION_EVIDENCE_INDEX.json"
IV_BUNDLE = ROOT / "governance/launch57/LAUNCH57_INDEPENDENT_VERIFICATION_REPO_BUNDLE.json"
OUT = ROOT / "governance/launch57/LAUNCH57_REMEDIATION_GATE_INDEX.json"


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
    if not INDEX.is_file():
        print(f"missing {INDEX}", file=sys.stderr)
        return 1
    idx = json.loads(INDEX.read_text(encoding="utf-8"))
    gates: list[dict] = []
    for key, rel in sorted(idx.items()):
        if key == "findings" or not isinstance(rel, str):
            continue
        if key.endswith("_gate") or key in {"ops_playbook_dry_run", "ops_closure_gate"}:
            gates.append({"id": key, "path": rel, "kind": "script" if rel.endswith(".py") else "artifact"})
    if IV_BUNDLE.is_file():
        bundle = json.loads(IV_BUNDLE.read_text(encoding="utf-8"))
        for entry in bundle.get("repo_scripts") or []:
            gates.append(
                {
                    "id": entry.get("id"),
                    "path": entry.get("script"),
                    "kind": "iv_repo_bundle",
                    "expect_exit": entry.get("expect_exit"),
                    "maps_to": entry.get("maps_to"),
                }
            )
    payload = {
        "schema": "launch57_remediation_gate_index_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_head(),
        "authority": idx.get("program_authority"),
        "phase": idx.get("phase"),
        "remediation_sha": idx.get("remediation_sha"),
        "cisa_certification_claimed": False,
        "program_complete": False,
        "gate_count": len(gates),
        "gates": gates,
        "source": str(INDEX.relative_to(ROOT)),
    }
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {OUT} ({len(gates)} gates)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
