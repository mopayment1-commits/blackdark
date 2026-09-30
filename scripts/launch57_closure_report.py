#!/usr/bin/env python3
"""Aggregate Launch-57 CISA closure status + evidence index (honest report)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "governance" / "launch57" / "CISA_REMEDIATION_EVIDENCE_INDEX.json"
DEFAULT_OUT = ROOT / "governance" / "launch57" / "evidence" / "CLOSURE_REPORT.json"


def main() -> int:
    sys.path.insert(0, str(ROOT))
    from launch57_assurance_closure import launch57_closure_status

    index = json.loads(INDEX.read_text(encoding="utf-8")) if INDEX.is_file() else {}
    findings = index.get("findings") or {}
    open_inventory = {
        fid: meta
        for fid, meta in findings.items()
        if str(meta.get("status", "")).startswith("OPEN")
        or meta.get("status") in {"CLOSED_REPO", "CLOSED_PARTIAL"}
    }
    runtime = launch57_closure_status()
    report = {
        "program": index.get("program"),
        "phase": index.get("phase"),
        "remediation_sha": index.get("remediation_sha"),
        "baseline_sha": index.get("baseline_sha"),
        "cisa_certification_claimed": False,
        "inventory_open_or_partial": open_inventory,
        "runtime_assurance": runtime,
        "next_ops_scripts": [
            "scripts/verify_railway_launch57_env.py",
            "scripts/verify_launch57_prod_surface.py",
            "scripts/launch57_ops_closure_gate.py",
        ],
    }
    text = json.dumps(report, indent=2) + "\n"
    print(text)
    if "--write" in sys.argv:
        DEFAULT_OUT.parent.mkdir(parents=True, exist_ok=True)
        DEFAULT_OUT.write_text(text, encoding="utf-8")
        print(f"Wrote {DEFAULT_OUT}", file=sys.stderr)
    open_ops = [k for k, v in runtime.get("findings", {}).items() if v.get("status") == "OPEN"]
    if open_ops:
        print(f"RUNTIME_OPEN: {', '.join(open_ops)}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
