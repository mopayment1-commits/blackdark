#!/usr/bin/env python3
"""Verify LAUNCH57_ENGINEERING_HANDOFF.json paths exist; no false program completion."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HANDOFF = ROOT / "governance/launch57/LAUNCH57_ENGINEERING_HANDOFF.json"


def main() -> int:
    if not HANDOFF.is_file():
        return 1
    data = json.loads(HANDOFF.read_text(encoding="utf-8"))
    if data.get("cisa_certification_claimed") or data.get("program_complete"):
        print("handoff must not claim certification or program complete", file=sys.stderr)
        return 1
    errors: list[str] = []
    for key in (
        "safe_to_merge_engineering_gate",
        "pr_merge_checklist_gates",
        "post_merge_ops",
        "post_merge_ops_manifest",
        "post_merge_ops_manifest_gate",
        "iv_human_signoff_preflight",
        "open_ops_closure_package",
        "allowed_release_attestation",
        "merge_readiness_doc",
    ):
        rel = data.get(key)
        if not rel or not (ROOT / rel).is_file():
            errors.append(f"missing {key}: {rel}")
    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        return 1
    print("PASS: engineering handoff artifact consistent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
