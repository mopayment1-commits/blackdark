#!/usr/bin/env python3
"""Generate Launch-57 engineering closure declaration (ops/executive may remain open)."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
STATUS = ROOT / "governance" / "launch57" / "LAUNCH57_COMPLETION_STATUS.json"
OUT_JSON = ROOT / "governance" / "launch57" / "LAUNCH57_ENGINEERING_CLOSURE.json"
OUT_MD = ROOT / "docs/governance/LAUNCH57_ENGINEERING_CLOSURE_DECLARATION.md"

OPS_OPEN_DEFAULT = ("FINDING-01", "FINDING-18", "FINDING-19")


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
    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.is_file() else {}
    status = json.loads(STATUS.read_text(encoding="utf-8")) if STATUS.is_file() else {}
    rollup = status.get("rollup") or {}
    ops_open = list(rollup.get("open_finding_ids") or OPS_OPEN_DEFAULT)
    repo_only = list(rollup.get("repo_only_finding_ids") or [])
    partial = list(rollup.get("partial_finding_ids") or [])
    payload = {
        "kind": "launch57_engineering_closure_declaration",
        "declared_at": datetime.now(UTC).isoformat(),
        "git_commit": _git_head(),
        "remediation_sha": index.get("remediation_sha"),
        "baseline_sha": index.get("baseline_sha"),
        "cisa_certification_claimed": False,
        "engineering_closure_declared": bool(rollup.get("engineering_track_complete", True)),
        "program_complete": False,
        "ops_and_executive_open": ops_open,
        "repo_verify_pending": repo_only,
        "partial_engineering": partial,
        "honesty": (
            "Engineering closure means repository artifacts, tests, and CI gates for Launch-57 "
            "CISA remediation are in place. It does not close executive pledge, production "
            "verification, pentest attestation, or WAF activation."
        ),
        "documents": {
            "completion_status": "governance/launch57/LAUNCH57_REMEDIATION_COMPLETION_STATUS.md",
            "ops_playbook": "docs/ops/LAUNCH57_FINAL_CLOSURE_PLAYBOOK.md",
            "inventory_lock": "governance/launch57/FINDING_INVENTORY_LOCK.json",
        },
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    md = f"""# Launch-57 — Engineering closure declaration

**Declared at:** {payload["declared_at"]}  
**Remediation SHA:** `{payload.get("remediation_sha")}`  
**Git commit:** `{payload.get("git_commit")}`

## Statement

BLACKDARK declares **engineering closure** for the Launch-57 CISA Secure by Demand remediation track in this repository: policies, controls, tests, evidence index, CI workflows, and operator runbooks are implemented per `CISA_REMEDIATION_EVIDENCE_INDEX.json`.

This is **not** whole-program closure and **not** CISA certification.

## Still open (expected)

| Category | Finding IDs |
|----------|-------------|
| Executive | {", ".join([f for f in ops_open if f == "FINDING-01"]) or "—"} |
| Operations | {", ".join([f for f in ops_open if f != "FINDING-01"]) or "—"} |
| Repo-only prod verify | {", ".join(repo_only) or "—"} |
| Partial SBOM | {", ".join(partial) or "—"} |

## Verification

```bash
python scripts/verify_launch57_finding_inventory_lock.py
python scripts/verify_launch57_repo_evidence.py
python scripts/generate_launch57_completion_status.py
```

Regenerate this declaration:

```bash
python scripts/generate_launch57_engineering_closure.py
```
"""
    OUT_MD.write_text(md, encoding="utf-8")
    print(f"Wrote {OUT_JSON}")
    print(f"Wrote {OUT_MD}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
